# Generated manually for EnergyDashboardSnapshot model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backoffice", "0022_alter_screenpagebinding_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="EnergyDashboardSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("cache_key", models.CharField(db_index=True, max_length=64, unique=True)),
                ("data_source_ids", models.JSONField(blank=True, default=list)),
                ("refresh_scope", models.CharField(blank=True, default="", max_length=32)),
                ("filters", models.JSONField(blank=True, default=dict)),
                ("snapshot_data", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "ordering": ["-updated_at"],
            },
        ),
    ]
