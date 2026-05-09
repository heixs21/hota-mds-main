import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backoffice", "0014_datasourceconfig_node"),
    ]

    operations = [
        migrations.CreateModel(
            name="ScreenPageBinding",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "reserved_1",
                    models.CharField(blank=True, default="", max_length=255, verbose_name="预留字段1"),
                ),
                (
                    "reserved_2",
                    models.CharField(blank=True, default="", max_length=255, verbose_name="预留字段2"),
                ),
                (
                    "reserved_3",
                    models.CharField(blank=True, default="", max_length=255, verbose_name="预留字段3"),
                ),
                (
                    "reserved_4",
                    models.CharField(blank=True, default="", max_length=255, verbose_name="预留字段4"),
                ),
                (
                    "reserved_5",
                    models.CharField(blank=True, default="", max_length=255, verbose_name="预留字段5"),
                ),
                (
                    "screen_key",
                    models.CharField(choices=[("left", "左屏"), ("right", "右屏")], max_length=16),
                ),
                ("page_key", models.CharField(max_length=64)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_enabled", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True)),
                (
                    "area",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="screen_page_bindings",
                        to="backoffice.area",
                    ),
                ),
                (
                    "data_source",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="screen_page_bindings",
                        to="backoffice.datasourceconfig",
                    ),
                ),
            ],
            options={
                "ordering": ["area", "screen_key", "sort_order", "page_key"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("area", "screen_key", "page_key"),
                        name="uniq_screen_page_binding_area_screen_page",
                    ),
                ],
            },
        ),
    ]
