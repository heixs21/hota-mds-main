from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class TimestampedModel(models.Model):
    """抽象基类：记录创建时间与最后更新时间。"""

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
        db_comment="创建时间",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间",
        db_comment="更新时间",
    )

    class Meta:
        abstract = True


class ReservedFieldsMixin(models.Model):
    """抽象混入：预留扩展字段，避免后续迁移频繁加列。"""

    reserved_1 = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="预留字段1",
        db_comment="预留字段1",
    )
    reserved_2 = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="预留字段2",
        db_comment="预留字段2",
    )
    reserved_3 = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="预留字段3",
        db_comment="预留字段3",
    )
    reserved_4 = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="预留字段4",
        db_comment="预留字段4",
    )
    reserved_5 = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="预留字段5",
        db_comment="预留字段5",
    )

    class Meta:
        abstract = True


class Area(ReservedFieldsMixin, TimestampedModel):
    """工厂/车间等区域层级，用于设备、产线与大屏配置的归属。"""

    code = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="区域编码",
        help_text="业务唯一编码",
        db_comment="区域编码；业务唯一编码",
    )
    name = models.CharField(max_length=128, verbose_name="区域名称", db_comment="区域名称")
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
        verbose_name="上级区域",
        db_comment="上级区域ID",
    )
    is_active = models.BooleanField(default=True, verbose_name="是否启用", db_comment="是否启用")
    notes = models.TextField(blank=True, verbose_name="备注", db_comment="备注")

    class Meta:
        verbose_name = "区域"
        verbose_name_plural = "区域"
        db_table_comment = "区域主数据：车间/区域层级"
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
    """产线主数据，关联区域；设备与订单可挂产线。"""

    code = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="产线编码",
        help_text="业务唯一编码",
        db_comment="产线编码；业务唯一编码",
    )
    name = models.CharField(max_length=128, verbose_name="产线名称", db_comment="产线名称")
    area = models.ForeignKey(
        Area,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="production_lines",
        verbose_name="所属区域",
        db_comment="所属区域ID",
    )
    is_active = models.BooleanField(default=True, verbose_name="是否启用", db_comment="是否启用")
    notes = models.TextField(blank=True, verbose_name="备注", db_comment="备注")

    class Meta:
        verbose_name = "产线"
        verbose_name_plural = "产线"
        db_table_comment = "产线主数据"
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
    """设备台账：编码、所属区域/产线及默认展示状态（大屏等）。"""

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

    code = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="设备编码",
        help_text="业务唯一编码",
        db_comment="设备编码；业务唯一编码",
    )
    name = models.CharField(max_length=128, verbose_name="设备名称", db_comment="设备名称")
    ip = models.CharField(max_length=64, blank=True, default="", verbose_name="设备 IP", db_comment="设备IP")
    area = models.ForeignKey(
        Area,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="devices",
        verbose_name="所属区域",
        db_comment="所属区域ID",
    )
    production_line = models.ForeignKey(
        ProductionLine,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="devices",
        verbose_name="所属产线",
        help_text="保存时会尝试同步区域的归属区域",
        db_comment="所属产线ID；保存时同步区域归属",
    )
    default_status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_STOPPED,
        verbose_name="默认状态",
        help_text="运行/停机/报警/离线，用于展示兜底",
        db_comment="默认状态；running/stopped/alarm/offline",
    )
    is_active = models.BooleanField(default=True, verbose_name="是否启用", db_comment="是否启用")
    notes = models.TextField(blank=True, verbose_name="备注", db_comment="备注")

    class Meta:
        verbose_name = "设备"
        verbose_name_plural = "设备"
        db_table_comment = "设备台账"
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
    """后台维护的一线员工信息（员工号、姓名、角色）。"""

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
        verbose_name="员工号",
        help_text="仅英文字母与数字",
        db_comment="员工号；仅英文字母与数字",
        validators=[
            RegexValidator(
                regex=r"^[A-Za-z0-9]+$",
                message="employee_no must contain only English letters and digits",
            )
        ],
    )
    name = models.CharField(max_length=128, verbose_name="姓名", db_comment="姓名")
    role = models.CharField(
        max_length=16,
        choices=ROLE_CHOICES,
        default=ROLE_EMPLOYEE,
        verbose_name="角色",
        db_comment="角色；employee/team_leader/supervisor",
    )
    is_active = models.BooleanField(default=True, verbose_name="是否启用", db_comment="是否启用")
    notes = models.TextField(blank=True, verbose_name="备注", db_comment="备注")

    class Meta:
        verbose_name = "员工"
        verbose_name_plural = "员工"
        db_table_comment = "员工主数据"
        ordering = ["employee_no"]

    def __str__(self):
        return f"{self.employee_no} {self.name}"


