"""按车间 IP 布置图写入套筒滚子 1~9 号线机床设备台账。"""

from django.core.management.base import BaseCommand
from django.db import transaction

from backoffice.models import Area, Device, ProductionLine
from backoffice.taotong_gunzi_device_seed import (
    LEGACY_AREA_CODES,
    LEGACY_DEVICE_CODE_PREFIXES,
    LEGACY_LINE_CODE_PREFIXES,
    TAOTONG_GUNZI_AREA,
    TAOTONG_GUNZI_LINES,
    iter_taotong_gunzi_devices,
)


class Command(BaseCommand):
    help = "创建/更新套筒滚子 1~9 号线机床（单区域 TTGZ，192.168.31.x / 35.x）。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="仅打印将写入的设备，不落库",
        )

    def _cleanup_legacy(self, dry_run: bool) -> int:
        removed = 0
        if dry_run:
            for prefix in LEGACY_DEVICE_CODE_PREFIXES:
                removed += Device.objects.filter(code__startswith=prefix).count()
            return removed

        for prefix in LEGACY_DEVICE_CODE_PREFIXES:
            count, _ = Device.objects.filter(code__startswith=prefix).delete()
            removed += count

        for prefix in LEGACY_LINE_CODE_PREFIXES:
            ProductionLine.objects.filter(code__startswith=prefix).delete()

        for code in LEGACY_AREA_CODES:
            area = Area.objects.filter(code=code).first()
            if area and not area.devices.exists() and not area.production_lines.exists():
                area.delete()

        return removed

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = bool(options.get("dry_run"))
        line_cache: dict[str, ProductionLine] = {}

        if dry_run:
            area = Area(code=TAOTONG_GUNZI_AREA["code"], name=TAOTONG_GUNZI_AREA["name"], is_active=True)
        else:
            area, _ = Area.objects.update_or_create(
                code=TAOTONG_GUNZI_AREA["code"],
                defaults={"name": TAOTONG_GUNZI_AREA["name"], "is_active": True},
            )

        for line_def in TAOTONG_GUNZI_LINES:
            if dry_run:
                line_cache[line_def["line_code"]] = ProductionLine(
                    code=line_def["line_code"],
                    name=line_def["line_name"],
                    area=area,
                    is_active=True,
                )
            else:
                pl, _ = ProductionLine.objects.update_or_create(
                    code=line_def["line_code"],
                    defaults={
                        "name": line_def["line_name"],
                        "area": area,
                        "is_active": True,
                    },
                )
                line_cache[line_def["line_code"]] = pl

        created = 0
        updated = 0
        for item in iter_taotong_gunzi_devices():
            line = line_cache[item["line_code"]]
            msg = f"{item['device_code']} | {item['device_name']} | {item['ip']}"
            if dry_run:
                self.stdout.write(msg)
                continue
            _, was_created = Device.objects.update_or_create(
                code=item["device_code"],
                defaults={
                    "name": item["device_name"],
                    "ip": item["ip"],
                    "area": area,
                    "production_line": line,
                    "default_status": Device.STATUS_STOPPED,
                    "is_active": True,
                    "notes": "seed_taotong_gunzi_devices 按 IP 布置图生成",
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        legacy_removed = self._cleanup_legacy(dry_run)

        if dry_run:
            self.stdout.write(self.style.WARNING(f"dry-run：共 {len(iter_taotong_gunzi_devices())} 台设备"))
            if legacy_removed:
                self.stdout.write(self.style.WARNING(f"dry-run：将清理遗留设备 {legacy_removed} 台"))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"套筒滚子设备台账完成：新建 {created} 台，更新 {updated} 台，"
                f"共 {created + updated} 台（1 个区域、9 条产线）。"
            )
        )
        if legacy_removed:
            self.stdout.write(self.style.WARNING(f"已清理旧版分区域遗留设备 {legacy_removed} 台。"))
