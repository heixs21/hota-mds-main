from django.db import migrations


# 与前端 ScreenDisplay.jsx PAGE_PRESETS / admin SCREEN_PAGE_KEY_OPTIONS 对齐
PRESET_PAGE_KEYS_BY_SCREEN = {
    "left": ["overview", "operations", "energy", "realtime"],
    "right": ["schedule", "risk", "simulation"],
}


def seed_full_preset_bindings(apps, schema_editor):
    """
    早期 ScreenConfig.page_keys 多为单页（如仅 overview），迁移 0017 只按旧列表播种，
    导致「设备实时监控」等子页面在后台无独立绑定行。此处为每个启用区域补全预设子页面行：
    仅创建尚不存在的 page_key；排序接在现有绑定之后，避免覆盖已有 sort_order。
    """
    Area = apps.get_model("backoffice", "Area")
    ScreenPageBinding = apps.get_model("backoffice", "ScreenPageBinding")
    for area in Area.objects.filter(is_active=True):
        for screen_key, canonical_keys in PRESET_PAGE_KEYS_BY_SCREEN.items():
            bindings = list(
                ScreenPageBinding.objects.filter(area_id=area.id, screen_key=screen_key).order_by(
                    "sort_order", "id"
                )
            )
            existing_keys = {b.page_key for b in bindings}
            max_order = max((b.sort_order for b in bindings), default=-1)
            next_order = max_order + 1
            for page_key in canonical_keys:
                if page_key in existing_keys:
                    continue
                ScreenPageBinding.objects.create(
                    area_id=area.id,
                    screen_key=screen_key,
                    page_key=page_key,
                    sort_order=next_order,
                    is_enabled=True,
                    binding_source_type="",
                    data_source_ids=[],
                    device_ids=[],
                    notes="",
                )
                existing_keys.add(page_key)
                next_order += 1


class Migration(migrations.Migration):

    dependencies = [
        ("backoffice", "0017_seed_screen_page_bindings"),
    ]

    operations = [
        migrations.RunPython(seed_full_preset_bindings, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="screenconfig",
            name="page_keys",
        ),
    ]