class CodeMapping(ReservedFieldsMixin, TimestampedModel):
    """本系统编码与外部系统编码的映射关系（按实体类型 + 来源系统区分）。"""

    ENTITY_CHOICES = [
        ("device", "设备"),
        ("production_line", "产线"),
        ("area", "区域"),
        ("order", "订单"),
        ("material", "物料"),
    ]

    entity_type = models.CharField(
        max_length=32,
        choices=ENTITY_CHOICES,
        verbose_name="实体类型",
        db_comment="实体类型；device/production_line/area/order/material",
    )
    source_system = models.CharField(
        max_length=64,
        verbose_name="外部来源系统",
        help_text="如 sap、energy 等标识",
        db_comment="外部来源系统标识",
    )
    internal_code = models.CharField(max_length=128, verbose_name="本系统编码", db_comment="本系统编码")
    external_code = models.CharField(max_length=128, verbose_name="外部系统编码", db_comment="外部系统编码")
    is_active = models.BooleanField(default=True, verbose_name="是否启用", db_comment="是否启用")
    notes = models.TextField(blank=True, verbose_name="备注", db_comment="备注")

    class Meta:
        verbose_name = "编码映射"
        verbose_name_plural = "编码映射"
        db_table_comment = "本系统与外部系统编码映射"
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
    """
    屏幕级配置：标题、轮播时长、模块/主题开关及该屏的子页面轮播顺序（page_order）。
    每个子页面的具体数据源绑定请在 ScreenPageBinding 维护。
    """

    SCREEN_CHOICES = [("left", "左屏"), ("right", "右屏")]

    area = models.ForeignKey(
        Area,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="screen_configs",
        verbose_name="所属区域",
        help_text="按区域区分左右屏布局；空值表示兼容旧数据的兜底配置",
        db_comment="所属区域ID；空为兜底配置",
    )
    screen_key = models.CharField(
        max_length=16,
        choices=SCREEN_CHOICES,
        verbose_name="屏幕侧",
        help_text="left/right",
        db_comment="屏幕侧；left/right",
    )
    title = models.CharField(max_length=128, verbose_name="大屏标题", db_comment="大屏标题")
    subtitle = models.CharField(max_length=255, blank=True, verbose_name="副标题", db_comment="副标题")
    rotation_interval_seconds = models.PositiveIntegerField(
        default=60,
        verbose_name="子页面轮播间隔（秒）",
        db_comment="子页面轮播间隔（秒）",
    )
    page_order = models.JSONField(
        default=list,
        blank=True,
        verbose_name="子页面轮播顺序",
        help_text="子页面键列表，如 [\"overview\", \"realtime\"]；空列表使用默认顺序",
        db_comment="子页面轮播顺序JSON",
    )
    module_settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="模块开关与参数（JSON）",
        db_comment="模块开关与参数JSON",
    )
    theme_settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="主题配置（JSON）",
        db_comment="主题配置JSON",
    )
    is_active = models.BooleanField(default=True, verbose_name="是否启用", db_comment="是否启用")

    class Meta:
        verbose_name = "大屏屏幕配置"
        verbose_name_plural = "大屏屏幕配置"
        db_table_comment = "大屏左右屏布局与轮播配置"
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
    """大屏通用展示文案：欢迎语、Logo、宣传图等（按 config_key 区分一套配置）。"""

    config_key = models.CharField(
        max_length=32,
        unique=True,
        verbose_name="配置键",
        help_text="区分多套展示方案",
        db_comment="配置键；区分多套展示方案",
    )
    company_name = models.CharField(max_length=128, verbose_name="企业/厂区名称", db_comment="企业或厂区名称")
    welcome_message = models.CharField(max_length=255, verbose_name="欢迎语", db_comment="欢迎语")
    logo_url = models.CharField(max_length=255, blank=True, verbose_name="Logo 地址", db_comment="Logo地址")
    promo_image_urls = models.JSONField(
        default=list,
        blank=True,
        verbose_name="宣传图片 URL 列表（JSON 数组）",
        db_comment="宣传图片URL列表JSON",
    )
    is_active = models.BooleanField(default=True, verbose_name="是否启用", db_comment="是否启用")

    class Meta:
        verbose_name = "大屏展示内容配置"
        verbose_name_plural = "大屏展示内容配置"
        db_table_comment = "大屏欢迎语与宣传素材配置"
        ordering = ["config_key"]

    def __str__(self):
        return self.config_key

    def clean(self):
        super().clean()
        if not isinstance(self.promo_image_urls, list):
            raise ValidationError("promo_image_urls must be a list")


