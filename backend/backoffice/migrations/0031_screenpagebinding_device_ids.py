# Re-add optional device filter for realtime page card titles

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backoffice", "0030_screenpagebinding_realtime_layout"),
    ]

    operations = [
        migrations.AddField(
            model_name="screenpagebinding",
            name="device_ids",
            field=models.JSONField(
                blank=True,
                db_comment="设备实时监控页可选设备ID列表JSON",
                default=list,
                help_text="仅 page_key=realtime 时可选；指定卡片标题/关联设备，空则按数据源绑定设备推断",
                verbose_name="监控设备 ID 列表（JSON）",
            ),
        ),
    ]
