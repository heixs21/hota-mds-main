from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("backoffice", "0011_datasourcedevicebinding_datasourceconfig_devices"),
    ]

    operations = [
        migrations.AddField(
            model_name="screenconfig",
            name="area",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="screen_configs",
                to="backoffice.area",
            ),
        ),
        migrations.AlterField(
            model_name="screenconfig",
            name="screen_key",
            field=models.CharField(choices=[("left", "左屏"), ("right", "右屏")], max_length=16),
        ),
        migrations.AlterModelOptions(
            name="screenconfig",
            options={"ordering": ["area__code", "screen_key"]},
        ),
        migrations.AddConstraint(
            model_name="screenconfig",
            constraint=models.UniqueConstraint(fields=("area", "screen_key"), name="uniq_area_screen_config"),
        ),
    ]