class GanttAnchorMode(models.TextChoices):
    """甘特图时间窗口起点：与展示用的窗口锚点一致。"""

    EARLIEST_ORDER = "earliest_order", _("最早未完成工单")
    CURRENT_TIME = "current_time", _("当前日期")


class RuntimeParameterConfig(ReservedFieldsMixin, TimestampedModel):
    """大屏与排产业务的运行时参数：产能窗口、甘特图天数、自动滚动等。"""

    config_key = models.CharField(max_length=32, unique=True, verbose_name="配置键", db_comment="配置键")
    single_day_effective_work_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=24,
        verbose_name="单日有效工时（小时）",
        help_text="用于延期预测等计算",
        db_comment="单日有效工时（小时）",
    )
    default_standard_capacity_per_hour = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="默认标准产能（每小时）",
        db_comment="默认标准产能（每小时）",
    )
    delay_warning_buffer_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name="延期预警缓冲（小时）",
        db_comment="延期预警缓冲（小时）",
    )
    gantt_window_days = models.PositiveIntegerField(
        default=30,
        verbose_name="甘特图展示窗口（天）",
        db_comment="甘特图展示窗口（天）",
    )
    gantt_anchor_mode = models.CharField(
        max_length=32,
        choices=GanttAnchorMode.choices,
        default=GanttAnchorMode.EARLIEST_ORDER,
        verbose_name="甘特图开始时间",
        help_text="当前日期：从今日起向后覆盖窗口天数；最早未完成工单：从区域内最早一笔工单计划开始日起计。",
        db_comment="甘特窗口锚点模式 earliest_order / current_time",
    )
    auto_scroll_enabled = models.BooleanField(
        default=True,
        verbose_name="是否启用列表自动滚动",
        db_comment="是否启用列表自动滚动",
    )
    auto_scroll_rows_threshold = models.PositiveIntegerField(
        default=10,
        verbose_name="超过该行数触发自动滚动",
        db_comment="自动滚动行数阈值",
    )
    recent_capacity_window_hours = models.PositiveIntegerField(
        default=2,
        verbose_name="近期产能统计窗口（小时）",
        db_comment="近期产能统计窗口（小时）",
    )
    production_trend_window_hours = models.PositiveIntegerField(
        default=8,
        verbose_name="产量趋势统计窗口（小时）",
        db_comment="产量趋势统计窗口（小时）",
    )
    notes = models.TextField(blank=True, verbose_name="备注", db_comment="备注")
    is_active = models.BooleanField(default=True, verbose_name="是否启用", db_comment="是否启用")

    class Meta:
        verbose_name = "运行时参数配置"
        verbose_name_plural = "运行时参数配置"
        db_table_comment = "大屏甘特图与滚动等运行时参数"
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
    """设备状态聚合快照（按 snapshot_key 存最新一条成功结果供大屏读取）。"""

    snapshot_key = models.CharField(
        max_length=32,
        unique=True,
        verbose_name="快照键",
        help_text="区分不同数据源或视图",
        db_comment="快照键；区分数据源或视图",
    )
    total_count = models.PositiveIntegerField(default=0, verbose_name="设备总数", db_comment="设备总数")
    running_count = models.PositiveIntegerField(default=0, verbose_name="运行台数", db_comment="运行台数")
    abnormal_count = models.PositiveIntegerField(default=0, verbose_name="异常台数", db_comment="异常台数")
    status_breakdown = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="状态分布（JSON）",
        db_comment="状态分布JSON",
    )
    generated_at = models.DateTimeField(verbose_name="快照生成时间", db_comment="快照生成时间")
    source_updated_at = models.DateTimeField(verbose_name="源数据时间", db_comment="源数据时间")
    last_success_at = models.DateTimeField(verbose_name="最近成功写入时间", db_comment="最近成功写入时间")

    class Meta:
        verbose_name = "设备状态快照"
        verbose_name_plural = "设备状态快照"
        db_table_comment = "设备状态聚合缓存快照"
        ordering = ["snapshot_key"]

    def __str__(self):
        return self.snapshot_key


