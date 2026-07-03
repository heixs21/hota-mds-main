"""为套筒滚子 1~9 号线各车床创建 OPC UA 数据源（DS-02001 起）。"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from backoffice.models import Area, DataSourceConfig, Device
from backoffice.taotong_gunzi_device_seed import TAOTONG_GUNZI_AREA
from backoffice.taotong_gunzi_opcua_seed import DEFAULT_OPCUA_PORT, iter_taotong_gunzi_opcua_sources


class Command(BaseCommand):
    help = "为套筒滚子各车床创建 OPC UA 数据源（endpoint=车床 IP，节点同销轴方案 A，编码 DS-02001 起）。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--opc-port",
            type=int,
            default=DEFAULT_OPCUA_PORT,
            help=f"OPC UA 端口，默认 {DEFAULT_OPCUA_PORT}",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="仅打印将写入的数据源，不落库",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        port = int(options["opc_port"])
        dry_run = bool(options["dry_run"])

        area = Area.objects.filter(code=TAOTONG_GUNZI_AREA["code"], is_active=True).first()
        if area is None and not dry_run:
            raise CommandError(
                f"未找到区域 {TAOTONG_GUNZI_AREA['code']}，请先执行 python manage.py seed_taotong_gunzi_devices"
            )

        created = 0
        updated = 0
        missing_devices: list[str] = []

        for item in iter_taotong_gunzi_opcua_sources(port=port):
            line = f"{item['source_code']} | {item['source_name']} | {item['endpoint_url']}"
            if dry_run:
                self.stdout.write(line)
                continue

            device = Device.objects.filter(code=item["device_code"], is_active=True).first()
            if device is None:
                missing_devices.append(item["device_code"])
                continue

            source, was_created = DataSourceConfig.objects.update_or_create(
                code=item["source_code"],
                defaults={
                    "name": item["source_name"],
                    "source_type": "opcua",
                    "is_enabled": True,
                    "connection_config": {"endpointUrl": item["endpoint_url"]},
                    "node": item["node"],
                    "notes": "套筒滚子新代 CNC；节点同销轴方案 A；seed_taotong_gunzi_opcua 生成",
                },
            )
            source.devices.set([device])
            if was_created:
                created += 1
            else:
                updated += 1

        if dry_run:
            total = len(iter_taotong_gunzi_opcua_sources(port=port))
            self.stdout.write(self.style.WARNING(f"dry-run：共 {total} 个 OPC UA 数据源（DS-02001 ~ DS-{2000 + total:05d}）"))
            return

        if missing_devices:
            raise CommandError(
                "以下设备尚未入库，请先执行 seed_taotong_gunzi_devices："
                + ", ".join(missing_devices[:5])
                + (" ..." if len(missing_devices) > 5 else "")
            )

        total = created + updated
        self.stdout.write(
            self.style.SUCCESS(
                f"套筒滚子 OPC UA 数据源完成：新建 {created} 个，更新 {updated} 个，共 {total} 个（DS-02001 起）。"
            )
        )
