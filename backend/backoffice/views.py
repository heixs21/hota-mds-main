from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from accounts.authentication import AdminTokenAuthentication
from hota_mds.responses import success_response, error_response

from .audit import log_operation
from .display_services import ensure_mock_snapshots, get_screen_payload
from .energy_dashboard_services import serve_energy_dashboard
from .models import (
    Area,
    CodeMapping,
    DataSourceConfig,
    DataSourceHealthSnapshot,
    Device,
    Employee,
    DisplayContentConfig,
    EnergyEquipmentCatalog,
    Material,
    OpcUaHistorySample,
    OperationLog,
    Order,
    PageModuleSwitch,
    ProductionLine,
    RuntimeParameterConfig,
    ScreenConfig,
    ScreenPageBinding,
)
from .opcua_history_services import ensure_opcua_history_samples
from .connection_test_services import test_database_connection, test_opcua_connection
from .serializers import (
    AreaSerializer,
    CodeMappingSerializer,
    DataSourceConfigSerializer,
    DataSourceHealthSnapshotSerializer,
    DeviceSerializer,
    EmployeeSerializer,
    DisplayContentConfigSerializer,
    MaterialSerializer,
    OpcUaHistorySampleSerializer,
    OperationLogSerializer,
    OrderSerializer,
    PageModuleSwitchSerializer,
    ProductionLineSerializer,
    RuntimeParameterConfigSerializer,
    ScreenConfigSerializer,
    ScreenPageBindingSerializer,
)


