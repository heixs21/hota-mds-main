from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("backoffice", "0010_trim_datasource_connection_config"),
    ]

    operations = [
        migrations.CreateModel(
            name="DataSourceDeviceBinding",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("data_source", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="device_bindings", to="backoffice.datasourceconfig")),
                ("device", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="data_source_bindings", to="backoffice.device")),
            ],
            options={
                "ordering": ["data_source_id", "device_id"],
                "constraints": [
                    models.UniqueConstraint(fields=("data_source", "device"), name="uniq_data_source_device_binding"),
                ],
            },
        ),
        migrations.AddField(
            model_name="datasourceconfig",
            name="devices",
            field=models.ManyToManyField(blank=True, related_name="data_sources", through="backoffice.DataSourceDeviceBinding", to="backoffice.device"),
        ),
    ]
