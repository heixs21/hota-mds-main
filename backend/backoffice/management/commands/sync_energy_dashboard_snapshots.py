"""
按 DataSourceConfig.refresh_interval_seconds 将能耗看板写入本地 EnergyDashboardSnapshot。

建议由系统定时任务每分钟执行一次，例如：
  * * * * * cd /path/to/backend && python manage.py sync_energy_dashboard_snapshots
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from backoffice.models import DataSourceConfig, ScreenPageBinding
from backoffice.energy_dashboard_services import (
    default_energy_sync_body,
    load_energy_dashboard_snapshot_row,
    refresh_energy_equipment_catalog_for_data_sources,
    run_energy_dashboard,
    _normalized_source_ids,
    _parse_filters,
)


class Command(BaseCommand):
    help = "依据数据源刷新间隔，将能耗页（ScreenPageBinding page_key=energy）同步到本地快照表"

    def handle(self, *args, **options):
        bindings = ScreenPageBinding.objects.filter(page_key="energy", is_enabled=True)
        catalog_done = set()
        dashboard_seen = set()
        for b in bindings:
            ids = _normalized_source_ids(list(b.data_source_ids or []))
            if not ids:
                continue

            sources = list(DataSourceConfig.objects.filter(pk__in=ids, is_enabled=True))
            if not sources:
                self.stdout.write(self.style.WARNING(f"skip {list(ids)}: 无启用数据源"))
                continue

            ds_tuple = tuple(ids)
            if ds_tuple not in catalog_done:
                cerr = refresh_energy_equipment_catalog_for_data_sources(ids)
                if cerr:
                    self.stdout.write(self.style.WARNING(f"catalog {list(ids)}: {cerr}"))
                else:
                    self.stdout.write(f"catalog refreshed for datasource ids={list(ids)}")
                catalog_done.add(ds_tuple)

            primary = min(sources, key=lambda s: s.pk)
            interval_sec = max(60, int(primary.refresh_interval_seconds or 300))

            body = default_energy_sync_body()
            eq_ids = sorted(str(x).strip() for x in (b.energy_equipment_ids or []) if str(x).strip())
            if eq_ids:
                body["equipmentIds"] = eq_ids
            filters = _parse_filters(body)
            dash_key = (b.area_id or 0, ds_tuple, tuple(eq_ids))
            if dash_key in dashboard_seen:
                continue

            row = load_energy_dashboard_snapshot_row(ids, filters)
            if row:
                age = (timezone.now() - row.updated_at).total_seconds()
                if age < interval_sec:
                    self.stdout.write(
                        f"skip area={b.area_id} ids={list(ids)} 缓存仍新 age={age:.0f}s < interval={interval_sec}s"
                    )
                    dashboard_seen.add(dash_key)
                    continue

            self.stdout.write(f"sync area={b.area_id} ids={list(ids)} interval={interval_sec}s …")
            result = run_energy_dashboard(ids, body, persist_snapshot=True)
            if not result.get("ok"):
                self.stdout.write(self.style.ERROR(f"failed {list(ids)}: {result.get('error')}"))
            else:
                dashboard_seen.add(dash_key)
                self.stdout.write(self.style.SUCCESS(f"ok area={b.area_id} ids={list(ids)}"))
