"""
重构 ScreenPageBinding 为全局（去除 area 维度，去除 sort_order）：
  1. ScreenConfig 新增 page_order 字段（该屏轮播顺序）
  2. ScreenPageBinding 去掉 area FK 和 sort_order，改唯一约束为 (screen_key, page_key)
  3. 播种 7 条预设全局绑定行（如已存在则跳过）
"""
import django.db.models.deletion
from django.db import migrations, models

PRESET_PAGES = [
    ("left",  "overview",   "综合总览"),
    ("left",  "operations", "运行与产量"),
    ("left",  "energy",     "能耗与占位"),
    ("left",  "realtime",   "设备实时监控"),
    ("right", "schedule",   "排产总览"),
    ("right", "risk",       "风险说明"),
    ("right", "simulation", "仿真预留"),
]


def seed_global_bindings(apps, schema_editor):
    """
    在旧表（仍有 area/sort_order）中收集已有数据源配置，合并为全局行；
    若同一 (screen_key, page_key) 有多条区域记录，取第一条的数据源设置。
    随后为预设页面补全缺失行。
    """
    ScreenPageBinding = apps.get_model("backoffice", "ScreenPageBinding")

    # 先按 (screen_key, page_key) 聚合，保留第一条的数据源信息
    seen = {}
    for b in ScreenPageBinding.objects.order_by("screen_key", "page_key", "id"):
        key = (b.screen_key, b.page_key)
        if key not in seen:
            seen[key] = {
                "binding_source_type": b.binding_source_type,
                "data_source_ids": b.data_source_ids,
                "is_enabled": b.is_enabled,
                "notes": b.notes,
            }

    # 确保 7 条预设页面都有记录
    for screen_key, page_key, _label in PRESET_PAGES:
        key = (screen_key, page_key)
        if key not in seen:
            seen[key] = {
                "binding_source_type": "",
                "data_source_ids": [],
                "is_enabled": True,
                "notes": "",
            }

    # 删除所有旧行，再用全局数据重建
    ScreenPageBinding.objects.all().delete()
    for (screen_key, page_key), defaults in seen.items():
        ScreenPageBinding.objects.create(
            screen_key=screen_key,
            page_key=page_key,
            **defaults,
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("backoffice", "0018_remove_screenconfig_page_keys_seed_presets"),
    ]

    operations = [
        # 1. ScreenConfig: 新增 page_order
        migrations.AddField(
            model_name="screenconfig",
            name="page_order",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='该屏轮播的子页面键顺序，如 ["overview", "realtime"]；空列表时使用全局默认顺序',
            ),
        ),
        # 2. ScreenPageBinding: 先加临时字段 area_nullable（让旧 area 可以为空，便于过渡）
        migrations.AlterField(
            model_name="screenpagebinding",
            name="area",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="screen_page_bindings",
                to="backoffice.area",
            ),
        ),
        # 3. 去掉旧唯一约束
        migrations.RemoveConstraint(
            model_name="screenpagebinding",
            name="uniq_screen_page_binding_area_screen_page",
        ),
        # 4. 去掉 sort_order
        migrations.RemoveField(
            model_name="screenpagebinding",
            name="sort_order",
        ),
        # 5. 数据迁移：聚合为全局行
        migrations.RunPython(seed_global_bindings, noop),
        # 6. 删除 area FK
        migrations.RemoveField(
            model_name="screenpagebinding",
            name="area",
        ),
        # 7. 新唯一约束 (screen_key, page_key)
        migrations.AddConstraint(
            model_name="screenpagebinding",
            constraint=models.UniqueConstraint(
                fields=["screen_key", "page_key"],
                name="uniq_screen_page_binding_screen_page",
            ),
        ),
    ]
