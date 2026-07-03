from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backoffice", "0034_screenpagebinding_xiaozhou_line_layout"),
    ]

    operations = [
        migrations.AddField(
            model_name="screenpagebinding",
            name="realtime_demo_mode",
            field=models.BooleanField(
                db_comment="设备实时监控展示模式；启用后全部工位在线并展示演示数据",
                default=True,
                help_text="仅 page_key=realtime 时生效；启用后不连接现场设备，全部显示在线演示数据",
                verbose_name="展示模式",
            ),
        ),
    ]