class ProductionSnapshot(TimestampedModel):
    """产量相关聚合快照：总目标/完成、产线汇总与趋势点（JSON）。"""

    snapshot_key = models.CharField(max_length=32, unique=True, verbose_name="快照键", db_comment="快照键")
    total_target_quantity = models.PositiveIntegerField(default=0, verbose_name="总目标产量", db_comment="总目标产量")
    total_produced_quantity = models.PositiveIntegerField(default=0, verbose_name="总完成产量", db_comment="总完成产量")
    overall_completion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="总体完成率（百分比）",
        db_comment="总体完成率（百分比）",
    )
    line_summaries = models.JSONField(
        default=list,
        blank=True,
        verbose_name="按产线汇总（JSON 数组）",
        db_comment="按产线汇总JSON数组",
    )
    trend_points = models.JSONField(
        default=list,
        blank=True,
        verbose_name="趋势点（JSON 数组）",
        db_comment="趋势点JSON数组",
    )
    generated_at = models.DateTimeField(verbose_name="快照生成时间", db_comment="快照生成时间")
    source_updated_at = models.DateTimeField(verbose_name="源数据时间", db_comment="源数据时间")
    last_success_at = models.DateTimeField(verbose_name="最近成功写入时间", db_comment="最近成功写入时间")

    class Meta:
        verbose_name = "产量快照"
        verbose_name_plural = "产量快照"
        db_table_comment = "产量聚合缓存快照"
        ordering = ["snapshot_key"]

    def __str__(self):
        return self.snapshot_key


class ScheduleSnapshot(TimestampedModel):
    """排产甘特与风险摘要等聚合快照（JSON 存储明细）。"""

    snapshot_key = models.CharField(max_length=32, unique=True, verbose_name="快照键", db_comment="快照键")
    line_schedules = models.JSONField(
        default=list,
        blank=True,
        verbose_name="按产线排产数据（JSON）",
        db_comment="按产线排产数据JSON",
    )
    risk_summary = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="风险摘要（JSON）",
        db_comment="风险摘要JSON",
    )
    legend_items = models.JSONField(
        default=list,
        blank=True,
        verbose_name="图例项（JSON）",
        db_comment="图例项JSON",
    )
    generated_at = models.DateTimeField(verbose_name="快照生成时间", db_comment="快照生成时间")
    source_updated_at = models.DateTimeField(verbose_name="源数据时间", db_comment="源数据时间")
    last_success_at = models.DateTimeField(verbose_name="最近成功写入时间", db_comment="最近成功写入时间")

    class Meta:
        verbose_name = "排产快照"
        verbose_name_plural = "排产快照"
        db_table_comment = "排产甘特与风险摘要缓存"
        ordering = ["snapshot_key"]

    def __str__(self):
        return self.snapshot_key