class AdminApiViewSet(viewsets.ModelViewSet):
    authentication_classes = [AdminTokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    target_type = ""
    search_fields = []
    ordering_fields = ["id", "created_at", "updated_at"]
    default_ordering = None
    boolean_filter_fields = []
    exact_filter_fields = []

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in (
            "list",
            "batch_delete",
            "bulk_refresh_interval",
            "bulk_rotation_interval",
            "bulk_runtime_fields",
            "bulk_set_enabled",
        ):
            return self._apply_query_filters(queryset)
        return queryset

    def _apply_query_filters(self, queryset):
        params = self.request.query_params

        keyword = (params.get("keyword") or "").strip()
        if keyword and self.search_fields:
            keyword_q = Q()
            for field_name in self.search_fields:
                keyword_q |= Q(**{f"{field_name}__icontains": keyword})
            queryset = queryset.filter(keyword_q)

        for field_name in self.boolean_filter_fields:
            bool_value = self._parse_bool(params.get(field_name))
            if bool_value is not None:
                queryset = queryset.filter(**{field_name: bool_value})

        for field_name in self.exact_filter_fields:
            raw_value = params.get(field_name)
            if raw_value is not None and str(raw_value).strip() != "":
                queryset = queryset.filter(**{field_name: raw_value})

        queryset = self._apply_time_range_filters(queryset, "created_at")
        queryset = self._apply_time_range_filters(queryset, "updated_at")
        queryset = self._apply_ordering(queryset)
        return queryset

    def _parse_bool(self, raw_value):
        if raw_value is None:
            return None
        normalized = str(raw_value).strip().lower()
        if normalized in {"1", "true", "yes"}:
            return True
        if normalized in {"0", "false", "no"}:
            return False
        return None

    def _apply_time_range_filters(self, queryset, field_name):
        start_raw = self.request.query_params.get(f"{field_name}_start")
        end_raw = self.request.query_params.get(f"{field_name}_end")
        start_dt = self._parse_datetime_boundary(start_raw, is_end=False)
        end_dt = self._parse_datetime_boundary(end_raw, is_end=True)
        if start_dt:
            queryset = queryset.filter(**{f"{field_name}__gte": start_dt})
        if end_dt:
            queryset = queryset.filter(**{f"{field_name}__lte": end_dt})
        return queryset

    def _parse_datetime_boundary(self, raw_value, is_end):
        if not raw_value or not str(raw_value).strip():
            return None
        parsed_dt = parse_datetime(str(raw_value))
        if parsed_dt:
            return self._ensure_aware(parsed_dt)
        parsed_d = parse_date(str(raw_value))
        if parsed_d:
            boundary_time = timezone.datetime.max.time() if is_end else timezone.datetime.min.time()
            return self._ensure_aware(timezone.datetime.combine(parsed_d, boundary_time))
        return None

    def _ensure_aware(self, value):
        if timezone.is_naive(value):
            return timezone.make_aware(value, timezone.get_current_timezone())
        return value

    def _apply_ordering(self, queryset):
        raw_ordering = (self.request.query_params.get("ordering") or "").strip()
        if raw_ordering:
            sanitized = []
            for part in raw_ordering.split(","):
                part = part.strip()
                field_name = part.lstrip("-")
                if field_name in self.ordering_fields:
                    sanitized.append(part)
            if sanitized:
                return queryset.order_by(*sanitized)
        if self.default_ordering:
            return queryset.order_by(*self.default_ordering)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        total = queryset.count()
        page = self._parse_positive_int(request.query_params.get("page"), default=1)
        page_size = self._parse_page_size(request.query_params.get("pageSize"))
        start = (page - 1) * page_size
        end = start + page_size
        paged_queryset = queryset[start:end]
        serializer = self.get_serializer(paged_queryset, many=True)
        return success_response(
            "list loaded",
            {
                "items": serializer.data,
                "total": total,
                "page": page,
                "pageSize": page_size,
            },
        )

    def _parse_positive_int(self, raw_value, default):
        try:
            parsed = int(raw_value)
            return parsed if parsed > 0 else default
        except (TypeError, ValueError):
            return default

    def _parse_page_size(self, raw_value):
        parsed = self._parse_positive_int(raw_value, default=20)
        return min(parsed, 200)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response("detail loaded", serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        output = self.get_serializer(instance)
        log_operation(
            actor=request.user,
            action="CREATE",
            target_type=self.target_type,
            target_id=instance.pk,
            target_label=str(instance),
            request=request,
            change_summary=output.data,
        )
        return success_response("created", output.data, status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()
        output = self.get_serializer(updated_instance)
        log_operation(
            actor=request.user,
            action="UPDATE",
            target_type=self.target_type,
            target_id=updated_instance.pk,
            target_label=str(updated_instance),
            request=request,
            change_summary={"changedFields": list(request.data.keys()), "current": output.data},
        )
        return success_response("updated", output.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        target_label = str(instance)
        target_id = instance.pk
        snapshot = self.get_serializer(instance).data
        self.perform_destroy(instance)
        log_operation(
            actor=request.user,
            action="DELETE",
            target_type=self.target_type,
            target_id=target_id,
            target_label=target_label,
            request=request,
            change_summary=snapshot,
        )
        return success_response("deleted", None)

    @action(detail=False, methods=["post"], url_path="batch-delete")
    def batch_delete(self, request):
        ids = request.data.get("ids")
        if not isinstance(ids, list) or len(ids) == 0:
            return error_response("INVALID_PARAMS", "ids must be a non-empty list", 400)
        if len(ids) > 200:
            return error_response("INVALID_PARAMS", "batch delete limited to 200 items", 400)

        queryset = self.get_queryset().filter(pk__in=ids)
        matched = list(queryset)
        if not matched:
            return error_response("NOT_FOUND", "no matching records found", 404)

        deleted_summaries = []
        for instance in matched:
            deleted_summaries.append({"id": instance.pk, "label": str(instance)})

        count = len(matched)
        queryset.delete()

        log_operation(
            actor=request.user,
            action="DELETE",
            target_type=self.target_type,
            target_id="batch",
            target_label=f"batch delete {count} items",
            request=request,
            change_summary={"deletedCount": count, "items": deleted_summaries},
        )
        return success_response("batch deleted", {"deletedCount": count})


class AreaViewSet(AdminApiViewSet):
    queryset = Area.objects.select_related("parent").all()
    serializer_class = AreaSerializer
    target_type = "area"
    search_fields = ["code", "name", "notes"]
    boolean_filter_fields = ["is_active"]
    exact_filter_fields = ["parent_id"]
    ordering_fields = ["id", "code", "name", "is_active", "created_at", "updated_at"]
    default_ordering = ["code"]


class ProductionLineViewSet(AdminApiViewSet):
    queryset = ProductionLine.objects.select_related("area").all()
    serializer_class = ProductionLineSerializer
    target_type = "production_line"
    search_fields = ["code", "name", "notes", "area__name"]
    boolean_filter_fields = ["is_active"]
    exact_filter_fields = ["area_id"]
    ordering_fields = ["id", "code", "name", "is_active", "area__name", "created_at", "updated_at"]
    default_ordering = ["code"]


class DeviceViewSet(AdminApiViewSet):
    queryset = Device.objects.select_related("area", "production_line").all()
    serializer_class = DeviceSerializer
    target_type = "device"
    search_fields = ["code", "name", "ip", "notes", "area__name", "production_line__name"]
    boolean_filter_fields = ["is_active"]
    exact_filter_fields = ["area_id", "production_line_id", "default_status"]
    ordering_fields = ["id", "code", "name", "ip", "default_status", "is_active", "created_at", "updated_at"]
    default_ordering = ["code"]


class EmployeeViewSet(AdminApiViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    target_type = "employee"
    search_fields = ["employee_no", "name", "notes"]
    boolean_filter_fields = ["is_active"]
    exact_filter_fields = ["role"]
    ordering_fields = ["id", "employee_no", "name", "role", "is_active", "created_at", "updated_at"]
    default_ordering = ["employee_no"]


class CodeMappingViewSet(AdminApiViewSet):
    queryset = CodeMapping.objects.all()
    serializer_class = CodeMappingSerializer
    target_type = "code_mapping"
    search_fields = ["source_system", "internal_code", "external_code", "notes"]
    boolean_filter_fields = ["is_active"]
    exact_filter_fields = ["entity_type"]
    ordering_fields = ["id", "entity_type", "source_system", "internal_code", "external_code", "created_at", "updated_at"]
    default_ordering = ["entity_type", "source_system"]


class ScreenConfigViewSet(AdminApiViewSet):
    queryset = ScreenConfig.objects.select_related("area").all()
    serializer_class = ScreenConfigSerializer
    target_type = "screen_config"
    search_fields = ["screen_key", "title", "subtitle", "area__code", "area__name"]
    boolean_filter_fields = ["is_active"]
    exact_filter_fields = ["screen_key", "area_id"]
    ordering_fields = ["id", "screen_key", "title", "is_active", "area__code", "created_at", "updated_at"]
    default_ordering = ["area__code", "screen_key"]

    @action(detail=False, methods=["post"], url_path="bulk-rotation-interval")
    def bulk_rotation_interval(self, request):
        """按勾选 id 批量设置左右屏配置的轮播时长（秒）；查询参数与列表一致以校验可见性。"""
        payload = request.data or {}
        ids = payload.get("ids")
        if not isinstance(ids, list) or len(ids) == 0:
            return error_response("INVALID_PARAMS", "ids must be a non-empty list", 400)
        if len(ids) > 200:
            return error_response("INVALID_PARAMS", "batch rotation interval limited to 200 items", 400)

        raw_seconds = payload.get("rotationIntervalSeconds")
        try:
            seconds = int(raw_seconds)
        except (TypeError, ValueError):
            return error_response("INVALID_PARAMS", "rotationIntervalSeconds must be an integer", 400)
        if seconds < 5 or seconds > 86400:
            return error_response("INVALID_PARAMS", "rotationIntervalSeconds must be between 5 and 86400", 400)

        try:
            unique_ids = {int(pk) for pk in ids}
        except (TypeError, ValueError):
            return error_response("INVALID_PARAMS", "ids must be integers", 400)

        queryset = self.get_queryset().filter(pk__in=unique_ids)
        if queryset.count() != len(unique_ids):
            return error_response(
                "INVALID_PARAMS",
                "some ids are missing or not visible under current filters",
                400,
            )

        updated = queryset.update(rotation_interval_seconds=seconds)

        log_operation(
            actor=request.user,
            action="UPDATE",
            target_type=self.target_type,
            target_id="bulk",
            target_label=f"bulk rotation interval -> {seconds}s ({updated} rows)",
            request=request,
            change_summary={"rotationIntervalSeconds": seconds, "updatedCount": updated, "ids": list(unique_ids)},
        )
        return success_response(
            "bulk rotation interval updated",
            {"updatedCount": updated, "rotationIntervalSeconds": seconds},
        )


class DisplayContentConfigViewSet(AdminApiViewSet):
    queryset = DisplayContentConfig.objects.all()
    serializer_class = DisplayContentConfigSerializer
    target_type = "display_content_config"
    search_fields = ["config_key", "company_name", "welcome_message"]
    boolean_filter_fields = ["is_active"]
    exact_filter_fields = ["config_key"]
    ordering_fields = ["id", "config_key", "company_name", "is_active", "created_at", "updated_at"]
    default_ordering = ["config_key"]


class RuntimeParameterConfigViewSet(AdminApiViewSet):
    queryset = RuntimeParameterConfig.objects.all()
    serializer_class = RuntimeParameterConfigSerializer
    target_type = "runtime_parameter_config"
    search_fields = ["config_key", "notes"]
    boolean_filter_fields = ["is_active", "auto_scroll_enabled"]
    exact_filter_fields = ["config_key"]
    ordering_fields = ["id", "config_key", "is_active", "created_at", "updated_at"]
    default_ordering = ["config_key"]

    @action(detail=False, methods=["post"], url_path="bulk-runtime-fields")
    def bulk_runtime_fields(self, request):
        """按勾选 id 批量设置日有效工时与甘特窗口天数；查询参数与列表一致。"""
        payload = request.data or {}
        ids = payload.get("ids")
        if not isinstance(ids, list) or len(ids) == 0:
            return error_response("INVALID_PARAMS", "ids must be a non-empty list", 400)
        if len(ids) > 200:
            return error_response("INVALID_PARAMS", "batch limited to 200 items", 400)

        raw_hours = payload.get("singleDayEffectiveWorkHours")
        raw_days = payload.get("ganttWindowDays")
        if raw_hours is None or raw_days is None:
            return error_response(
                "INVALID_PARAMS",
                "singleDayEffectiveWorkHours and ganttWindowDays are required",
                400,
            )

        try:
            hours_dec = Decimal(str(raw_hours))
        except (InvalidOperation, TypeError, ValueError):
            return error_response("INVALID_PARAMS", "singleDayEffectiveWorkHours must be a decimal number", 400)
        if hours_dec <= 0 or hours_dec > 24:
            return error_response(
                "INVALID_PARAMS",
                "singleDayEffectiveWorkHours must be greater than 0 and at most 24",
                400,
            )

        try:
            days_int = int(raw_days)
        except (TypeError, ValueError):
            return error_response("INVALID_PARAMS", "ganttWindowDays must be an integer", 400)
        if days_int <= 0:
            return error_response("INVALID_PARAMS", "ganttWindowDays must be greater than 0", 400)

        try:
            unique_ids = {int(pk) for pk in ids}
        except (TypeError, ValueError):
            return error_response("INVALID_PARAMS", "ids must be integers", 400)

        queryset = self.get_queryset().filter(pk__in=unique_ids)
        if queryset.count() != len(unique_ids):
            return error_response(
                "INVALID_PARAMS",
                "some ids are missing or not visible under current filters",
                400,
            )

        updated = queryset.update(
            single_day_effective_work_hours=hours_dec,
            gantt_window_days=days_int,
        )

        log_operation(
            actor=request.user,
            action="UPDATE",
            target_type=self.target_type,
            target_id="bulk",
            target_label=f"bulk runtime fields hours={hours_dec} days={days_int} ({updated} rows)",
            request=request,
            change_summary={
                "singleDayEffectiveWorkHours": str(hours_dec),
                "ganttWindowDays": days_int,
                "updatedCount": updated,
                "ids": list(unique_ids),
            },
        )
        return success_response(
            "bulk runtime fields updated",
            {"updatedCount": updated},
        )


class DataSourceConfigViewSet(AdminApiViewSet):
    queryset = DataSourceConfig.objects.prefetch_related("devices").all()
    serializer_class = DataSourceConfigSerializer
    target_type = "data_source_config"
    search_fields = ["code", "name", "notes"]
    boolean_filter_fields = ["is_enabled"]
    exact_filter_fields = ["source_type", "secret_storage_type"]
    ordering_fields = ["id", "code", "name", "source_type", "is_enabled", "created_at", "updated_at"]
    default_ordering = ["code"]

    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        instance = self.get_object()
        if instance.source_type != "opcua":
            return success_response(
                "history loaded",
                {"items": [], "total": 0, "page": 1, "pageSize": 0},
            )

        ensure_opcua_history_samples(instance)
        queryset = OpcUaHistorySample.objects.filter(data_source=instance)
        total = queryset.count()
        page = self._parse_positive_int(request.query_params.get("page"), default=1)
        page_size = self._parse_page_size(request.query_params.get("pageSize"))
        start = (page - 1) * page_size
        end = start + page_size
        serializer = OpcUaHistorySampleSerializer(queryset[start:end], many=True)
        return success_response(
            "history loaded",
            {
                "items": serializer.data,
                "total": total,
                "page": page,
                "pageSize": page_size,
            },
        )

    @action(detail=False, methods=["post"], url_path="test-connection")
    def test_connection(self, request):
        payload = request.data or {}
        source_type = (payload.get("sourceType") or "").strip()
        connection_config = payload.get("connectionConfig") or {}
        node = payload.get("node")

        if not source_type:
            return error_response("INVALID_PARAMS", "sourceType is required", 400)

        if source_type == "opcua":
            result = test_opcua_connection(connection_config, node=node)
            if not result.ok:
                return error_response("CONNECTION_FAILED", result.message, 400)
            return success_response(
                "connection test ok",
                {
                    "sourceType": source_type,
                    "checkedAt": timezone.now().isoformat(),
                    "message": result.message,
                },
            )

        if source_type in {"database", "energy_db", "schedule_db", "wms"}:
            result = test_database_connection(connection_config)
            if not result.ok:
                return error_response("CONNECTION_FAILED", result.message, 400)
            return success_response(
                "connection test ok",
                {
                    "sourceType": source_type,
                    "checkedAt": timezone.now().isoformat(),
                    "message": result.message,
                },
            )

        return success_response(
            "connection test ok",
            {
                "sourceType": source_type,
                "checkedAt": timezone.now().isoformat(),
                "message": "连接参数校验通过（模拟测试）",
            },
        )

    @action(detail=False, methods=["post"], url_path="bulk-refresh-interval")
    def bulk_refresh_interval(self, request):
        """按勾选 id 批量设置数据源的轮询间隔（秒）；列表 source_type 等筛选与记录可见性一致。"""
        payload = request.data or {}
        ids = payload.get("ids")
        if not isinstance(ids, list) or len(ids) == 0:
            return error_response("INVALID_PARAMS", "ids must be a non-empty list", 400)
        if len(ids) > 200:
            return error_response("INVALID_PARAMS", "batch refresh interval limited to 200 items", 400)

        raw_seconds = payload.get("refreshIntervalSeconds")
        try:
            seconds = int(raw_seconds)
        except (TypeError, ValueError):
            return error_response("INVALID_PARAMS", "refreshIntervalSeconds must be an integer", 400)
        if seconds < 5 or seconds > 86400:
            return error_response("INVALID_PARAMS", "refreshIntervalSeconds must be between 5 and 86400", 400)

        try:
            unique_ids = {int(pk) for pk in ids}
        except (TypeError, ValueError):
            return error_response("INVALID_PARAMS", "ids must be integers", 400)

        queryset = self.get_queryset().filter(pk__in=unique_ids)
        if queryset.count() != len(unique_ids):
            return error_response(
                "INVALID_PARAMS",
                "some ids are missing or not visible under current filters",
                400,
            )

        updated = queryset.update(refresh_interval_seconds=seconds)

        log_operation(
            actor=request.user,
            action="UPDATE",
            target_type=self.target_type,
            target_id="bulk",
            target_label=f"bulk refresh interval -> {seconds}s ({updated} rows)",
            request=request,
            change_summary={"refreshIntervalSeconds": seconds, "updatedCount": updated, "ids": list(unique_ids)},
        )
        return success_response(
            "bulk refresh interval updated",
            {"updatedCount": updated, "refreshIntervalSeconds": seconds},
        )


class MaterialViewSet(AdminApiViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    target_type = "material"
    search_fields = ["code", "name", "specification", "notes"]
    boolean_filter_fields = ["is_active"]
    ordering_fields = ["id", "code", "name", "is_active", "created_at", "updated_at"]
    default_ordering = ["code"]


class OrderViewSet(AdminApiViewSet):
    queryset = Order.objects.select_related("material", "production_line").all()
    serializer_class = OrderSerializer
    target_type = "order"
    search_fields = ["order_no", "notes", "material__name", "production_line__name"]
    boolean_filter_fields = ["is_active"]
    exact_filter_fields = ["status", "material_id", "production_line_id"]
    ordering_fields = [
        "id", "order_no", "status", "quantity", "completed_quantity",
        "planned_start", "planned_end", "is_active", "created_at", "updated_at",
    ]
    default_ordering = ["-created_at", "order_no"]


class PageModuleSwitchViewSet(AdminApiViewSet):
    queryset = PageModuleSwitch.objects.all()
    serializer_class = PageModuleSwitchSerializer
    target_type = "page_module_switch"
    search_fields = ["module_key", "label", "notes"]
    boolean_filter_fields = ["is_enabled"]
    exact_filter_fields = ["screen_key"]
    ordering_fields = ["id", "screen_key", "module_key", "sort_order", "is_enabled", "created_at", "updated_at"]
    default_ordering = ["screen_key", "sort_order"]


class ScreenPageBindingViewSet(AdminApiViewSet):
    queryset = ScreenPageBinding.objects.all()
    serializer_class = ScreenPageBindingSerializer
    target_type = "screen_page_binding"
    search_fields = ["page_key", "notes"]
    boolean_filter_fields = ["is_enabled"]
    exact_filter_fields = ["screen_key", "area_id"]
    ordering_fields = ["id", "area_id", "screen_key", "page_key", "is_enabled", "created_at", "updated_at"]
    default_ordering = ["area_id", "screen_key", "page_key"]

    def get_queryset(self):
        return super().get_queryset().select_related("area")

    @action(detail=False, methods=["post"], url_path="bulk-set-enabled")
    def bulk_set_enabled(self, request):
        """按勾选 id 批量设置是否启用；查询参数与列表一致。"""
        payload = request.data or {}
        ids = payload.get("ids")
        if not isinstance(ids, list) or len(ids) == 0:
            return error_response("INVALID_PARAMS", "ids must be a non-empty list", 400)
        if len(ids) > 200:
            return error_response("INVALID_PARAMS", "batch limited to 200 items", 400)

        raw_enabled = payload.get("isEnabled")
        if raw_enabled is None:
            return error_response("INVALID_PARAMS", "isEnabled is required", 400)
        if isinstance(raw_enabled, bool):
            enabled = raw_enabled
        elif raw_enabled in (1, "1", "true", "True"):
            enabled = True
        elif raw_enabled in (0, "0", "false", "False"):
            enabled = False
        else:
            return error_response("INVALID_PARAMS", "isEnabled must be a boolean", 400)

        try:
            unique_ids = {int(pk) for pk in ids}
        except (TypeError, ValueError):
            return error_response("INVALID_PARAMS", "ids must be integers", 400)

        queryset = self.get_queryset().filter(pk__in=unique_ids)
        if queryset.count() != len(unique_ids):
            return error_response(
                "INVALID_PARAMS",
                "some ids are missing or not visible under current filters",
                400,
            )

        updated = queryset.update(is_enabled=enabled)

        log_operation(
            actor=request.user,
            action="UPDATE",
            target_type=self.target_type,
            target_id="bulk",
            target_label=f"bulk set enabled -> {enabled} ({updated} rows)",
            request=request,
            change_summary={"isEnabled": enabled, "updatedCount": updated, "ids": list(unique_ids)},
        )
        return success_response(
            "bulk set enabled updated",
            {"updatedCount": updated, "isEnabled": enabled},
        )


class DataSourceHealthSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = [AdminTokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DataSourceHealthSnapshotSerializer
    queryset = DataSourceHealthSnapshot.objects.all()
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        ensure_mock_snapshots()
        return super().get_queryset()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response("list loaded", {"items": serializer.data, "total": queryset.count()})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response("detail loaded", serializer.data)


class OperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = [AdminTokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = OperationLogSerializer
    queryset = OperationLog.objects.select_related("actor").all()
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        queryset = super().get_queryset()
        action = self.request.query_params.get("action")
        target_type = self.request.query_params.get("targetType")
        if action:
            queryset = queryset.filter(action=action)
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        total = queryset.count()
        page = self._parse_positive_int(request.query_params.get("page"), default=1)
        page_size = self._parse_page_size(request.query_params.get("pageSize"))
        start = (page - 1) * page_size
        end = start + page_size
        paged_queryset = queryset[start:end]
        serializer = self.get_serializer(paged_queryset, many=True)
        return success_response(
            "list loaded",
            {
                "items": serializer.data,
                "total": total,
                "page": page,
                "pageSize": page_size,
            },
        )

    def _parse_positive_int(self, raw_value, default):
        try:
            parsed = int(raw_value)
            return parsed if parsed > 0 else default
        except (TypeError, ValueError):
            return default

    def _parse_page_size(self, raw_value):
        parsed = self._parse_positive_int(raw_value, default=20)
        return min(parsed, 200)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response("detail loaded", serializer.data)


class EnergyEquipmentOptionsView(APIView):
    """后台能耗表计选项：读本地 EnergyEquipmentCatalog（由定时任务 sync 写入）。"""

    authentication_classes = [AdminTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        raw = request.query_params.get("data_source_id")
        try:
            ds_id = int(raw)
        except (TypeError, ValueError):
            return error_response("INVALID_PARAMS", "缺少或非法的 data_source_id", 400)
        if ds_id <= 0:
            return error_response("INVALID_PARAMS", "缺少或非法的 data_source_id", 400)
        rows = (
            EnergyEquipmentCatalog.objects.filter(data_source_id=ds_id)
            .order_by("display_name", "equipment_id")[:6000]
        )
        opts = [{"id": r.equipment_id, "label": r.display_name or r.equipment_id} for r in rows]
        return success_response("energy equipment options loaded", {"options": opts})


class EnergyDashboardView(APIView):
    """能耗看板：默认读本地 EnergyDashboardSnapshot；forceRefresh 直连外部库写回快照。
    设置 ENERGY_DASHBOARD_ALLOW_LIVE_FALLBACK=false 可无缓存时禁止兜底查询。"""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        raw = request.data if isinstance(request.data, dict) else {}
        ids_raw = raw.get("dataSourceIds") or raw.get("data_source_ids") or []
        clean_ids: list[int] = []
        for x in ids_raw:
            try:
                clean_ids.append(int(x))
            except (TypeError, ValueError):
                continue
        clean_ids = [i for i in clean_ids if i > 0]
        allow_live = getattr(settings, "ENERGY_DASHBOARD_ALLOW_LIVE_FALLBACK", True)
        result = serve_energy_dashboard(clean_ids, raw, allow_live_fallback=allow_live)
        if not result.get("ok"):
            return error_response(
                "ENERGY_DASHBOARD_FAILED",
                result.get("error") or "能耗看板查询失败",
                400,
            )
        return success_response("energy dashboard loaded", result)


class ScreenDisplayView(APIView):
    permission_classes = [AllowAny]
    screen_key = ""

    def get(self, request, area_code, *args, **kwargs):
        try:
            payload = get_screen_payload(self.screen_key, area_code=area_code)
        except ValueError as exc:
            return error_response("INVALID_PARAMS", str(exc), 400)
        return success_response("screen payload loaded", payload)


class LeftScreenDisplayView(ScreenDisplayView):
    screen_key = "left"


class RightScreenDisplayView(ScreenDisplayView):
    screen_key = "right"
