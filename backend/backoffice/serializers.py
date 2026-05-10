from rest_framework import serializers

from .models import (
    Area,
    CodeMapping,
    DataSourceConfig,
    DataSourceHealthSnapshot,
    Device,
    DeviceStatusSnapshot,
    Employee,
    EnergySnapshot,
    DisplayContentConfig,
    Material,
    OpcUaHistorySample,
    OperationLog,
    ProductionSnapshot,
    Order,
    PageModuleSwitch,
    ProductionLine,
    RuntimeParameterConfig,
    ScheduleSnapshot,
    ScreenConfig,
    ScreenPageBinding,
)


RESERVED_FIELDS = ["reserved_1", "reserved_2", "reserved_3", "reserved_4", "reserved_5"]

CONNECTION_CONFIG_ALLOWED_KEYS = {
    "opcua": {"endpointUrl", "username", "password"},
    "database": {"engine", "host", "port", "database", "username", "password"},
    "energy_db": {"engine", "host", "port", "database", "username", "password"},
    "schedule_db": {"engine", "host", "port", "database", "username", "password"},
    "wms": {"engine", "host", "port", "database", "username", "password"},
    "modbus_tcp": set(),
    "sap_rfc": set(),
    "repair": set(),
}


def _should_keep_connection_value(value):
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def sanitize_connection_config(source_type, connection_config):
    if not isinstance(connection_config, dict):
        return {}
    allowed_keys = CONNECTION_CONFIG_ALLOWED_KEYS.get(source_type, set())
    cleaned = {}
    for key in allowed_keys:
        value = connection_config.get(key)
        if _should_keep_connection_value(value):
            cleaned[key] = value
    return cleaned


class CamelCaseModelSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        if isinstance(data, dict):
            data = {self._to_snake_case(key): value for key, value in data.items()}
        return super().to_internal_value(data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {self._to_camel_case(key): value for key, value in data.items()}

    def _to_camel_case(self, value):
        parts = value.split("_")
        return parts[0] + "".join(part.capitalize() for part in parts[1:])

    def _to_snake_case(self, value):
        converted = []
        for char in value:
            if char.isupper():
                converted.append("_")
                converted.append(char.lower())
            else:
                converted.append(char)
        return "".join(converted)


class AreaSerializer(CamelCaseModelSerializer):
    parent_id = serializers.PrimaryKeyRelatedField(source="parent", queryset=Area.objects.all(), allow_null=True, required=False)
    parent_name = serializers.CharField(source="parent.name", read_only=True)

    class Meta:
        model = Area
        fields = ["id", "code", "name", "parent_id", "parent_name", "is_active", "notes", "created_at", "updated_at"] + RESERVED_FIELDS


class ProductionLineSerializer(CamelCaseModelSerializer):
    area_id = serializers.PrimaryKeyRelatedField(source="area", queryset=Area.objects.all(), allow_null=True, required=False)
    area_name = serializers.CharField(source="area.name", read_only=True)

    class Meta:
        model = ProductionLine
        fields = ["id", "code", "name", "area_id", "area_name", "is_active", "notes", "created_at", "updated_at"] + RESERVED_FIELDS


class DeviceSerializer(CamelCaseModelSerializer):
    area_id = serializers.PrimaryKeyRelatedField(source="area", queryset=Area.objects.all(), allow_null=True, required=False)
    area_name = serializers.CharField(source="area.name", read_only=True)
    production_line_id = serializers.PrimaryKeyRelatedField(
        source="production_line",
        queryset=ProductionLine.objects.all(),
        allow_null=True,
        required=False,
    )
    production_line_name = serializers.CharField(source="production_line.name", read_only=True)

    class Meta:
        model = Device
        fields = [
            "id",
            "code",
            "name",
            "ip",
            "area_id",
            "area_name",
            "production_line_id",
            "production_line_name",
            "default_status",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        ] + RESERVED_FIELDS


class EmployeeSerializer(CamelCaseModelSerializer):
    role_label = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id",
            "employee_no",
            "name",
            "role",
            "role_label",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        ] + RESERVED_FIELDS


class CodeMappingSerializer(CamelCaseModelSerializer):
    class Meta:
        model = CodeMapping
        fields = [
            "id",
            "entity_type",
            "source_system",
            "internal_code",
            "external_code",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        ] + RESERVED_FIELDS


