from django.db import migrations


def seed_area_screen_configs(apps, schema_editor):
    Area = apps.get_model("backoffice", "Area")
    ScreenConfig = apps.get_model("backoffice", "ScreenConfig")

    global_configs = list(ScreenConfig.objects.filter(area__isnull=True))
    if not global_configs:
        return

    for area in Area.objects.filter(is_active=True):
        for global_config in global_configs:
            ScreenConfig.objects.get_or_create(
                area=area,
                screen_key=global_config.screen_key,
                defaults={
                    "title": global_config.title,
                    "subtitle": global_config.subtitle,
                    "rotation_interval_seconds": global_config.rotation_interval_seconds,
                    "page_keys": global_config.page_keys,
                    "module_settings": global_config.module_settings,
                    "theme_settings": global_config.theme_settings,
                    "is_active": global_config.is_active,
                    "reserved_1": global_config.reserved_1,
                    "reserved_2": global_config.reserved_2,
                    "reserved_3": global_config.reserved_3,
                    "reserved_4": global_config.reserved_4,
                    "reserved_5": global_config.reserved_5,
                },
            )


class Migration(migrations.Migration):

    dependencies = [
        ("backoffice", "0012_screenconfig_area_scope"),
    ]

    operations = [
        migrations.RunPython(seed_area_screen_configs, migrations.RunPython.noop),
    ]
