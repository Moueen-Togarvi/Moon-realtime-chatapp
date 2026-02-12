# models.py
from django.db import models
from django.utils import timezone
from datetime import timedelta


# Manager for efficient queries
class ChannelMessageManager(models.Manager):
    def unprocessed_for_channels(self, channels):
        """Get unprocessed messages for specific channels"""
        return self.filter(
            channel__in=channels, processed_by="", expires_at__gt=timezone.now()
        ).order_by("created_at")

    def mark_processed(self, message_ids, process_id):
        """Mark messages as processed"""
        return self.filter(id__in=message_ids).update(processed_by=process_id)

    def cleanup_expired(self, batch_size=100):
        """Remove expired messages"""
        expired_ids = list(
            self.filter(expires_at__lt=timezone.now()).values_list("id", flat=True)[
                :batch_size
            ]
        )
        if expired_ids:
            return self.filter(id__in=expired_ids).delete()
        return 0, {}

    def cleanup_old_processed(self, retention_seconds, batch_size=100):
        """Remove old processed messages"""
        cutoff_time = timezone.now() - timedelta(seconds=retention_seconds)
        old_ids = list(
            self.filter(created_at__lt=cutoff_time, processed_by__gt="").values_list(
                "id", flat=True
            )[:batch_size]
        )
        if old_ids:
            return self.filter(id__in=old_ids).delete()
        return 0, {}


class ChannelGroupManager(models.Manager):
    def get_channels_for_group(self, group_name):
        """Get all channels in a group"""
        return self.filter(group_name=group_name).values_list("channel_name", flat=True)

    def add_to_group(self, group_name, channel_name):
        """Add a channel to a group (get_or_create pattern)"""
        return self.get_or_create(group_name=group_name, channel_name=channel_name)

    def remove_from_group(self, group_name, channel_name):
        """Remove a channel from a group"""
        return self.filter(group_name=group_name, channel_name=channel_name).delete()


class ChannelMessage(models.Model):
    channel = models.CharField(max_length=100)
    message = models.JSONField()
    expires_at = models.DateTimeField()
    delivered = models.BooleanField(default=False)  # Changed from processed_by
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["delivered", "expires_at"]),
            models.Index(fields=["channel", "delivered"]),
        ]


class ChannelGroup(models.Model):
    group_name = models.CharField(max_length=100)
    channel_name = models.CharField(max_length=100)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["group_name", "channel_name"]
        indexes = [
            models.Index(fields=["group_name"]),
            models.Index(fields=["added_at"]),
        ]
