from django.conf import settings


class ChannelsRouter:
    """
    Route channels models to separate database dynamically based on CHANNEL_LAYERS config
    """

    route_app_labels = {"channels_sqlite"}

    def __init__(self):
        print("Called")
        # Dynamically get the database name from CHANNEL_LAYERS settings
        self.channels_db = self._get_channels_database()

    def _get_channels_database(self):
        """
        Extract the database name from CHANNEL_LAYERS config
        """
        try:
            channel_layers = settings.CHANNEL_LAYERS
            default_layer = channel_layers.get("default", {})
            config = default_layer.get("CONFIG", {})
            db_name = config.get(
                "database", "channels"
            )  # Default to "channels" if not found
            return db_name
        except (AttributeError, KeyError):
            return "channels"  # Fallback default

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return self.channels_db
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return self.channels_db
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Ensure channels_sqlite only migrates to the configured channels database
        and other apps only migrate to 'default' database
        """
        if app_label in self.route_app_labels:
            # channels_sqlite ONLY goes to the dynamically determined database
            return db == self.channels_db
        else:
            # All other apps ONLY go to default database
            return db == "default"
