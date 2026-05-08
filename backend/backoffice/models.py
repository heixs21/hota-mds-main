from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ReservedFieldsMixin(models.Model):
    reserved_1 = models.CharField(max_length=255, blank=True, default="", verbose_name="预留字段1")
    reserved_2 = models.CharField(max_length=255, blank=True, default="", verbose_name="预留字段2")
    reserved_3 = models.CharField(max_length=255, blank=True, default="", verbose_name="预留字段3")
    reserved_4 = models.CharField(max_length=255, blank=True, default="", verbose_name="预留字段4")
    reserved_5 = models.CharField(max_length=255, blank=True, default="", verbose_name="预留字段5")

    class Meta:
        abstract = True


class Area(ReservedFieldsMixin, TimestampedModel):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} {self.name}"

    def save(self, *args, **kwargs):
        previous_is_active = None
        if self.pk:
            previous_is_active = (
                type(self).objects.filter(pk=self.pk).values_list("is_active", flat=True).first()
            )
        super().save(*args, **kwargs)
        if previous_is_active is True and not self.is_active:
            ProductionLine.objects.filter(area=self).update(is_active=False)
            Device.objects.filter(Q(area=self) | Q(production_line__area=self)).update(is_active=False)


class ProductionLine(ReservedFieldsMixin, TimestampedModel):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    area = models.ForeignKey(Area, null=True, blank=True, on_delete=models.PROTECT, related_name="production_lines")
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} {self.name}"

    def save(self, *args, **kwargs):
        previous_area_id = None
        previous_is_active = None
        if self.pk:
            row = type(self).objects.filter(pk=self.pk).values("area_id", "is_active").first()
            if row:
                previous_area_id = row["area_id"]
                previous_is_active = row["is_active"]
        super().save(*args, **kwargs)
        if previous_area_id != self.area_id:
            Device.objects.filter(production_line=self).update(area_id=self.area_id)
        if previous_is_active is True and not self.is_active:
            Device.objects.filter(production_line=self).update(is_active=False)


class Device(ReservedFieldsMixin, TimestampedModel):
    STATUS_RUNNING = "running"
    STATUS_STOPPED = "stopped"
    STATUS_ALARM = "alarm"
    STATUS_OFFLINE = "offline"
    STATUS_CHOICES = [
        (STATUS_RUNNING, "运行"),
        (STATUS_STOPPED, "停机"),
        (STATUS_ALARM, "报警"),
        (STATUS_OFFLINE, "离线"),
    ]

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    ip = models.CharField(max_length=64, blank=True, default="", verbose_name="设备IP")
    area = models.ForeignKey(Area, null=True, blank=True, on_delete=models.PROTECT, related_name="devices")
    production_line = models.ForeignKey(
        ProductionLine,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="devices",
    )
    default_status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_STOPPED)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} {self.name}"

    def save(self, *args, **kwargs):
        if self.production_line_id:
            line = getattr(self, "production_line", None)
            if line is None or line.pk != self.production_line_id:
                line_area_id = (
                    ProductionLine.objects.filter(pk=self.production_line_id)
                    .values_list("area_id", flat=True)
                    .first()
                )
            else:
                line_area_id = line.area_id
            if line_area_id:
                self.area_id = line_area_id
        super().save(*args, **kwargs)


class Employee(ReservedFieldsMixin, TimestampedModel):
    ROLE_EMPLOYEE = "employee"
    ROLE_TEAM_LEADER = "team_leader"
    ROLE_SUPERVISOR = "supervisor"
    ROLE_CHOICES = [
        (ROLE_EMPLOYEE, "员工"),
        (ROLE_TEAM_LEADER, "班组长"),
        (ROLE_SUPERVISOR, "主管"),
    ]

    employee_no = models.CharField(
        max_length=64,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Za-z0-9]+$",
                message="employee_no must contain only English letters and digits",
            )
        ],
    )
    name = models.CharField(max_length=128)
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=ROLE_EMPLOYEE)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["employee_no"]

    def __str__(self):
        return f"{self.employee_no} {self.name}"