class ScreenConfigSerializer(CamelCaseModelSerializer):
    area_id = serializers.PrimaryKeyRelatedField(source="area", queryset=Area.objects.all(), allow_null=True, required=False)
    area_name = serializers.CharField(source="area.name", read_only=True)

    def validate_page_order(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("pageOrder must be a list")
        return value

    def validate_module_settings(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("moduleSettings must be an object")
        return value

    def validate_theme_settings(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("themeSettings must be an object")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = getattr(self, "instance", None)
        area = attrs.get("area", getattr(instance, "area", None))
        screen_key = attrs.get("screen_key", getattr(instance, "screen_key", None))
        if screen_key:
            queryset = ScreenConfig.objects.filter(area=area, screen_key=screen_key)
            if instance is not None:
                queryset = queryset.exclude(pk=instance.pk)
            if queryset.exists():
                raise serializers.ValidationError("area_id and screen_key must be unique together")
        return attrs

    class Meta:
        model = ScreenConfig
        fields = [
            "id",
            "area_id",
            "area_name",
            "screen_key",
            "title",
            "subtitle",
            "rotation_interval_seconds",
            "page_order",
            "module_settings",
            "theme_settings",
            "is_active",
            "created_at",
            "updated_at",
        ] + RESERVED_FIELDS


class DisplayContentConfigSerializer(CamelCaseModelSerializer):
    def validate_promo_image_urls(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("promoImageUrls must be a list")
        return value

    class Meta:
        model = DisplayContentConfig
        fields = [
            "id",
            "config_key",
            "company_name",
            "welcome_message",
            "logo_url",
            "promo_image_urls",
            "is_active",
            "created_at",
            "updated_at",
        ] + RESERVED_FIELDS


class RuntimeParameterConfigSerializer(CamelCaseModelSerializer):
    class Meta:
        model = RuntimeParameterConfig
        fields = [
            "id",
            "config_key",
            "single_day_effective_work_hours",
            "default_standard_capacity_per_hour",
            "delay_warning_buffer_hours",
            "gantt_window_days",
            "gantt_anchor_mode",
            "auto_scroll_enabled",
            "auto_scroll_rows_threshold",
            "recent_capacity_window_hours",
            "production_trend_window_hours",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        ] + RESERVED_FIELDS

    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = getattr(self, "instance", None) or RuntimeParameterConfig()
        for attr, value in attrs.items():
            setattr(instance, attr, value)

        try:
            instance.clean()
        except Exception as exc:
            raise serializers.ValidationError(str(exc))

        return attrs


class DataSourceConfigSerializer(CamelCaseModelSerializer):
    secret_config = serializers.JSONField(write_only=True, required=False)
    secret_summary = serializers.SerializerMethodField(read_only=True)
    device_ids = serializers.PrimaryKeyRelatedField(
        source="devices",
        queryset=Device.objects.all(),
        many=True,
        required=False,
    )
    bound_devices = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DataSourceConfig
        fields = [
            "id",
            "code",
            "name",
            "source_type",
            "is_enabled",
            "refresh_interval_seconds",
            "timeout_seconds",
            "connection_config",
            "node",
            "secret_config",
            "secret_summary",
            "device_ids",
            "bound_devices",
            "notes",
            "created_at",
            "updated_at",
        ] + RESERVED_FIELDS

    def validate_secret_config(self, value):
        if value is None:
            return {"storageType": DataSourceConfig.STORAGE_NONE}
        if not isinstance(value, dict):
            raise serializers.ValidationError("secretConfig must be an object")

        storage_type = value.get("storageType")
        valid_types = {
            DataSourceConfig.STORAGE_NONE,
            DataSourceConfig.STORAGE_ENV_REF,
            DataSourceConfig.STORAGE_ENCRYPTED,
        }
        if storage_type not in valid_types:
            raise serializers.ValidationError("unsupported secret storage type")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        secret_config = attrs.pop("secret_config", None)
        devices = attrs.pop("devices", None)
        instance = getattr(self, "instance", None)
        source_type = attrs.get("source_type", getattr(instance, "source_type", None))
        node = attrs.get("node", getattr(instance, "node", {}))

        if secret_config is None and instance is None:
            secret_config = {"storageType": DataSourceConfig.STORAGE_NONE}

        if secret_config is not None:
            storage_type = secret_config.get("storageType", DataSourceConfig.STORAGE_NONE)
            attrs["secret_storage_type"] = storage_type
            attrs["secret_env_mapping"] = secret_config.get("envMapping", {}) if storage_type == DataSourceConfig.STORAGE_ENV_REF else {}
            attrs["secret_ciphertext"] = secret_config.get("ciphertext", "") if storage_type == DataSourceConfig.STORAGE_ENCRYPTED else ""
            attrs["secret_key_version"] = secret_config.get("keyVersion", "") if storage_type == DataSourceConfig.STORAGE_ENCRYPTED else ""

        if "connection_config" in attrs:
            attrs["connection_config"] = sanitize_connection_config(source_type, attrs.get("connection_config"))

        if source_type == "opcua" and node not in ({}, [], None):
            if not isinstance(node, list):
                raise serializers.ValidationError("node must be a list for opcua source")
            for item in node:
                if isinstance(item, str):
                    if not item.strip():
                        raise serializers.ValidationError("node string item cannot be empty")
                    continue
                if isinstance(item, dict):
                    node_id = item.get("nodeId")
                    comment = item.get("comment")
                    if not isinstance(node_id, str) or not node_id.strip():
                        raise serializers.ValidationError("node object must include non-empty nodeId")
                    if not isinstance(comment, str) or not comment.strip():
                        raise serializers.ValidationError("node object must include non-empty comment")
                    continue
                raise serializers.ValidationError("node items must be string or object")

        probe_instance = instance or DataSourceConfig()
        for attr, value in attrs.items():
            setattr(probe_instance, attr, value)

        try:
            probe_instance.clean()
        except Exception as exc:
            raise serializers.ValidationError(str(exc))

        if devices is not None:
            attrs["devices"] = devices

        return attrs

    def create(self, validated_data):
        devices = validated_data.pop("devices", None)
        instance = super().create(validated_data)
        if devices is not None:
            instance.devices.set(devices)
        return instance

    def update(self, instance, validated_data):
        devices = validated_data.pop("devices", None)
        updated = super().update(instance, validated_data)
        if devices is not None:
            updated.devices.set(devices)
        return updated

    def get_secret_summary(self, obj):
        return {
            "storageType": obj.secret_storage_type,
            "envKeys": sorted(obj.secret_env_mapping.keys()),
            "hasEncryptedSecret": bool(obj.secret_ciphertext),
            "keyVersion": obj.secret_key_version or None,
        }

    def get_bound_devices(self, obj):
        devices = getattr(obj, "_prefetched_objects_cache", {}).get("devices")
        if devices is None:
            devices = obj.devices.all()
        return [
            {"id": device.id, "code": device.code, "name": device.name}
            for device in devices
        ]


class MaterialSerializer(CamelCaseModelSerializer):
    class Meta:
        model = Material
        fields = [
            "id",
            "code",
            "name",
            "specification",
            "unit",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        ] + RESERVED_FIELDS


class OrderSerializer(CamelCaseModelSerializer):
    material_id = serializers.PrimaryKeyRelatedField(
        source="material", queryset=Material.objects.all(), allow_null=True, required=False,
    )
    material_name = serializers.CharField(source="material.name", read_only=True)
    production_line_id = serializers.PrimaryKeyRelatedField(
        source="production_line", queryset=ProductionLine.objects.all(), allow_null=True, required=False,
    )
    production_line_name = serializers.CharField(source="production_line.name", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_no",
            "material_id",
            "material_name",
            "production_line_id",
            "production_line_name",
            "quantity",
            "completed_quantity",
            "unit",
            "status",
            "status_label",
            "planned_start",
            "planned_end",
            "actual_start",
            "actual_end",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        ] + RESERVED_FIELDS


class PageModuleSwitchSerializer(CamelCaseModelSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = getattr(self, "instance", None)
        screen_key = attrs.get("screen_key", getattr(instance, "screen_key", None))
        module_key = attrs.get("module_key", getattr(instance, "module_key", None))

        if screen_key and module_key:
            queryset = PageModuleSwitch.objects.filter(screen_key=screen_key, module_key=module_key)
            if instance is not None:
                queryset = queryset.exclude(pk=instance.pk)
            if queryset.exists():
                raise serializers.ValidationError("screen_key and module_key must be unique together")

        return attrs

    class Meta:
        model = PageModuleSwitch
        fields = [
            "id",
            "screen_key",
            "module_key",
            "label",
            "is_enabled",
            "sort_order",
            "notes",
            "created_at",
            "updated_at",
        ] + RESERVED_FIELDS


VALID_PAGE_KEYS = frozenset({"overview", "operations", "energy", "realtime", "schedule", "risk", "simulation"})

PAGE_KEY_LABELS = {
    "overview": "综合总览",
    "operations": "运行与产量",
    "energy": "能耗数据",
    "realtime": "设备实时监控",
    "schedule": "排产总览",
    "risk": "风险说明",
    "simulation": "仿真预留",
}


class ScreenPageBindingSerializer(CamelCaseModelSerializer):
    page_key_label = serializers.SerializerMethodField()
    binding_scope_label = serializers.SerializerMethodField()
    area_id = serializers.PrimaryKeyRelatedField(
        queryset=Area.objects.all(),
        source="area",
        allow_null=True,
        required=False,
    )
    data_source_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
    )
    energy_equipment_ids = serializers.ListField(
        child=serializers.CharField(allow_blank=False),
        required=False,
        allow_empty=True,
    )

    def get_page_key_label(self, obj):
        return PAGE_KEY_LABELS.get(obj.page_key, obj.page_key)

    def get_binding_scope_label(self, obj):
        sk = "左屏" if obj.screen_key == "left" else "右屏"
        ar = getattr(obj, "area", None)
        if ar:
            return f"{ar.code}-{ar.name}的{sk}"
        return f"{sk}（未指定区域）"

    class Meta:
        model = ScreenPageBinding
        fields = [
            "id",
            "area_id",
            "binding_scope_label",
            "screen_key",
            "page_key",
            "page_key_label",
            "binding_source_type",
            "data_source_ids",
            "energy_equipment_ids",
            "is_enabled",
            "notes",
            "created_at",
            "updated_at",
        ] + RESERVED_FIELDS

    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = getattr(self, "instance", None)
        screen_key = attrs.get("screen_key", getattr(instance, "screen_key", None))
        page_key = attrs.get("page_key", getattr(instance, "page_key", None))
        if page_key and page_key not in VALID_PAGE_KEYS:
            raise serializers.ValidationError(
                {"page_key": f"page_key '{page_key}' is not a known page key"}
            )
        area = attrs.get("area", getattr(instance, "area", None))
        if screen_key and page_key:
            qs = ScreenPageBinding.objects.filter(screen_key=screen_key, page_key=page_key)
            if area is None:
                qs = qs.filter(area__isnull=True)
            else:
                qs = qs.filter(area_id=area.pk)
            if instance is not None:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "该区域（或未指定区域）下，同一屏幕与子页面的绑定已存在。"
                )
        return attrs


class OperationLogSerializer(CamelCaseModelSerializer):
    actor_username = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = OperationLog
        fields = [
            "id",
            "actor_username",
            "action",
            "target_type",
            "target_id",
            "target_label",
            "request_method",
            "request_path",
            "change_summary",
            "created_at",
        ]


class OpcUaHistorySampleSerializer(CamelCaseModelSerializer):
    quality_label = serializers.CharField(source="get_quality_display", read_only=True)

    class Meta:
        model = OpcUaHistorySample
        fields = [
            "id",
            "node_id",
            "value",
            "quality",
            "quality_label",
            "sampled_at",
            "created_at",
        ]


class DataSourceHealthSnapshotSerializer(CamelCaseModelSerializer):
    class Meta:
        model = DataSourceHealthSnapshot
        fields = [
            "id",
            "source_key",
            "display_name",
            "status",
            "last_success_at",
            "last_attempt_at",
            "is_stale",
            "fallback_in_use",
            "error_message",
            "details",
            "created_at",
            "updated_at",
        ]


class DeviceStatusSnapshotSerializer(CamelCaseModelSerializer):
    class Meta:
        model = DeviceStatusSnapshot
        fields = [
            "snapshot_key",
            "total_count",
            "running_count",
            "abnormal_count",
            "status_breakdown",
            "generated_at",
            "source_updated_at",
            "last_success_at",
        ]


class ProductionSnapshotSerializer(CamelCaseModelSerializer):
    class Meta:
        model = ProductionSnapshot
        fields = [
            "snapshot_key",
            "total_target_quantity",
            "total_produced_quantity",
            "overall_completion_rate",
            "line_summaries",
            "trend_points",
            "generated_at",
            "source_updated_at",
            "last_success_at",
        ]


class ScheduleSnapshotSerializer(CamelCaseModelSerializer):
    class Meta:
        model = ScheduleSnapshot
        fields = [
            "snapshot_key",
            "line_schedules",
            "risk_summary",
            "legend_items",
            "generated_at",
            "source_updated_at",
            "last_success_at",
        ]


class EnergySnapshotSerializer(CamelCaseModelSerializer):
    class Meta:
        model = EnergySnapshot
        fields = [
            "snapshot_key",
            "total_consumption",
            "unit",
            "area_summaries",
            "generated_at",
            "source_updated_at",
            "last_success_at",
        ]
