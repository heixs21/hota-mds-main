"""绑定套筒滚子 OPC UA 数据源到设备实时监控子页面（套筒滚子产线布局）。"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from backoffice.models import Area, DataSourceConfig, ScreenConfig, ScreenPageBinding
from backoffice.realtime_dashboard_services import REALTIME_LAYOUT_TAOTONG_GUNZI_LINE
from backoffice.taotong_gunzi_device_seed import TAOTONG_GUNZI_AREA
from backoffice.taotong_gunzi_opcua_seed import OPCUA_SOURCE_CODE_START, iter_taotong_gunzi_opcua_sources


class Command(BaseCommand):
    help = "将套筒滚子 DS-02001 起 OPC UA 数据源绑定到 realtime 子页面（taotong_gunzi_line 布局）。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--area-code",
            default=TAOTONG_GUNZI_AREA["code"],
            help=f"区域编码，默认 {TAOTONG_GUNZI_AREA['code']}",
        )
        parser.add_argument(
            "--screen-key",
            default="left",
            choices=("left", "right"),
            help="绑定到哪一侧大屏，默认 left",
        )
        parser.add_argument(
            "--live-mode",
            action="store_true",
            help="关闭展示模式，使用现场 OPC 数据（默认开启展示模式）",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        area_code = (options["area_code"] or "").strip()
        area = Area.objects.filter(code__iexact=area_code, is_active=True).first()
        if area is None:
            raise CommandError(f"未找到启用区域 code={area_code}，请先 seed_taotong_gunzi_devices")

        source_codes = [item["source_code"] for item in iter_taotong_gunzi_opcua_sources()]
        sources = list(
            DataSourceConfig.objects.filter(code__in=source_codes, is_enabled=True).order_by("code")
        )
        if len(sources) < len(source_codes):
            missing = len(source_codes) - len(sources)
            raise CommandError(
                f"缺少 {missing} 个 OPC UA 数据源，请先执行 python manage.py seed_taotong_gunzi_opcua"
            )

        screen_key = options["screen_key"]
        demo_mode = not options["live_mode"]

        screen_config, sc_created = ScreenConfig.objects.get_or_create(
            area=area,
            screen_key=screen_key,
            defaults={
                "title": f"{area.name}{'左' if screen_key == 'left' else '右'}屏",
                "subtitle": "",
                "page_order": ["overview", "operations", "energy", "realtime"],
                "is_active": True,
            },
        )
        page_order = list(screen_config.page_order or [])
        if "realtime" not in page_order:
            page_order.append("realtime")
            screen_config.page_order = page_order
            screen_config.save(update_fields=["page_order"])

        binding, binding_created = ScreenPageBinding.objects.update_or_create(
            area=area,
            screen_key=screen_key,
            page_key="realtime",
            defaults={
                "binding_source_type": "opcua",
                "data_source_ids": [s.pk for s in sources],
                "realtime_layout": REALTIME_LAYOUT_TAOTONG_GUNZI_LINE,
                "realtime_demo_mode": demo_mode,
                "is_enabled": True,
                "notes": "套筒滚子 9 行×3 列产线布局；seed_taotong_gunzi_realtime_screen 生成",
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"套筒滚子实时监控绑定完成：area={area.code}, screen={screen_key}, "
                f"sources={len(sources)}(DS-{OPCUA_SOURCE_CODE_START:05d} 起), "
                f"layout=taotong_gunzi_line, demo_mode={demo_mode}, "
                f"binding={'新建' if binding_created else '更新'}"
            )
        )
        self.stdout.write(f"大屏 URL: /screen/{area.code}/{screen_key}")
