# management/commands/cleanup_channel_layer.py

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import asyncio


class Command(BaseCommand):
    help = "Clean up channel layer data and perform maintenance tasks"

    def add_arguments(self, parser):
        parser.add_argument(
            "--expired-messages",
            action="store_true",
            help="Remove expired messages",
        )
        parser.add_argument(
            "--old-delivered",
            type=int,
            default=24,
            help="Remove delivered messages older than X hours (default: 24)",
        )
        parser.add_argument(
            "--stale-groups",
            type=int,
            default=24,
            help="Remove group memberships older than X hours (default: 24)",
        )
        parser.add_argument(
            "--optimize-db",
            action="store_true",
            help="Run database optimization (VACUUM for SQLite)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force cleanup without confirmation prompts",
        )
        parser.add_argument(
            "--test-channel-layer",
            action="store_true",
            help="Test the channel layer functionality",
        )

    def handle(self, *args, **options):
        if options["test_channel_layer"]:
            self.test_channel_layer()
            return

        # Import models
        try:
            from .models import ChannelMessage, ChannelGroup
        except ImportError:
            try:
                # Try different import paths
                from ..models import ChannelMessage, ChannelGroup
            except ImportError:
                raise CommandError(
                    "Could not import ChannelMessage and ChannelGroup models. "
                    "Make sure they are in the correct location."
                )

        self.stdout.write(self.style.SUCCESS("=== Channel Layer Cleanup ==="))

        # Show current statistics
        self.show_current_stats(ChannelMessage, ChannelGroup)

        cleanup_performed = False

        # Clean expired messages
        if options["expired_messages"] or not any(
            [
                options["expired_messages"],
                options["old_delivered"] != 24,
                options["stale_groups"] != 24,
            ]
        ):
            cleanup_performed = True
            self.cleanup_expired_messages(
                ChannelMessage, options["dry_run"], options["force"]
            )

        # Clean old delivered messages
        if options["old_delivered"] and options["old_delivered"] > 0:
            cleanup_performed = True
            self.cleanup_old_delivered_messages(
                ChannelMessage,
                options["old_delivered"],
                options["dry_run"],
                options["force"],
            )

        # Clean stale groups
        if options["stale_groups"] and options["stale_groups"] > 0:
            cleanup_performed = True
            self.cleanup_stale_groups(
                ChannelGroup,
                options["stale_groups"],
                options["dry_run"],
                options["force"],
            )

        # Optimize database
        if options["optimize_db"]:
            self.optimize_database(options["dry_run"])

        if cleanup_performed:
            # Show updated statistics
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write(self.style.SUCCESS("Updated Statistics:"))
            self.show_current_stats(ChannelMessage, ChannelGroup)

    def show_current_stats(self, ChannelMessage, ChannelGroup):
        """Display current channel layer statistics"""
        now = timezone.now()

        total_messages = ChannelMessage.objects.count()
        delivered_messages = ChannelMessage.objects.filter(delivered=True).count()
        pending_messages = ChannelMessage.objects.filter(delivered=False).count()
        expired_messages = ChannelMessage.objects.filter(expires_at__lt=now).count()

        total_groups = ChannelGroup.objects.values("group_name").distinct().count()
        total_memberships = ChannelGroup.objects.count()

        self.stdout.write(f"Total Messages: {total_messages}")
        self.stdout.write(f"  - Delivered: {delivered_messages}")
        self.stdout.write(f"  - Pending: {pending_messages}")
        self.stdout.write(f"  - Expired: {expired_messages}")
        self.stdout.write(f"Total Groups: {total_groups}")
        self.stdout.write(f"Total Group Memberships: {total_memberships}")

    def cleanup_expired_messages(self, ChannelMessage, dry_run, force):
        """Clean up expired messages"""
        self.stdout.write("\n--- Cleaning Expired Messages ---")

        now = timezone.now()
        expired_messages = ChannelMessage.objects.filter(expires_at__lt=now)
        count = expired_messages.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No expired messages to clean up."))
            return

        self.stdout.write(f"Found {count} expired messages.")

        if dry_run:
            self.stdout.write(
                self.style.WARNING("[DRY RUN] Would delete expired messages.")
            )
            return

        if not force:
            confirm = input(f"Delete {count} expired messages? (y/N): ")
            if confirm.lower() != "y":
                self.stdout.write("Skipped expired message cleanup.")
                return

        with transaction.atomic():
            deleted_count = expired_messages.delete()[0]
            self.stdout.write(
                self.style.SUCCESS(f"✓ Deleted {deleted_count} expired messages.")
            )

    def cleanup_old_delivered_messages(self, ChannelMessage, hours, dry_run, force):
        """Clean up old delivered messages"""
        self.stdout.write(f"\n--- Cleaning Delivered Messages Older Than {hours}h ---")

        cutoff = timezone.now() - timedelta(hours=hours)
        old_messages = ChannelMessage.objects.filter(
            delivered=True, created_at__lt=cutoff
        )
        count = old_messages.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"No delivered messages older than {hours}h to clean up."
                )
            )
            return

        self.stdout.write(f"Found {count} old delivered messages.")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Would delete {count} old delivered messages."
                )
            )
            return

        if not force:
            confirm = input(f"Delete {count} old delivered messages? (y/N): ")
            if confirm.lower() != "y":
                self.stdout.write("Skipped old delivered message cleanup.")
                return

        with transaction.atomic():
            deleted_count = old_messages.delete()[0]
            self.stdout.write(
                self.style.SUCCESS(f"✓ Deleted {deleted_count} old delivered messages.")
            )

    def cleanup_stale_groups(self, ChannelGroup, hours, dry_run, force):
        """Clean up stale group memberships"""
        self.stdout.write(f"\n--- Cleaning Group Memberships Older Than {hours}h ---")

        cutoff = timezone.now() - timedelta(hours=hours)
        stale_groups = ChannelGroup.objects.filter(added_at__lt=cutoff)
        count = stale_groups.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"No group memberships older than {hours}h to clean up."
                )
            )
            return

        self.stdout.write(f"Found {count} stale group memberships.")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Would delete {count} stale group memberships."
                )
            )
            return

        if not force:
            confirm = input(f"Delete {count} stale group memberships? (y/N): ")
            if confirm.lower() != "y":
                self.stdout.write("Skipped stale group cleanup.")
                return

        with transaction.atomic():
            deleted_count = stale_groups.delete()[0]
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Deleted {deleted_count} stale group memberships."
                )
            )

    def optimize_database(self, dry_run):
        """Optimize the database"""
        self.stdout.write("\n--- Database Optimization ---")

        if dry_run:
            self.stdout.write(
                self.style.WARNING("[DRY RUN] Would run database optimization.")
            )
            return

        try:
            from django.db import connection

            # Check if using SQLite
            if "sqlite" in connection.settings_dict["ENGINE"]:
                self.stdout.write("Running SQLite VACUUM...")
                with connection.cursor() as cursor:
                    cursor.execute("VACUUM;")
                self.stdout.write(self.style.SUCCESS("✓ SQLite database optimized."))
            else:
                self.stdout.write(
                    "Database optimization not implemented for this database engine."
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Database optimization failed: {e}"))

    def test_channel_layer(self):
        """Test the channel layer functionality"""
        self.stdout.write(self.style.SUCCESS("=== Testing Channel Layer ==="))

        try:
            # Test async functionality
            asyncio.run(self._async_test_channel_layer())
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Channel layer test failed: {e}"))
            raise

    async def _async_test_channel_layer(self):
        """Async channel layer test"""
        try:
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            if not channel_layer:
                raise Exception("No channel layer configured")

            self.stdout.write(f"Channel layer: {channel_layer.__class__.__name__}")

            # Test basic functionality
            channel = await channel_layer.new_channel()
            self.stdout.write(f"✓ Created test channel: {channel}")

            # Test send/receive
            test_message = {"type": "test.message", "data": "Hello World"}
            await channel_layer.send(channel, test_message)
            self.stdout.write("✓ Sent test message")

            # Note: In production, you might want to test receive as well
            # received = await channel_layer.receive(channel)
            # self.stdout.write(f'✓ Received message: {received}')

            # Test group functionality
            test_group = "test_group"
            await channel_layer.group_add(test_group, channel)
            self.stdout.write(f"✓ Added channel to group: {test_group}")

            await channel_layer.group_send(test_group, {"type": "test.group.message"})
            self.stdout.write("✓ Sent group message")

            await channel_layer.group_discard(test_group, channel)
            self.stdout.write("✓ Removed channel from group")

            # Get stats
            if hasattr(channel_layer, "get_stats"):
                stats = await channel_layer.get_stats()
                self.stdout.write(f"Channel layer stats: {stats}")

            self.stdout.write(self.style.SUCCESS("✓ All channel layer tests passed!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Channel layer test failed: {e}"))
            raise
