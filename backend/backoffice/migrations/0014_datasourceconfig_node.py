from django.db import migrations, models


def migrate_opcua_node_id_to_node_field(apps, schema_editor):
    DataSourceConfig = apps.get_model("backoffice", "DataSourceConfig")
    for item in DataSourceConfig.objects.filter(source_type="opcua").only("id", "connection_config", "node"):
        if item.node:
            continue
        connection_config = item.connection_config or {}
        node_id = connection_config.get("nodeId")
        if isinstance(node_id, str) and node_id.strip():
            DataSourceConfig.objects.filter(pk=item.pk).update(node=[node_id.strip()])


class Migration(migrations.Migration):

    dependencies = [
        ("backoffice", "0013_seed_area_screen_configs"),
    ]

    operations = [
        migrations.AddField(
            model_name="datasourceconfig",
            name="node",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.RunPython(migrate_opcua_node_id_to_node_field, migrations.RunPython.noop),
    ]