class EnergySnapshot(TimestampedModel):
    """能耗区域汇总快照：总能耗与各区域明细（JSON）。"""

    snapshot_key = models.CharField(max_length=32, unique=True, verbose_name="快照键", db_comment="快照键")
    total_consumption = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="总能耗",
        db_comment="总能耗",
    )
    unit = models.CharField(max_length=16, default="kWh", verbose_name="能耗单位", db_comment="能耗单位")
    area_summaries = models.JSONField(
        default=list,
        blank=True,
        verbose_name="按区域汇总（JSON）",
        db_comment="按区域汇总JSON",
    )
    generated_at = models.DateTimeField(verbose_name="快照生成时间", db_comment="快照生成时间")
    source_updated_at = models.DateTimeField(verbose_name="源数据时间", db_comment="源数据时间")
    last_success_at = models.DateTimeField(verbose_name="最近成功写入时间", db_comment="最近成功写入时间")

    class Meta:
        verbose_name = "能耗快照"
        verbose_name_plural = "能耗快照"
        db_table_comment = "能耗区域汇总缓存快照"
        ordering = ["snapshot_key"]

    def __str__(self):
        return self.snapshot_key


class EnergyDashboardSnapshot(TimestampedModel):
    """能耗看板接口聚合结果缓存（按数据源 + 筛选 + 刷新粒度去重，保留最后一次成功结果）。"""

    cache_key = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name="缓存键",
        help_text="区分请求维度",
        db_comment="缓存键；区分请求维度",
    )
    data_source_ids = models.JSONField(
        default=list,
        verbose_name="关联数据源 ID 列表",
        db_comment="关联数据源ID列表JSON",
    )
    refresh_scope = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="刷新范围标识",
        db_comment="刷新范围标识",
    )
    filters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="筛选条件（JSON）",
        db_comment="筛选条件JSON",
    )
    snapshot_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="聚合结果载荷（JSON）",
        db_comment="聚合结果载荷JSON",
    )

    class Meta:
        verbose_name = "能耗看板快照缓存"
        verbose_name_plural = "能耗看板快照缓存"
        db_table_comment = "能耗看板接口聚合缓存"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.cache_key[:16]}..."


class EnergyEquipmentCatalog(TimestampedModel):
    """能耗库 platform_equipment 在本地库的镜像，供后台勾选表计；由定时任务从数据源同步。"""

    data_source = models.ForeignKey(
        "DataSourceConfig",
        on_delete=models.CASCADE,
        related_name="energy_equipment_catalog",
        verbose_name="数据来源配置",
        db_comment="数据源配置ID",
    )
    equipment_id = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name="外部设备/表计 ID",
        db_comment="外部设备或表计ID",
    )
    display_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="展示名称",
        db_comment="展示名称",
    )

    class Meta:
        verbose_name = "能耗设备目录"
        verbose_name_plural = "能耗设备目录"
        db_table_comment = "能耗库设备镜像目录"
        ordering = ["display_name", "equipment_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["data_source", "equipment_id"],
                name="uniq_energy_equipment_catalog_ds_eid",
            ),
        ]

    def __str__(self):
        return f"{self.data_source_id}:{self.equipment_id}"


class DataSourceHealthSnapshot(TimestampedModel):
    """各数据源最近一次采集健康状态（成功/失败、是否过期、兜底是否启用等）。"""

    STATUS_HEALTHY = "healthy"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_HEALTHY, "healthy"),
        (STATUS_FAILED, "failed"),
    ]

    source_key = models.CharField(
        max_length=32,
        unique=True,
        verbose_name="数据源键",
        help_text="与采集任务约定一致",
        db_comment="数据源键；与采集任务约定一致",
    )
    display_name = models.CharField(max_length=128, verbose_name="展示名称", db_comment="展示名称")
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_HEALTHY,
        verbose_name="健康状态",
        db_comment="健康状态；healthy/failed",
    )
    last_success_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="最近成功时间",
        db_comment="最近成功时间",
    )
    last_attempt_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="最近尝试时间",
        db_comment="最近尝试时间",
    )
    is_stale = models.BooleanField(default=False, verbose_name="数据是否过期", db_comment="数据是否过期")
    fallback_in_use = models.BooleanField(default=False, verbose_name="是否使用兜底数据", db_comment="是否使用兜底数据")
    error_message = models.CharField(max_length=255, blank=True, verbose_name="最近错误摘要", db_comment="最近错误摘要")
    details = models.JSONField(default=dict, blank=True, verbose_name="扩展详情（JSON）", db_comment="扩展详情JSON")

    class Meta:
        verbose_name = "数据源健康快照"
        verbose_name_plural = "数据源健康快照"
        db_table_comment = "数据源采集健康状态"
        ordering = ["source_key"]

    def __str__(self):
        return self.source_key


