from django.core.management.base import BaseCommand

from backoffice.models import Area, Device, ProductionLine


class Command(BaseCommand):
    help = "Generate 100 sample devices based on existing area/production line."

    def handle(self, *args, **options):
        area = Area.objects.order_by("id").first()
        if area is None:
            area = Area.objects.create(code="AREA001", name="示例区域", is_active=True)

        production_line = ProductionLine.objects.order_by("id").first()
        if production_line is None:
            production_line = ProductionLine.objects.create(
                code="LINE001",
                name="示例产线",
                area=area,
                is_active=True,
            )

        status_cycle = [
            Device.STATUS_RUNNING,
            Device.STATUS_STOPPED,
            Device.STATUS_ALARM,
            Device.STATUS_OFFLINE,
        ]

        created_count = 0
        for offset in range(1, 101):
            code = f"SAMPLE-{offset:03d}"
            defaults = {
                "name": f"示例设备{offset:03d}",
                "ip": f"10.10.1.{offset}",
                "area": area,
                "production_line": production_line,
                "default_status": status_cycle[(offset - 1) % len(status_cycle)],
                "is_active": True,
                "notes": "系统生成的分页示例数据",
            }
            _, created = Device.objects.update_or_create(code=code, defaults=defaults)
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed finished. Upserted 100 devices, newly created {created_count} records."
            )
        )
