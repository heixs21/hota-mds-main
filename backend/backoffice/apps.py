from django.apps import AppConfig


class BackofficeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backoffice"

    def ready(self) -> None:
        import sys
        import threading

        from django.db.models.signals import post_delete, post_save

        from .models import DataSourceConfig
        from .opcua_subscription_services import notify_opcua_subscription_config_changed

        def _on_data_source_changed(sender, instance, **kwargs):  # noqa: ARG001
            if getattr(instance, "source_type", None) == "opcua":
                notify_opcua_subscription_config_changed()

        post_save.connect(_on_data_source_changed, sender=DataSourceConfig)
        post_delete.connect(_on_data_source_changed, sender=DataSourceConfig)

        skip_commands = {"test", "migrate", "makemigrations", "collectstatic", "shell", "check"}
        if skip_commands.intersection(sys.argv):
            return

        def _deferred_start() -> None:
            try:
                from .opcua_subscription_services import start_opcua_subscription_manager

                start_opcua_subscription_manager()
            except Exception:
                import logging

                logging.getLogger(__name__).exception("OPC UA subscription manager deferred start failed")

        threading.Timer(1.0, _deferred_start).start()
