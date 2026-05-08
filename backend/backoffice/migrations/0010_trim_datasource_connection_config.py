from django.db import migrations


CONNECTION_CONFIG_ALLOWED_KEYS = {
    "opcua": {"endpointUrl", "nodeId", "username", "password"},
    "database": {"engine", "host", "port", "database", "username", "password"},
    "modbus_tcp": set(),
    "sap_rfc": set(),
    "repair": set(),
}


def _should_keep_connection_value(value):
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def _sanitize_connection_config(source_type, connection_config):
    if not isinstance(connection_config, dict):
        return {}
    allowed_keys = CONNECTION_CONFIG_ALLOWED_KEYS.get(source_type, set())
    cleaned = {}
    for key in allowed_keys:
        value = connection_config.get(key)
        if _should_keep_connection_value(value):
            cleaned[key] = value
    return cleaned


def trim_connection_config(apps, schema_editor):
    DataSourceConfig = apps.get_model("backoffice", "DataSourceConfig")
    for item in DataSourceConfig.objects.all().only("id", "source_type", "connection_config"):
        cleaned = _sanitize_connection_config(item.source_type, item.connection_config)
        if cleaned != (item.connection_config or {}):
            DataSourceConfig.objects.filter(pk=item.pk).update(connection_config=cleaned)


class Migration(migrations.Migration):

    dependencies = [
        ("backoffice", "0009_alter_datasourceconfig_source_type"),
    ]

    operations = [
        migrations.RunPython(trim_connection_config, migrations.RunPython.noop),
    ]
