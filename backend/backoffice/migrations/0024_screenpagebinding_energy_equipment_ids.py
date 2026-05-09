# Manual migration for energy_equipment_ids on ScreenPageBinding

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backoffice", "0023_energy_dashboard_snapshot"),
    ]

    operations = [
        migrations.AddField(
            model_name="screenpagebinding",
            name="energy_equipment_ids",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="能耗页：platform_equipment.e_id 列表，对应大屏筛选范围",
            ),
        ),
    ]