class CodeMapping(ReservedFieldsMixin, TimestampedModel):
    ENTITY_CHOICES = [
        ("device", "设备"),
        ("production_line", "产线"),
        ("area", "区域"),
        ("order", "订单"),
        ("material", "物料"),
    ]

    entity_type = models.CharField(max_length=32, choices=ENTITY_CHOICES)
    source_system = models.CharField(max_length=64)
    internal_code = models.CharField(max_length=128)
    external_code = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["entity_type", "source_system", "internal_code", "external_code"]
        constraints = [
            models.UniqueConstraint(
                fields=["entity_type", "source_system", "external_code"],
                name="uniq_mapping_by_external_code",
            ),
            models.UniqueConstraint(
                fields=["entity_type", "source_system", "internal_code", "external_code"],
                name="uniq_mapping_full_pair",
            ),
        ]

    def __str__(self):
        return f"{self.entity_type}:{self.source_system}:{self.external_code}"


class ScreenConfig(ReservedFieldsMixin, TimestampedModel):
    SCREEN_CHOICES = [("left", "左屏"), ("right", "右屏")]

    area = models.ForeignKey(
        Area,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="screen_configs",
    )
    screen_key = models.CharField(max_length=16, choices=SCREEN_CHOICES)
    title = models.CharField(max_length=128)
    subtitle = models.CharField(max_length=255, blank=True)
    rotation_interval_seconds = models.PositiveIntegerField(default=60)
    page_keys = models.JSONField(default=list, blank=True)
    module_settings = models.JSONField(default=dict, blank=True)
    theme_settings = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["area__code", "screen_key"]
        constraints = [
            models.UniqueConstraint(
                fields=["area", "screen_key"],
                name="uniq_area_screen_config",
            ),
        ]

    def __str__(self):
        return self.screen_key


class DisplayContentConfig(ReservedFieldsMixin, TimestampedModel):
    config_key = models.CharField(max_length=32, unique=True)
    company_name = models.CharField(max_length=128)
    welcome_message = models.CharField(max_length=255)
    logo_url = models.CharField(max_length=255, blank=True)
    promo_image_urls = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["config_key"]

    def __str__(self):
        return self.config_key

    def clean(self):
        super().clean()
        if not isinstance(self.promo_image_urls, list):
            raise ValidationError("promo_image_urls must be a list")


class RuntimeParameterConfig(ReservedFieldsMixin, TimestampedModel):
    config_key = models.CharField(max_length=32, unique=True)
    single_day_effective_work_hours = models.DecimalField(max_digits=5, decimal_places=2, default=24)
    default_standard_capacity_per_hour = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    delay_warning_buffer_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    gantt_window_days = models.PositiveIntegerField(default=30)
    auto_scroll_enabled = models.BooleanField(default=True)
    auto_scroll_rows_threshold = models.PositiveIntegerField(default=10)
    recent_capacity_window_hours = models.PositiveIntegerField(default=2)
    production_trend_window_hours = models.PositiveIntegerField(default=8)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["config_key"]

    def __str__(self):
        return self.config_key

    def clean(self):
        super().clean()
        if self.single_day_effective_work_hours <= 0 or self.single_day_effective_work_hours > 24:
            raise ValidationError("single_day_effective_work_hours must be greater than 0 and less than or equal to 24")
        if self.gantt_window_days <= 0:
            raise ValidationError("gantt_window_days must be greater than 0")
        if self.auto_scroll_rows_threshold <= 0:
            raise ValidationError("auto_scroll_rows_threshold must be greater than 0")
        if self.recent_capacity_window_hours <= 0:
            raise ValidationError("recent_capacity_window_hours must be greater than 0")
        if self.production_trend_window_hours <= 0:
            raise ValidationError("production_trend_window_hours must be greater than 0")


class DeviceStatusSnapshot(TimestampedModel):
    snapshot_key = models.CharField(max_length=32, unique=True)
    total_count = models.PositiveIntegerField(default=0)
    running_count = models.PositiveIntegerField(default=0)
    abnormal_count = models.PositiveIntegerField(default=0)
    status_breakdown = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField()
    source_updated_at = models.DateTimeField()
    last_success_at = models.DateTimeField()

    class Meta:
        ordering = ["snapshot_key"]

    def __str__(self):
        return self.snapshot_key


