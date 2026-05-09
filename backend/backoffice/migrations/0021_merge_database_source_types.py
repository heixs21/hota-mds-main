"""
Merge energy_db / schedule_db / wms into the generic database source type.

Any DataSourceConfig rows that carry one of the legacy sub-types are converted
to "database" so they appear in the unified database admin list and can be
selected in the screen-page-binding multi-select filtered by "database".
"""

from django.db import migrations, models

DATABASE_LEGACY_TYPES = {"energy_db", "schedule_db", "wms"}


def consolidate_db_source_types(apps, schema_editor):
    DataSourceConfig = apps.get_model("backoffice", "DataSourceConfig")
    DataSourceConfig.objects.filter(source_type__in=DATABASE_LEGACY_TYPES).update(
        source_type="database"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("backoffice", "0020_remove_screenpagebinding_device_ids"),
    ]

    operations = [
        migrations.RunPython(consolidate_db_source_types, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="datasourceconfig",
            name="source_type",
            field=models.CharField(
                max_length=32,
                choices=[
                    ("opcua", "OPCUA"),
                    ("modbus_tcp", "Modbus TCP"),
                    ("sap_rfc", "SAP RFC"),
                    ("database", "数据库"),
                    ("repair", "报修系统"),
                    ("custom", "自定义"),
                ],
            ),
        ),
    ]
