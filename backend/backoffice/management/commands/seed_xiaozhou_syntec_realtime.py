"""为销轴区域初始化新代 CNC 设备实时监控（111.md 方案 A）。"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from backoffice.models import Area, DataSourceConfig, Device, ScreenConfig, ScreenPageBinding
from backoffice.realtime_dashboard_services import REALTIME_LAYOUT_SYNTEC_CNC, XIAOZHOU_SYNTEC_SCHEME_A_NODES


class Command(BaseCommand):
    help = "为指定区域创建销轴新代 CNC 实时监控：OPC 数据源 + 左屏 realtime 子页面绑定。"

    def add_arguments(self, parser):
        parser.add_argument("--area-code", required=True, help="区域编码，例如 01")
        parser.add_argument(
            "--opc-endpoint",
            default="opc.tcp://127.0.0.1:4840",
            help="新代 CNC OPC UA endpoint",
        )
        parser.add_argument("--source-code", default="OPC_XZ_CNC", help="数据源编码")
        parser.add_argument("--device-code", default="XZ-CNC-01", help="绑定设备编码")
        parser.add_argument("--device-name", default="销轴 CNC", help="绑定设备名称")

    @transaction.atomic
    def handle(self, *args, **options):
        area_code = (options["area_code"] or "").strip()
        if not area_code:
            raise CommandError("--area-code 不能为空")

        area = Area.objects.filter(code__iexact=area_code, is_active=True).first()
        if area is None:
            raise CommandError(f"未找到启用区域 code={area_code}")

        source_code = (options["source_code"] or "").strip()
        endpoint = (options["opc_endpoint"] or "").strip()
        source, source_created = DataSourceConfig.objects.update_or_create(
            code=source_code,
            defaults={
                "name": "销轴新代 CNC",
                "source_type": "opcua",
                "is_enabled": True,
                "connection_config": {
                    "endpoint": endpoint,
                    "securityMode": "None",
                    "securityPolicy": "None",
                },
                "node": XIAOZHOU_SYNTEC_SCHEME_A_NODES,
                "notes": "111.md 方案 A；由 seed_xiaozhou_syntec_realtime 生成",
            },
        )

        device_code = (options["device_code"] or "").strip()
        device_name = (options["device_name"] or "").strip() or device_code
        device, device_created = Device.objects.update_or_create(
            code=device_code,
            defaults={
                "name": device_name,
                "area": area,
                "production_line": None,
                "default_status": Device.STATUS_STOPPED,
                "is_active": True,
                "notes": "销轴新代 CNC；seed_xiaozhou_syntec_realtime",
            },
        )
        source.devices.add(device)

        screen_config, sc_created = ScreenConfig.objects.get_or_create(
            area=area,
            screen_key="left",
            defaults={
                "title": f"{area.name}左屏",
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
            screen_key="left",
            page_key="realtime",
            defaults={
                "binding_source_type": "opcua",
                "data_source_ids": [source.pk],
                "realtime_layout": REALTIME_LAYOUT_SYNTEC_CNC,
                "is_enabled": True,
                "notes": "销轴新代 CNC 实时监控；111.md 方案 A",
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                "销轴实时监控配置完成："
                f" area={area.code}, source={source.code}({'新建' if source_created else '更新'}), "
                f" device={device.code}({'新建' if device_created else '更新'}), "
                f" binding={'新建' if binding_created else '更新'}(layout=syntec_cnc), "
                f" screenConfig={'新建' if sc_created else '已有'}"
            )
        )
        self.stdout.write(f"大屏 URL 示例: /screen/{area.code}/left")