class ProductionSnapshot(TimestampedModel):
    snapshot_key = models.CharField(max_length=32, unique=True)
    total_target_quantity = models.PositiveIntegerField(default=0)
    total_produced_quantity = models.PositiveIntegerField(default=0)
    overall_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_summaries = models.JSONField(default=list, blank=True)
    trend_points = models.JSONField(default=list, blank=True)
    generated_at = models.DateTimeField()
    source_updated_at = models.DateTimeField()
    last_success_at = models.DateTimeField()

    class Meta:
        ordering = ["snapshot_key"]

    def __str__(self):
        return self.snapshot_key


class ScheduleSnapshot(TimestampedModel):
    snapshot_key = models.CharField(max_length=32, unique=True)
    line_schedules = models.JSONField(default=list, blank=True)
    risk_summary = models.JSONField(default=dict, blank=True)
    legend_items = models.JSONField(default=list, blank=True)
    generated_at = models.DateTimeField()
    source_updated_at = models.DateTimeField()
    last_success_at = models.DateTimeField()

    class Meta:
        ordering = ["snapshot_key"]

    def __str__(self):
        return self.snapshot_key


class EnergySnapshot(TimestampedModel):
    snapshot_key = models.CharField(max_length=32, unique=True)
    total_consumption = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit = models.CharField(max_length=16, default="kWh")
    area_summaries = models.JSONField(default=list, blank=True)
    generated_at = models.DateTimeField()
    source_updated_at = models.DateTimeField()
    last_success_at = models.DateTimeField()

    class Meta:
        ordering = ["snapshot_key"]

    def __str__(self):
        return self.snapshot_key


class DataSourceHealthSnapshot(TimestampedModel):
    STATUS_HEALTHY = "healthy"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_HEALTHY, "healthy"),
        (STATUS_FAILED, "failed"),
    ]

    source_key = models.CharField(max_length=32, unique=True)
    display_name = models.CharField(max_length=128)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_HEALTHY)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    is_stale = models.BooleanField(default=False)
    fallback_in_use = models.BooleanField(default=False)
    error_message = models.CharField(max_length=255, blank=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["source_key"]

    def __str__(self):
        return self.source_key


class DataSourceDeviceBinding(TimestampedModel):
    data_source = models.ForeignKey(
        "DataSourceConfig",
        on_delete=models.CASCADE,
        related_name="device_bindings",
    )
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="data_source_bindings",
    )

    class Meta:
        ordering = ["data_source_id", "device_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["data_source", "device"],
                name="uniq_data_source_device_binding",
            ),
        ]

    def __str__(self):
        return f"{self.data_source_id}:{self.device_id}"


class DataSourceConfig(ReservedFieldsMixin, TimestampedModel):
    STORAGE_NONE = "none"
    STORAGE_ENV_REF = "env_ref"
    STORAGE_ENCRYPTED = "encrypted"
    STORAGE_CHOICES = [
        (STORAGE_NONE, "无敏感密钥"),
        (STORAGE_ENV_REF, "环境变量引用"),
        (STORAGE_ENCRYPTED, "密文存储"),
    ]

    SOURCE_CHOICES = [
        ("opcua", "OPCUA"),
        ("modbus_tcp", "Modbus TCP"),
        ("sap_rfc", "SAP RFC"),
        ("database", "数据库"),
        ("schedule_db", "排产数据库"),
        ("energy_db", "能耗数据库"),
        ("wms", "WMS数据库"),
        ("repair", "报修系统"),
        ("custom", "自定义"),
    ]

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    source_type = models.CharField(max_length=32, choices=SOURCE_CHOICES)
    is_enabled = models.BooleanField(default=True)
    refresh_interval_seconds = models.PositiveIntegerField(default=300)
    timeout_seconds = models.PositiveIntegerField(default=30)
    connection_config = models.JSONField(default=dict, blank=True)
    node = models.JSONField(default=dict, blank=True)
    secret_storage_type = models.CharField(max_length=16, choices=STORAGE_CHOICES, default=STORAGE_NONE)
    secret_env_mapping = models.JSONField(default=dict, blank=True)
    secret_ciphertext = models.TextField(blank=True)
    secret_key_version = models.CharField(max_length=32, blank=True)
    devices = models.ManyToManyField(
        Device,
        through="DataSourceDeviceBinding",
        related_name="data_sources",
        blank=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} {self.name}"

    def clean(self):
        super().clean()
        if self.secret_storage_type == self.STORAGE_NONE:
            if self.secret_env_mapping or self.secret_ciphertext or self.secret_key_version:
                raise ValidationError("secret config must be empty when storage type is none")
            return

        if self.secret_storage_type == self.STORAGE_ENV_REF:
            if not isinstance(self.secret_env_mapping, dict) or not self.secret_env_mapping:
                raise ValidationError("env_ref storage requires env mapping")
            if self.secret_ciphertext or self.secret_key_version:
                raise ValidationError("env_ref storage cannot include encrypted payload")
            return

        if self.secret_storage_type == self.STORAGE_ENCRYPTED:
            if not self.secret_ciphertext or not self.secret_key_version:
                raise ValidationError("encrypted storage requires ciphertext and key version")
            if self.secret_env_mapping:
                raise ValidationError("encrypted storage cannot include env mapping")