class DataSourceDeviceBinding(TimestampedModel):
    """数据源与设备的多对多中间表：指定某数据源采集覆盖哪些设备。"""

    data_source = models.ForeignKey(
        "DataSourceConfig",
        on_delete=models.CASCADE,
        related_name="device_bindings",
        verbose_name="数据源配置",
        db_comment="数据源配置ID",
    )
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="data_source_bindings",
        verbose_name="设备",
        db_comment="设备ID",
    )

    class Meta:
        verbose_name = "数据源-设备绑定"
        verbose_name_plural = "数据源-设备绑定"
        db_table_comment = "数据源与设备多对多关系"
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
    """外部数据源连接定义：类型、轮询间隔、连接 JSON、节点配置与密钥存储策略。"""

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
        ("repair", "报修系统"),
        ("custom", "自定义"),
    ]

    code = models.CharField(max_length=64, unique=True, verbose_name="数据源编码", db_comment="数据源编码")
    name = models.CharField(max_length=128, verbose_name="数据源名称", db_comment="数据源名称")
    source_type = models.CharField(
        max_length=32,
        choices=SOURCE_CHOICES,
        verbose_name="数据源类型",
        db_comment="数据源类型；opcua/modbus_tcp/sap_rfc等",
    )
    is_enabled = models.BooleanField(default=True, verbose_name="是否启用", db_comment="是否启用")
    refresh_interval_seconds = models.PositiveIntegerField(
        default=300,
        verbose_name="刷新间隔（秒）",
        db_comment="刷新间隔（秒）",
    )
    timeout_seconds = models.PositiveIntegerField(default=30, verbose_name="请求超时（秒）", db_comment="请求超时（秒）")
    connection_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="连接参数（JSON，非密钥部分）",
        db_comment="连接参数JSON（非密钥）",
    )
    node = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="节点/点表配置（JSON）",
        db_comment="节点或点表配置JSON",
    )
    secret_storage_type = models.CharField(
        max_length=16,
        choices=STORAGE_CHOICES,
        default=STORAGE_NONE,
        verbose_name="密钥存储方式",
        db_comment="密钥存储方式；none/env_ref/encrypted",
    )
    secret_env_mapping = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="环境变量映射（JSON）",
        db_comment="环境变量映射JSON",
    )
    secret_ciphertext = models.TextField(blank=True, verbose_name="密文载荷", db_comment="密文载荷")
    secret_key_version = models.CharField(max_length=32, blank=True, verbose_name="密钥版本", db_comment="密钥版本")
    devices = models.ManyToManyField(
        Device,
        through="DataSourceDeviceBinding",
        related_name="data_sources",
        blank=True,
        verbose_name="关联设备",
    )
    notes = models.TextField(blank=True, verbose_name="备注", db_comment="备注")

    class Meta:
        verbose_name = "数据源配置"
        verbose_name_plural = "数据源配置"
        db_table_comment = "外部数据源连接与密钥配置"
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
    """OPC UA 历史采样原始记录（按数据源 + 节点 + 时间索引）。"""

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
        verbose_name="数据源配置",
        db_comment="数据源配置ID",
    )
    node_id = models.CharField(max_length=255, verbose_name="OPC UA NodeId", db_comment="OPC UA NodeId")
    value = models.TextField(blank=True, default="", verbose_name="采样值（文本）", db_comment="采样值文本")
    quality = models.CharField(
        max_length=16,
        choices=QUALITY_CHOICES,
        default=QUALITY_GOOD,
        verbose_name="数据质量",
        db_comment="数据质量；good/uncertain/bad",
    )
    sampled_at = models.DateTimeField(verbose_name="采样时间（业务时间）", db_comment="采样时间（业务时间）")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="入库时间", db_comment="入库时间")

    class Meta:
        verbose_name = "OPC UA 历史采样"
        verbose_name_plural = "OPC UA 历史采样"
        db_table_comment = "OPC UA 历史采样明细"
        ordering = ["-sampled_at", "-id"]
        indexes = [
            models.Index(fields=["data_source", "-sampled_at"], name="opcua_hist_ds_time_idx"),
        ]

    def __str__(self):
        return f"{self.data_source_id}:{self.node_id}@{self.sampled_at:%Y-%m-%d %H:%M:%S}"


