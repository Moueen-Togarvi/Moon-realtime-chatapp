import asyncio
import string
import random
from datetime import timedelta
from typing import Dict, Any
from channels.layers import BaseChannelLayer
from django.utils import timezone
from django.db import transaction
from channels.db import database_sync_to_async
from .models import ChannelMessage, ChannelGroup
from django.conf import settings


class SqliteChannelLayer(BaseChannelLayer):
    """
    Django ORM-based SQLite channel layer using models and migrations.
    """

    def __init__(
        self,
        polling_interval: float = 0.1,
        message_retention: int = 86400,  # 1 day
        capacity: int = 100,
        expiry: int = 60,
        trim_batch_size: int = 100,
        auto_trim: bool = True,
        database="channels",
        **kwargs,
    ):
        super().__init__(capacity=capacity, expiry=expiry, **kwargs)
        self.polling_interval = polling_interval
        self.message_retention = message_retention
        self.trim_batch_size = trim_batch_size
        self.auto_trim = auto_trim
        self.database = database

        self.channels = {}  # Maps channel names to queues (like Redis layer)
        self._polling_task = None
        self._shutdown_event = asyncio.Event()
        self._initialized = False
        self._receive_lock = asyncio.Lock()

        if self.database == "default":
            raise ValueError(
                "It is not advisable to set your primary database as channel layer database"
            )

        assert "sqlite3" in settings.DATABASES[self.database]["ENGINE"], (
            "Sqlite3 Database Engine Is Needed to use this channel layer"
        )

    # Extensions that this layer supports
    extensions = ["groups", "flush"]

    async def new_channel(self, prefix="specific"):
        """
        Generate a new channel name with the given prefix.
        This is required by Django Channels.
        """
        # Generate a random suffix similar to Redis implementation
        suffix = "".join(random.choices(string.ascii_letters + string.digits, k=10))
        channel_name = f"{prefix}.{suffix}"
        # Ensure it follows Django Channels naming rules
        if len(channel_name) >= self.MAX_NAME_LENGTH:
            suffix = suffix[:10]  # Truncate if needed
            channel_name = f"{prefix}.{suffix}"
        return channel_name

    async def _ensure_initialized(self):
        """Ensure the channel layer is initialized"""
        if not self._initialized:
            await self._initialize()

    async def _initialize(self):
        """Initialize the polling task"""
        # Start polling task
        self._polling_task = asyncio.create_task(self._polling_loop())
        self._initialized = True

    async def _polling_loop(self):
        """Main polling loop for message delivery"""
        while not self._shutdown_event.is_set():
            try:
                await self._poll_and_deliver_messages()
                if self.auto_trim:
                    await self._trim_expired_messages()
            except Exception as e:
                raise e

            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(), timeout=self.polling_interval
                )
                break  # Shutdown requested
            except asyncio.TimeoutError:
                continue

    @database_sync_to_async
    def _get_undelivered_messages(self, limit: int = 1000):
        """Get undelivered messages from database"""
        return list(
            ChannelMessage.objects.using(self.database)
            .filter(expires_at__gte=timezone.now(), delivered=False)
            .order_by("created_at")[:limit]
            .values("id", "channel", "message", "created_at")
        )

    @database_sync_to_async
    def _mark_messages_delivered(self, message_ids: list):
        """Mark messages as delivered"""
        return (
            ChannelMessage.objects.using(self.database)
            .filter(id__in=message_ids)
            .update(delivered=True)
        )

    async def _poll_and_deliver_messages(self):
        """Poll for messages and deliver to active channels"""
        if not self.channels:
            return

        # Get undelivered messages
        messages = await self._get_undelivered_messages()

        if messages:
            delivered_ids = []
            # Deliver messages to active channels
            for msg in messages:
                channel = msg["channel"]
                if channel in self.channels:
                    queue = self.channels[channel]
                    try:
                        # Non-blocking put, following Redis pattern
                        if queue.qsize() < self.capacity:
                            queue.put_nowait(msg["message"])
                            delivered_ids.append(msg["id"])
                        else:
                            return
                    except Exception as _:
                        # Remove problematic queue
                        del self.channels[channel]

            # Mark delivered messages
            if delivered_ids:
                await self._mark_messages_delivered(delivered_ids)

    @database_sync_to_async
    def _cleanup_expired_messages(self):
        """Remove expired messages"""
        return (
            ChannelMessage.objects.using(self.database)
            .filter(expires_at__lt=timezone.now())
            .delete()
        )

    @database_sync_to_async
    def _cleanup_old_messages(self):
        """Remove old delivered messages"""
        cutoff = timezone.now() - timedelta(seconds=self.message_retention)
        return (
            ChannelMessage.objects.using(self.database)
            .filter(delivered=True, created_at__lt=cutoff)
            .delete()
        )

    async def _trim_expired_messages(self):
        """Remove expired and old messages"""
        try:
            # Remove expired messages
            await self._cleanup_expired_messages()
            await self._cleanup_old_messages()
        except Exception as e:
            print(f"Error trimming messages: {e}")

    # @database_sync_to_async
    def _create_message(self, channel: str, message: Dict[str, Any], expires_at):
        """Create a new message in the database"""
        return ChannelMessage.objects.using(self.database).acreate(
            channel=channel, message=message, expires_at=expires_at, delivered=False
        )

    async def send(self, channel: str, message: Dict[str, Any]):
        """Send a message to a channel"""
        await self._ensure_initialized()

        assert isinstance(message, dict), "message is not a dict"
        self.require_valid_channel_name(channel)
        assert "__asgi_channel__" not in message

        # Calculate expiration time
        expires_at = timezone.now() + timedelta(seconds=self.expiry)

        # Store message in database
        await self._create_message(channel, message, expires_at)

    async def receive(self, channel: str):
        """
        Receive a message from a channel.
        Blocks until a message is available (like Redis channel layer).
        """
        await self._ensure_initialized()
        self.require_valid_channel_name(channel, receive=True)

        # Create queue for channel if it doesn't exist (like Redis implementation)
        if channel not in self.channels:
            self.channels[channel] = asyncio.Queue(maxsize=self.capacity)

            # Check for existing messages for this channel immediately
            async with self._receive_lock:
                messages = await self._get_undelivered_messages()
                channel_messages = [
                    msg for msg in messages if msg["channel"] == channel
                ]

                if channel_messages:
                    delivered_ids = []
                    queue = self.channels[channel]

                    for msg in channel_messages:
                        if queue.qsize() < self.capacity:
                            queue.put_nowait(msg["message"])
                            delivered_ids.append(msg["id"])
                        else:
                            break

                    if delivered_ids:
                        await self._mark_messages_delivered(delivered_ids)

        queue = self.channels[channel]

        try:
            # Block until message arrives (no timeout)
            message = await queue.get()
            return message
        except asyncio.CancelledError:
            raise
        except Exception as e:
            raise
        finally:
            # Clean up empty queues
            if channel in self.channels and self.channels[channel].empty():
                self.channels.pop(channel, None)

    @database_sync_to_async
    def _add_to_group_db(self, group: str, channel: str):
        """Add a channel to a group in the database"""
        return ChannelGroup.objects.using(self.database).get_or_create(
            group_name=group,
            channel_name=channel,
            defaults={"added_at": timezone.now()},
        )

    async def group_add(self, group: str, channel: str):
        """Add a channel to a group"""
        await self._ensure_initialized()

        # Validate names (following Redis implementation)
        assert self.require_valid_group_name(group), "Group name not valid"
        assert self.require_valid_channel_name(channel), "Channel name not valid"

        await self._add_to_group_db(group, channel)

    @database_sync_to_async
    def _remove_from_group_db(self, group: str, channel: str):
        """Remove a channel from a group in the database"""
        return (
            ChannelGroup.objects.using(self.database)
            .filter(group_name=group, channel_name=channel)
            .delete()
        )

    async def group_discard(self, group: str, channel: str):
        """Remove a channel from a group"""
        await self._ensure_initialized()

        # Validate names (following Redis implementation)
        assert self.require_valid_group_name(group), "Group name not valid"
        assert self.require_valid_channel_name(channel), "Channel name not valid"

        await self._remove_from_group_db(group, channel)

    @database_sync_to_async
    def _get_group_channels(self, group: str):
        """Get all channels in a group"""
        # Clean expired group memberships first
        cutoff = timezone.now() - timedelta(seconds=86400)  # 1 day default
        ChannelGroup.objects.using(self.database).filter(added_at__lt=cutoff).delete()

        return list(
            ChannelGroup.objects.using(self.database)
            .filter(group_name=group)
            .values_list("channel_name", flat=True)
        )

    async def group_send(self, group: str, message: Dict[str, Any]):
        """Send a message to all channels in a group"""
        await self._ensure_initialized()

        # Validate (following Redis implementation)
        assert isinstance(message, dict), "Message is not a dict"
        assert self.require_valid_group_name(group), "Group name not valid"

        # Get channels in the group
        channels = await self._get_group_channels(group)

        # Send to each channel
        for channel in channels:
            try:
                await self.send(channel, message)
            except Exception as e:
                raise e

    @database_sync_to_async
    def _flush_all_data(self):
        """Flush all messages and groups from database"""
        with transaction.atomic():
            ChannelMessage.objects.using(self.database).all().delete()
            ChannelGroup.objects.using(self.database).all().delete()

    async def flush(self):
        """Flush all messages and groups"""
        await self._ensure_initialized()

        # Clear database
        await self._flush_all_data()

        # Clear in-memory state (like Redis implementation)
        self.channels.clear()

    async def cleanup(self):
        """Cleanup resources"""
        if self._polling_task and not self._polling_task.done():
            self._shutdown_event.set()
            try:
                await asyncio.wait_for(self._polling_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._polling_task.cancel()
                try:
                    await self._polling_task
                except asyncio.CancelledError:
                    pass

        # Clear all queues and cancel any pending operations
        for channel, queue in list(self.channels.items()):
            # Cancel any pending queue operations
            try:
                while not queue.empty():
                    queue.get_nowait()
            except asyncio.QueueEmpty:
                pass

        self.channels.clear()
        ic("Channel layer cleaned up")

    # Additional methods for monitoring and debugging
    @database_sync_to_async
    def _get_stats(self):
        """Get statistics about the channel layer"""
        total_messages = ChannelMessage.objects.using(self.database).count()
        undelivered_messages = (
            ChannelMessage.objects.using(self.database).filter(delivered=False).count()
        )
        expired_messages = (
            ChannelMessage.objects.using(self.database)
            .filter(expires_at__lt=timezone.now())
            .count()
        )
        total_groups = (
            ChannelGroup.objects.using(self.database)
            .values("group_name")
            .distinct()
            .count()
        )
        total_channels_in_groups = ChannelGroup.objects.using(self.database).count()
        return {
            "total_messages": total_messages,
            "undelivered_messages": undelivered_messages,
            "expired_messages": expired_messages,
            "total_groups": total_groups,
            "total_channels_in_groups": total_channels_in_groups,
            "active_channels": len(self.channels),
        }

    async def get_stats(self):
        """Get statistics about the channel layer (async)"""
        await self._ensure_initialized()
        return await self._get_stats()
