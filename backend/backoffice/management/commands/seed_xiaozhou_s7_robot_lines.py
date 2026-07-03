"""为销轴 1~5 号线初始化 S7 机器手数据源（222.md）。"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from backoffice.models import Area, DataSourceConfig, Device, ProductionLine, ScreenConfig, ScreenPageBinding
from backoffice.realtime_dashboard_services import REALTIME_LAYOUT_XIAOZHOU_LINE
from backoffice.s7_robot_seed import XIAOZHOU_S7_ROBOT_LINES, s7_robot_line_seed_payload


class Command(BaseCommand):
    help = "按 222.md 创建/更新销轴 1~5 号线 S7 机器手数据源，并绑定代表设备。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--area-code",
            default="",
            help="可选：新建代表设备时写入的区域编码；查找已有设备时也优先该区域",
        )
        parser.add_argument(
            "--create-devices",
            action="store_true",
            help="代表设备不存在时自动创建（需配合 --area-code）",
        )
        parser.add_argument(
            "--refresh-interval",
            type=int,
            default=30,
            help="轮询间隔（秒），默认 30",
        )
        parser.add_argument(
            "--lines",
            default="1,2,3,4,5",
            help="要处理的产线编号，逗号分隔，默认 1,2,3,4,5",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="仅打印将写入的配置，不落库",
        )
        parser.add_argument(
            "--bind-screen",
            action="store_true",
            help="将所选产线的 S7 数据源绑定到左屏 realtime 子页面（销轴产线布局）",
        )
        parser.add_argument(
            "--screen-key",
            default="left",
            choices=("left", "right"),
            help="绑定到哪一侧大屏，默认 left",
        )

    def _parse_lines(self, raw: str) -> set[int]:
        parts = [p.strip() for p in (raw or "").split(",") if p.strip()]
        if not parts:
            raise CommandError("--lines 不能为空")
        try:
            lines = {int(p) for p in parts}
        except ValueError as exc:
            raise CommandError("--lines 必须为逗号分隔的整数") from exc
        allowed = {item["line"] for item in XIAOZHOU_S7_ROBOT_LINES}
        unknown = lines - allowed
        if unknown:
            raise CommandError(f"不支持的产线编号: {sorted(unknown)}")
        return lines

    def _resolve_area(self, area_code: str) -> Area | None:
        code = (area_code or "").strip()
        if not code:
            return None
        area = Area.objects.filter(code__iexact=code, is_active=True).first()
        if area is None:
            raise CommandError(f"未找到启用区域 code={code}")
        return area

    def _resolve_production_line(self, area: Area | None, line: int) -> ProductionLine | None:
        if area is None:
            return None
        name_candidates = [
            f"销轴{line}号线",
            f"销轴 {line} 号线",
        ]
        for name in name_candidates:
            pl = ProductionLine.objects.filter(area=area, name=name, is_active=True).first()
            if pl:
                return pl
        code_candidates = [f"LINE-{line}", f"XZ-LINE-{line}", f"XZ{line}"]
        for code in code_candidates:
            pl = ProductionLine.objects.filter(area=area, code__iexact=code, is_active=True).first()
            if pl:
                return pl
        return None

    def _find_existing_robot_device(self, area: Area | None, line_def: dict) -> Device | None:
        device_code = line_def["device_code"]
        by_code = Device.objects.filter(code__iexact=device_code, is_active=True).first()
        if by_code:
            return by_code

        line = line_def["line"]
        name_keywords = [
            line_def["device_name"],
            f"销轴{line}号线机器手",
            f"销轴{line}号线机器人",
        ]
        qs = Device.objects.filter(is_active=True)
        if area is not None:
            qs = qs.filter(area=area)
        for keyword in name_keywords:
            hit = qs.filter(name=keyword).order_by("id").first()
            if hit:
                return hit
            hit = qs.filter(name__icontains=f"销轴{line}号线").filter(
                name__icontains="机器手"
            ).order_by("id").first()
            if hit:
                return hit
            hit = qs.filter(name__icontains=f"销轴{line}号线").filter(
                name__icontains="机器人"
            ).order_by("id").first()
            if hit:
                return hit
        return None

    def _ensure_device(
        self,
        *,
        area: Area | None,
        line_def: dict,
        create_devices: bool,
    ) -> tuple[Device | None, str]:
        existing = self._find_existing_robot_device(area, line_def)
        if existing:
            return existing, "已有"

        if not create_devices:
            return None, "未找到（跳过绑定）"

        if area is None:
            raise CommandError(
                f"产线 {line_def['line']} 无代表设备且未指定 --area-code，无法 --create-devices"
            )

        production_line = self._resolve_production_line(area, line_def["line"])
        device, created = Device.objects.update_or_create(
            code=line_def["device_code"],
            defaults={
                "name": line_def["device_name"],
                "area": area,
                "production_line": production_line,
                "default_status": Device.STATUS_STOPPED,
                "is_active": True,
                "notes": "222.md 机器手代表设备；seed_xiaozhou_s7_robot_lines 生成",
            },
        )
        return device, "新建" if created else "更新"

    def _collect_realtime_binding_source_ids(self, area: Area, screen_key: str) -> list[int]:
        """大屏 realtime：全部 S7 机器手 + 绑定里已有的 OPC UA 车床源。"""
        codes = [item["source_code"] for item in XIAOZHOU_S7_ROBOT_LINES]
        s7_ids = list(
            DataSourceConfig.objects.filter(code__in=codes, source_type="s7", is_enabled=True)
            .order_by("code")
            .values_list("pk", flat=True)
        )
        binding = ScreenPageBinding.objects.filter(
            area=area,
            screen_key=screen_key,
            page_key="realtime",
        ).first()
        opc_ids: list[int] = []
        if binding:
            for pk in binding.data_source_ids or []:
                if not isinstance(pk, int) or pk <= 0:
                    continue
                src = DataSourceConfig.objects.filter(pk=pk, is_enabled=True).first()
                if src and (src.source_type or "").strip() == "opcua":
                    opc_ids.append(pk)
        merged: list[int] = []
        seen: set[int] = set()
        for pk in [*s7_ids, *opc_ids]:
            if pk not in seen:
                seen.add(pk)
                merged.append(pk)
        return merged

    def _bind_realtime_screen(self, area: Area, screen_key: str) -> tuple[str, list[int]]:
        source_ids = self._collect_realtime_binding_source_ids(area, screen_key)
        if not source_ids:
            return "未绑定（无数据源）", []

        screen_config, _ = ScreenConfig.objects.get_or_create(
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

        binding, created = ScreenPageBinding.objects.update_or_create(
            area=area,
            screen_key=screen_key,
            page_key="realtime",
            defaults={
                "binding_source_type": "s7",
                "data_source_ids": source_ids,
                "realtime_layout": REALTIME_LAYOUT_XIAOZHOU_LINE,
                "realtime_demo_mode": True,
                "is_enabled": True,
                "notes": "222.md 销轴产线布局；seed_xiaozhou_s7_robot_lines 生成",
            },
        )
        return ("新建" if created else "更新"), source_ids

    @transaction.atomic
    def handle(self, *args, **options):
        selected_lines = self._parse_lines(options["lines"])
        area = self._resolve_area(options["area_code"])
        create_devices = bool(options["create_devices"])
        refresh_interval = max(5, int(options["refresh_interval"]))
        dry_run = bool(options["dry_run"])

        if create_devices and area is None:
            raise CommandError("--create-devices 需要同时指定 --area-code")
        if options["bind_screen"] and area is None:
            raise CommandError("--bind-screen 需要同时指定 --area-code")

        summaries: list[str] = []
        seeded_source_ids: list[int] = []
        for line_def in XIAOZHOU_S7_ROBOT_LINES:
            if line_def["line"] not in selected_lines:
                continue

            payload = s7_robot_line_seed_payload(line_def, refresh_interval_seconds=refresh_interval)
            if dry_run:
                summaries.append(
                    f"DRY {payload['code']} -> {payload['name']} @ {payload['connection_config']['host']} "
                    f"(nodes={len(payload['node'])})"
                )
                continue

            source, source_created = DataSourceConfig.objects.update_or_create(
                code=payload["code"],
                defaults={
                    "name": payload["name"],
                    "source_type": payload["source_type"],
                    "is_enabled": payload["is_enabled"],
                    "refresh_interval_seconds": payload["refresh_interval_seconds"],
                    "connection_config": payload["connection_config"],
                    "node": payload["node"],
                    "notes": payload["notes"],
                },
            )

            device, device_status = self._ensure_device(
                area=area,
                line_def=line_def,
                create_devices=create_devices,
            )
            if device is not None:
                source.devices.set([device])

            seeded_source_ids.append(source.pk)

            summaries.append(
                f"{payload['code']}({'新建' if source_created else '更新'}) "
                f"host={payload['connection_config']['host']} "
                f"device={device.code if device else '-'}({device_status}) "
                f"nodes={len(payload['node'])}"
            )

        if not dry_run and options["bind_screen"] and area is not None:
            bind_status, bound_ids = self._bind_realtime_screen(area, options["screen_key"])
            summaries.append(
                f"screen/{area.code}/{options['screen_key']} realtime 绑定 {len(bound_ids)} 个数据源({bind_status})"
            )

        if not summaries:
            raise CommandError("没有匹配到任何产线配置")

        prefix = "预览完成" if dry_run else "销轴 S7 机器手数据源配置完成"
        self.stdout.write(self.style.SUCCESS(f"{prefix}："))
        for line in summaries:
            self.stdout.write(f"  - {line}")
