from django.db import migrations


def seed_from_screen_configs(apps, schema_editor):
    ScreenConfig = apps.get_model("backoffice", "ScreenConfig")
    ScreenPageBinding = apps.get_model("backoffice", "ScreenPageBinding")
    for sc in ScreenConfig.objects.select_related("area").exclude(area_id=None).filter(is_active=True):
        keys = sc.page_keys or []
        if not isinstance(keys, list):
            continue
        for index, page_key in enumerate(keys):
            if not isinstance(page_key, str) or not page_key.strip():
                continue
            ScreenPageBinding.objects.get_or_create(
                area_id=sc.area_id,
                screen_key=sc.screen_key,
                page_key=page_key.strip(),
                defaults={
                    "sort_order": index,
                    "is_enabled": True,
                    "binding_source_type": "",
                    "data_source_ids": [],
                    "device_ids": [],
                    "notes": "",
                },
            )


class Migration(migrations.Migration):

    dependencies = [
        ("backoffice", "0016_screenpagebinding_multiselect"),
    ]

    operations = [
        migrations.RunPython(seed_from_screen_configs, migrations.RunPython.noop),
    ]
