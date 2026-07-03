from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backoffice", "0035_screenpagebinding_realtime_demo_mode"),
    ]

    operations = [
        migrations.AlterField(
            model_name="screenpagebinding",
            name="realtime_layout",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "自动识别"),
                    ("siemens_boring", "西门子镗孔"),
                    ("syntec_cnc", "新代 CNC"),
                    ("parameter_grid", "参数列表"),
                    ("xiaozhou_line", "销轴产线布局"),
                    ("taotong_gunzi_line", "套筒滚子产线布局"),
                ],
                db_comment="设备实时监控页仪表盘模板；空为自动识别",
                default="",
                help_text="仅 page_key=realtime 时生效；空则按 OPC 节点自动识别",
                max_length=32,
                verbose_name="实时监控模板",
            ),
        ),
    ]