class Material(ReservedFieldsMixin, TimestampedModel):
    """物料主数据：编码、名称、规格与计量单位。"""

    code = models.CharField(max_length=64, unique=True, verbose_name="物料编码", db_comment="物料编码")
    name = models.CharField(max_length=128, verbose_name="物料名称", db_comment="物料名称")
    specification = models.CharField(max_length=255, blank=True, default="", verbose_name="规格型号", db_comment="规格型号")
    unit = models.CharField(max_length=32, blank=True, default="", verbose_name="计量单位", db_comment="计量单位")
    is_active = models.BooleanField(default=True, verbose_name="是否启用", db_comment="是否启用")
    notes = models.TextField(blank=True, verbose_name="备注", db_comment="备注")

    class Meta:
        verbose_name = "物料"
        verbose_name_plural = "物料"
        db_table_comment = "物料主数据"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} {self.name}"


class Order(ReservedFieldsMixin, TimestampedModel):
    """生产订单：关联物料与产线，记录数量与计划/实际时间。"""

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

    order_no = models.CharField(max_length=64, unique=True, verbose_name="订单号", db_comment="订单号")
    material = models.ForeignKey(
        Material,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="物料",
        db_comment="物料ID",
    )
    production_line = models.ForeignKey(
        ProductionLine,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="产线",
        db_comment="产线ID",
    )
    quantity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name="计划数量",
        db_comment="计划数量",
    )
    completed_quantity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name="完成数量",
        db_comment="完成数量",
    )
    unit = models.CharField(max_length=32, blank=True, default="", verbose_name="数量单位", db_comment="数量单位")
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PLANNED,
        verbose_name="订单状态",
        db_comment="订单状态；planned/in_progress/completed/cancelled",
    )
    planned_start = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="计划开始时间",
        db_comment="计划开始时间",
    )
    planned_end = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="计划结束时间",
        db_comment="计划结束时间",
    )
    actual_start = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="实际开始时间",
        db_comment="实际开始时间",
    )
    actual_end = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="实际结束时间",
        db_comment="实际结束时间",
    )
    is_active = models.BooleanField(default=True, verbose_name="是否启用", db_comment="是否启用")
    notes = models.TextField(blank=True, verbose_name="备注", db_comment="备注")

    class Meta:
        verbose_name = "生产订单"
        verbose_name_plural = "生产订单"
        db_table_comment = "生产订单主数据"
        ordering = ["-created_at", "order_no"]

    def __str__(self):
        return self.order_no


SCREEN_KEY_CHOICES = [("left", "左屏"), ("right", "右屏")]