class OpcUaHistorySample(models.Model):
    QUALITY_GOOD = "good"
    QUALITY_UNCERTAIN = "uncertain"
    QUALITY_BAD = "bad"
    QUALITY_CHOICES = [
        (QUALITY_GOOD, "Good"),
        (QUALITY_UNCERTAIN, "Uncertain"),
        (QUALITY_BAD, "Bad"),
    ]

    data_source = models.ForeignKey(
        "DataSourceConfig",
        on_delete=models.CASCADE,
        related_name="opcua_history_samples",
    )
    node_id = models.CharField(max_length=255)
    value = models.TextField(blank=True, default="")
    quality = models.CharField(max_length=16, choices=QUALITY_CHOICES, default=QUALITY_GOOD)
    sampled_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-sampled_at", "-id"]
        indexes = [
            models.Index(fields=["data_source", "-sampled_at"], name="opcua_hist_ds_time_idx"),
        ]

    def __str__(self):
        return f"{self.data_source_id}:{self.node_id}@{self.sampled_at:%Y-%m-%d %H:%M:%S}"


class Material(ReservedFieldsMixin, TimestampedModel):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    specification = models.CharField(max_length=255, blank=True, default="")
    unit = models.CharField(max_length=32, blank=True, default="")
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} {self.name}"


class Order(ReservedFieldsMixin, TimestampedModel):
    STATUS_PLANNED = "planned"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PLANNED, "计划"),
        (STATUS_IN_PROGRESS, "生产中"),
        (STATUS_COMPLETED, "已完成"),
        (STATUS_CANCELLED, "已取消"),
    ]

    order_no = models.CharField(max_length=64, unique=True)
    material = models.ForeignKey(Material, null=True, blank=True, on_delete=models.PROTECT, related_name="orders")
    production_line = models.ForeignKey(
        ProductionLine, null=True, blank=True, on_delete=models.PROTECT, related_name="orders",
    )
    quantity = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    completed_quantity = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    unit = models.CharField(max_length=32, blank=True, default="")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PLANNED)
    planned_start = models.DateTimeField(null=True, blank=True)
    planned_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at", "order_no"]

    def __str__(self):
        return self.order_no


class PageModuleSwitch(ReservedFieldsMixin, TimestampedModel):
    SCREEN_CHOICES = [("left", "左屏"), ("right", "右屏")]

    screen_key = models.CharField(max_length=16, choices=SCREEN_CHOICES)
    module_key = models.CharField(max_length=64)
    label = models.CharField(max_length=128)
    is_enabled = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["screen_key", "sort_order", "module_key"]
        constraints = [
            models.UniqueConstraint(
                fields=["screen_key", "module_key"],
                name="uniq_screen_module",
            ),
        ]

    def __str__(self):
        return f"{self.screen_key}:{self.module_key}"


class OperationLog(models.Model):
    ACTION_CHOICES = [
        ("LOGIN", "登录"),
        ("CREATE", "创建"),
        ("UPDATE", "更新"),
        ("DELETE", "删除"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="operation_logs",
    )
    action = models.CharField(max_length=16, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=64)
    target_id = models.CharField(max_length=64, blank=True)
    target_label = models.CharField(max_length=255, blank=True)
    request_method = models.CharField(max_length=16, blank=True)
    request_path = models.CharField(max_length=255, blank=True)
    change_summary = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.action}:{self.target_type}:{self.target_label}"
