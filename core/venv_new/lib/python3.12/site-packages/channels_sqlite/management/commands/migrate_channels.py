from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connection
from django.conf import settings
import os


class Command(BaseCommand):
    help = "Set up the Django ORM Channel Layer with proper database migrations"

    def add_arguments(self, parser):
        parser.add_argument(
            "--create-migration",
            action="store_true",
            help="Create initial migration files for channel layer models",
        )
        parser.add_argument(
            "--migrate",
            action="store_true",
            help="Run database migrations for channel layer",
        )
        parser.add_argument(
            "--verify",
            action="store_true",
            help="Verify the channel layer setup and database tables",
        )
        parser.add_argument(
            "--cleanup",
            action="store_true",
            help="Clean up expired messages and old group memberships",
        )
        parser.add_argument(
            "--stats",
            action="store_true",
            help="Show channel layer statistics",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Run all setup steps (create migration, migrate, verify)",
        )

    def handle(self, *args, **options):
        if options["all"]:
            self.stdout.write(
                self.style.SUCCESS("=== Setting up Django ORM Channel Layer ===")
            )
            self.create_migration()
            self.run_migration()
            self.verify_setup()
            self.show_stats()
        else:
            if options["create_migration"]:
                self.create_migration()

            if options["migrate"]:
                self.run_migration()

            if options["verify"]:
                self.verify_setup()

            if options["cleanup"]:
                self.cleanup_data()

            if options["stats"]:
                self.show_stats()

    def create_migration(self):
        """Create migration files for channel layer models"""
        self.stdout.write("Creating migration files...")

        try:
            # Get the app name from settings or assume it's in the current app
            app_name = self.get_app_name()

            # Create initial migration
            call_command(
                "makemigrations", app_name, name="channel_layer_models", verbosity=2
            )

            self.stdout.write(
                self.style.SUCCESS(f"✓ Created migration files for {app_name}")
            )

        except Exception as e:
            raise CommandError(f"Failed to create migrations: {e}")

    def run_migration(self):
        """Run database migrations"""
        self.stdout.write("Running database migrations...")

        try:
            call_command("migrate", verbosity=2)
            self.stdout.write(self.style.SUCCESS("✓ Database migrations completed"))

        except Exception as e:
            raise CommandError(f"Failed to run migrations: {e}")

    def verify_setup(self):
        """Verify that the channel layer is properly set up"""
        self.stdout.write("Verifying channel layer setup...")

        try:
            # Check if tables exist
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('channel_messages', 'channel_groups')"
                )
                tables = [row[0] for row in cursor.fetchall()]

                if "channel_messages" in tables:
                    self.stdout.write(
                        self.style.SUCCESS("✓ channel_messages table exists")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR("✗ channel_messages table missing")
                    )

                if "channel_groups" in tables:
                    self.stdout.write(
                        self.style.SUCCESS("✓ channel_groups table exists")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR("✗ channel_groups table missing")
                    )

            # Check channel layer configuration
            channel_layers = getattr(settings, "CHANNEL_LAYERS", {})
            default_layer = channel_layers.get("default", {})
            backend = default_layer.get("BACKEND", "")

            if "DjangoORMChannelLayer" in backend:
                self.stdout.write(
                    self.style.SUCCESS("✓ DjangoORMChannelLayer configured in settings")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "⚠ DjangoORMChannelLayer not found in CHANNEL_LAYERS settings"
                    )
                )
                self.stdout.write("Add this to your settings.py:")
                self.stdout.write("""
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'your_app.channel_layers.DjangoORMChannelLayer',
        'CONFIG': {
            'polling_interval': 0.05,
            'message_retention': 86400,
            'capacity': 100,
            'expiry': 30,
        },
    },
}""")

            self.stdout.write(
                self.style.SUCCESS("✓ Channel layer verification completed")
            )

        except Exception as e:
            raise CommandError(f"Verification failed: {e}")

    def cleanup_data(self):
        """Clean up expired messages and old group memberships"""
        self.stdout.write("Cleaning up channel layer data...")

        try:
            from django.utils import timezone
            from datetime import timedelta

            # Import models dynamically
            app_name = self.get_app_name()
            ChannelMessage = self.get_model(app_name, "ChannelMessage")
            ChannelGroup = self.get_model(app_name, "ChannelGroup")

            # Clean expired messages
            expired_count = ChannelMessage.objects.filter(
                expires_at__lt=timezone.now()
            ).count()

            if expired_count > 0:
                ChannelMessage.objects.filter(expires_at__lt=timezone.now()).delete()
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Cleaned up {expired_count} expired messages")
                )

            # Clean old delivered messages (older than 1 day)
            cutoff = timezone.now() - timedelta(days=1)
            old_delivered_count = ChannelMessage.objects.filter(
                delivered=True, created_at__lt=cutoff
            ).count()

            if old_delivered_count > 0:
                ChannelMessage.objects.filter(
                    delivered=True, created_at__lt=cutoff
                ).delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Cleaned up {old_delivered_count} old delivered messages"
                    )
                )

            # Clean old group memberships (older than 1 day)
            old_groups_count = ChannelGroup.objects.filter(added_at__lt=cutoff).count()

            if old_groups_count > 0:
                ChannelGroup.objects.filter(added_at__lt=cutoff).delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Cleaned up {old_groups_count} old group memberships"
                    )
                )

            if (
                expired_count == 0
                and old_delivered_count == 0
                and old_groups_count == 0
            ):
                self.stdout.write(
                    self.style.SUCCESS("✓ No cleanup needed - all data is current")
                )

        except Exception as e:
            raise CommandError(f"Cleanup failed: {e}")

    def show_stats(self):
        """Show channel layer statistics"""
        self.stdout.write("Channel Layer Statistics:")
        self.stdout.write("=" * 50)

        try:
            app_name = self.get_app_name()
            ChannelMessage = self.get_model(app_name, "ChannelMessage")
            ChannelGroup = self.get_model(app_name, "ChannelGroup")

            from django.utils import timezone

            # Message statistics
            total_messages = ChannelMessage.objects.count()
            undelivered_messages = ChannelMessage.objects.filter(
                delivered=False
            ).count()
            delivered_messages = ChannelMessage.objects.filter(delivered=True).count()
            expired_messages = ChannelMessage.objects.filter(
                expires_at__lt=timezone.now()
            ).count()

            self.stdout.write(f"Total Messages: {total_messages}")
            self.stdout.write(f"Delivered Messages: {delivered_messages}")
            self.stdout.write(f"Pending Messages: {undelivered_messages}")
            self.stdout.write(f"Expired Messages: {expired_messages}")

            # Group statistics
            total_groups = ChannelGroup.objects.values("group_name").distinct().count()
            total_memberships = ChannelGroup.objects.count()

            self.stdout.write(f"Total Groups: {total_groups}")
            self.stdout.write(f"Total Group Memberships: {total_memberships}")

            # Recent activity
            from datetime import timedelta

            recent_cutoff = timezone.now() - timedelta(hours=1)
            recent_messages = ChannelMessage.objects.filter(
                created_at__gte=recent_cutoff
            ).count()

            self.stdout.write(f"Messages in last hour: {recent_messages}")

        except Exception as e:
            raise CommandError(f"Failed to get statistics: {e}")

    def get_app_name(self):
        """Get the app name where the models are located"""
        # Try to determine the app name from the command location
        command_path = os.path.abspath(__file__)

        # Look for the app name in the path
        path_parts = command_path.split(os.sep)
        try:
            # Find 'management' in path and get the app name before it
            management_index = path_parts.index("management")
            if management_index > 0:
                return path_parts[management_index - 1]
        except ValueError:
            pass

        # Fallback: ask user or use a default
        return input(
            "Enter the app name where ChannelMessage and ChannelGroup models are located: "
        ).strip()

    def get_model(self, app_name, model_name):
        """Dynamically import and return a model"""
        try:
            from django.apps import apps

            return apps.get_model(app_name, model_name)
        except Exception as e:
            raise CommandError(f"Could not import {app_name}.{model_name}: {e}")
