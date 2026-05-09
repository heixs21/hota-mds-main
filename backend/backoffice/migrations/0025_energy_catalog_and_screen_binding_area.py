# EnergyEquipmentCatalog + ScreenPageBinding.area；移除 (screen_key, page_key) 全局唯一约束

import django.db.models.deletion
from django.db import migrations, models


def assign_default_area(apps, schema_editor):
    Area = apps.get_model("backoffice", "Area")
    Binding = apps.get_model("backoffice", "ScreenPageBinding")
    first = Area.objects.order_by("code").first()
    if first:
        Binding.objects.filter(area__isnull=True).update(area_id=first.pk)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("backoffice", "0024_screenpagebinding_energy_equipment_ids"),
    ]

    operations = [
        migrations.CreateModel(
            name="EnergyEquipmentCatalog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("equipment_id", models.CharField(db_index=True, max_length=64)),
                ("display_name", models.CharField(blank=True, default="", max_length=255)),
                (
                    "data_source",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="energy_equipment_catalog",
                        to="backoffice.datasourceconfig",
                    ),
                ),
            ],
            options={
                "ordering": ["display_name", "equipment_id"],
            },
        ),
        migrations.AddConstraint(
            model_name="energyequipmentcatalog",
            constraint=models.UniqueConstraint(
                fields=("data_source", "equipment_id"),
                name="uniq_energy_equipment_catalog_ds_eid",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="screenpagebinding",
            name="uniq_screen_page_binding_screen_page",
        ),
        migrations.AddField(
            model_name="screenpagebinding",
            name="area",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="screen_page_bindings",
                to="backoffice.area",
            ),
        ),
        migrations.RunPython(assign_default_area, noop_reverse),
    ]
