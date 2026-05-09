from django.db import migrations, models


def forwards_fill_from_fk(apps, schema_editor):
    ScreenPageBinding = apps.get_model("backoffice", "ScreenPageBinding")
    DataSourceConfig = apps.get_model("backoffice", "DataSourceConfig")
    for b in ScreenPageBinding.objects.all():
        ds_id = getattr(b, "data_source_id", None)
        if not ds_id:
            continue
        ds = DataSourceConfig.objects.filter(pk=ds_id).first()
        b.data_source_ids = [ds_id]
        if ds:
            b.binding_source_type = ds.source_type
        b.save(update_fields=["data_source_ids", "binding_source_type"])


class Migration(migrations.Migration):

    dependencies = [
        ("backoffice", "0015_screenpagebinding"),
    ]

    operations = [
        migrations.AddField(
            model_name="screenpagebinding",
            name="binding_source_type",
            field=models.CharField(
                blank=True,
                default="",
                help_text="与 DataSourceConfig.source_type 对齐；表单先选类型再筛选具体数据源",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="screenpagebinding",
            name="data_source_ids",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="screenpagebinding",
            name="device_ids",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(forwards_fill_from_fk, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="screenpagebinding",
            name="data_source",
        ),
    ]