class PageModuleSwitch(ReservedFieldsMixin, TimestampedModel):
    """左右屏各功能模块是否展示及排序（全局模块开关）。"""

    SCREEN_CHOICES = SCREEN_KEY_CHOICES

    screen_key = models.CharField(max_length=16, choices=SCREEN_CHOICES, verbose_name="屏幕侧", db_comment="屏幕侧")
    module_key = models.CharField(
        max_length=64,
        verbose_name="模块键",
        help_text="与前端约定一致",
        db_comment="模块键；与前端约定一致",
    )
    label = models.CharField(max_length=128, verbose_name="模块显示名称", db_comment="模块显示名称")
    is_enabled = models.BooleanField(default=True, verbose_name="是否启用", db_comment="是否启用")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="排序权重", db_comment="排序权重")
    notes = models.TextField(blank=True, verbose_name="备注", db_comment="备注")

    class Meta:
        verbose_name = "页面模块开关"
        verbose_name_plural = "页面模块开关"
        db_table_comment = "大屏页面模块显示开关"
        ordering = ["screen_key", "sort_order", "module_key"]
        constraints = [
            models.UniqueConstraint(
                fields=["screen_key", "module_key"],
                name="uniq_screen_module",
            ),
        ]

    def __str__(self):
        return f"{self.screen_key}:{self.module_key}"


class ScreenPageBinding(ReservedFieldsMixin, TimestampedModel):
    """
    子页面数据源绑定：按「区域 + 左/右屏 + page_key」区分。
    area 为空时为兼容旧数据的兜底绑定；大屏解析时优先使用当前区域的绑定。
    """

    area = models.ForeignKey(
        Area,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="screen_page_bindings",
        verbose_name="所属区域",
        help_text="空表示全局兜底绑定",
        db_comment="所属区域ID；空为全局兜底",
    )
    screen_key = models.CharField(max_length=16, choices=SCREEN_KEY_CHOICES, verbose_name="屏幕侧", db_comment="屏幕侧")
    page_key = models.CharField(
        max_length=64,
        verbose_name="子页面键",
        help_text="与前端路由/组件约定一致",
        db_comment="子页面键",
    )
    binding_source_type = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="绑定数据源类型",
        help_text="与 DataSourceConfig.source_type 对齐；先选类型再选具体数据源",
        db_comment="绑定数据源类型",
    )
    data_source_ids = models.JSONField(
        default=list,
        blank=True,
        verbose_name="绑定的数据源 ID 列表（JSON）",
        db_comment="绑定的数据源ID列表JSON",
    )
    energy_equipment_ids = models.JSONField(
        default=list,
        blank=True,
        verbose_name="能耗设备 ID 列表（JSON）",
        help_text="platform_equipment.e_id，用于能耗页筛选",
        db_comment="能耗设备ID列表JSON",
    )
    is_enabled = models.BooleanField(default=True, verbose_name="是否启用", db_comment="是否启用")
    notes = models.TextField(blank=True, verbose_name="备注", db_comment="备注")

    class Meta:
        verbose_name = "大屏子页数据源绑定"
        verbose_name_plural = "大屏子页数据源绑定"
        db_table_comment = "大屏子页面数据源绑定"
        ordering = ["area_id", "screen_key", "page_key"]

    def __str__(self):
        return f"{self.screen_key}:{self.page_key}"


class OperationLog(models.Model):
    """后台用户关键操作审计日志（登录、增删改及对象摘要）。"""

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
        verbose_name="操作人",
        db_comment="操作人用户ID",
    )
    action = models.CharField(
        max_length=16,
        choices=ACTION_CHOICES,
        verbose_name="操作类型",
        db_comment="操作类型；LOGIN/CREATE/UPDATE/DELETE",
    )
    target_type = models.CharField(
        max_length=64,
        verbose_name="目标类型",
        help_text="如模型名或业务对象分类",
        db_comment="目标类型",
    )
    target_id = models.CharField(max_length=64, blank=True, verbose_name="目标主键", db_comment="目标主键")
    target_label = models.CharField(max_length=255, blank=True, verbose_name="目标可读标签", db_comment="目标可读标签")
    request_method = models.CharField(max_length=16, blank=True, verbose_name="HTTP 方法", db_comment="HTTP方法")
    request_path = models.CharField(max_length=255, blank=True, verbose_name="请求路径", db_comment="请求路径")
    change_summary = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="变更摘要（JSON）",
        db_comment="变更摘要JSON",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="操作时间", db_comment="操作时间")

    class Meta:
        verbose_name = "操作日志"
        verbose_name_plural = "操作日志"
        db_table_comment = "后台操作审计日志"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.action}:{self.target_type}:{self.target_label}"
