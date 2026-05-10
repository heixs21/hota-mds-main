# 数据模型草案

## 1. 设计前提

| 项目 | 说明 |
| --- | --- |
| 技术前提 | Django + Django REST Framework + React + MySQL + Docker |
| 一期前段范围 | 外部参观双屏大屏、后台基础配置、台账、编码映射、标准缓存模型、数据源健康状态 |
| 一期前段不包含 | 内部 Web 报表、报修真实接入、3D 仿真真实开发与联动、复杂多角色权限体系 |
| 前端数据原则 | 前端只访问本系统后端 API，不直接访问 SAP、排产库、能耗库、OPCUA、Modbus 等外部系统 |
| 大屏数据原则 | 大屏接口面向标准缓存模型，不面向外部系统原始结构 |
| 异常兜底原则 | 数据源异常时，大屏继续展示最近一次成功数据，不白屏，不在大屏提示数据过期 |
| 历史数据原则 | 当前文档按永久保留设计，不默认删除历史数据 |

## 2. 通用字段约定

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint | 主键，自增或雪花 ID，具体实现待工程阶段确定 |
| `code` | varchar(64) | 本系统主编码，业务唯一 |
| `name` | varchar(128) | 显示名称 |
| `description` | varchar(512) | 说明 |
| `is_active` | boolean | 是否启用 |
| `sort_order` | int | 排序 |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |
| `created_by` | varchar(64) | 创建人 |
| `updated_by` | varchar(64) | 更新人 |

**Django 实现补充**：`backoffice` 应用内多数实体继承抽象混入 `TimestampedModel`（自动维护 `created_at`、`updated_at`）与 `ReservedFieldsMixin`（`reserved_1`～`reserved_5`，varchar 255，默认空字符串）。下文标注「含混入」的表均包含上述字段；下表仅列出业务字段，避免重复。

---

## 3. Django `backoffice` 自定义表（与代码一致）

默认表名规则为 `backoffice_<模型名小写>`；字段类型以迁移为准，说明列与模型中文注释（`verbose_name` / `help_text`）对齐。自定义业务模型均在本应用；系统内置用户表等为 Django `contrib.auth`，不在此罗列。

### 3.1 主数据

#### `backoffice_area` — 区域 `Area`（含混入）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| （混入） | — | `reserved_1`～`reserved_5`、`created_at`、`updated_at` |
| `code` | varchar(64)，唯一 | 区域编码，业务唯一 |
| `name` | varchar(128) | 区域名称 |
| `parent_id` | bigint，可空，FK `backoffice_area` | 上级区域 |
| `is_active` | bool | 是否启用 |
| `notes` | text | 备注 |

#### `backoffice_productionline` — 产线 `ProductionLine`（含混入）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| （混入） | — | 预留与时间戳 |
| `code` | varchar(64)，唯一 | 产线编码 |
| `name` | varchar(128) | 产线名称 |
| `area_id` | bigint，可空，FK `backoffice_area` | 所属区域 |
| `is_active` | bool | 是否启用 |
| `notes` | text | 备注 |

#### `backoffice_device` — 设备 `Device`（含混入）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| （混入） | — | 预留与时间戳 |
| `code` | varchar(64)，唯一 | 设备编码 |
| `name` | varchar(128) | 设备名称 |
| `ip` | varchar(64) | 设备 IP |
| `area_id` | bigint，可空 | 所属区域 |
| `production_line_id` | bigint，可空，FK `backoffice_productionline` | 所属产线 |
| `default_status` | varchar(16) | 默认状态：running / stopped / alarm / offline |
| `is_active` | bool | 是否启用 |
| `notes` | text | 备注 |

#### `backoffice_employee` — 员工 `Employee`（含混入）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| （混入） | — | 预留与时间戳 |
| `employee_no` | varchar(64)，唯一 | 员工号（仅英文字母与数字） |
| `name` | varchar(128) | 姓名 |
| `role` | varchar(16) | employee / team_leader / supervisor |
| `is_active` | bool | 是否启用 |
| `notes` | text | 备注 |

#### `backoffice_material` — 物料 `Material`（含混入）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| （混入） | — | 预留与时间戳 |
| `code` | varchar(64)，唯一 | 物料编码 |
| `name` | varchar(128) | 物料名称 |
| `specification` | varchar(255) | 规格型号 |
| `unit` | varchar(32) | 计量单位 |
| `is_active` | bool | 是否启用 |
| `notes` | text | 备注 |

#### `backoffice_order` — 生产订单 `Order`（含混入）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| （混入） | — | 预留与时间戳 |
| `order_no` | varchar(64)，唯一 | 订单号 |
| `material_id` | bigint，可空，FK `backoffice_material` | 物料 |
| `production_line_id` | bigint，可空，FK `backoffice_productionline` | 产线 |
| `quantity` | decimal(14,2) | 计划数量 |
| `completed_quantity` | decimal(14,2) | 完成数量 |
| `unit` | varchar(32) | 数量单位 |
| `status` | varchar(16) | planned / in_progress / completed / cancelled |
| `planned_start` | datetime，可空 | 计划开始时间 |
| `planned_end` | datetime，可空 | 计划结束时间 |
| `actual_start` | datetime，可空 | 实际开始时间 |
| `actual_end` | datetime，可空 | 实际结束时间 |
| `is_active` | bool | 是否启用 |
| `notes` | text | 备注 |

### 3.2 映射与数据源

#### `backoffice_codemapping` — 编码映射 `CodeMapping`（含混入）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| （混入） | — | 预留与时间戳 |
| `entity_type` | varchar(32) | 实体类型：device / production_line / area / order / material |
| `source_system` | varchar(64) | 外部来源系统标识 |
| `internal_code` | varchar(128) | 本系统编码 |
| `external_code` | varchar(128) | 外部系统编码 |
| `is_active` | bool | 是否启用 |
| `notes` | text | 备注 |

#### `backoffice_datasourceconfig` — 数据源配置 `DataSourceConfig`（含混入）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| （混入） | — | 预留与时间戳 |
| `code` | varchar(64)，唯一 | 数据源编码 |
| `name` | varchar(128) | 数据源名称 |
| `source_type` | varchar(32) | opcua / modbus_tcp / sap_rfc / database / repair / custom |
| `is_enabled` | bool | 是否启用 |
| `refresh_interval_seconds` | 正整数 | 刷新间隔（秒） |
| `timeout_seconds` | 正整数 | 请求超时（秒） |
| `connection_config` | json | 连接参数（非密钥部分） |
| `node` | json | 节点或点表配置 |
| `secret_storage_type` | varchar(16) | none / env_ref / encrypted |
| `secret_env_mapping` | json | 环境变量映射 |
| `secret_ciphertext` | text | 密文载荷 |
| `secret_key_version` | varchar(32) | 密钥版本 |
| `notes` | text | 备注 |

与设备的关联使用显式中间表 `backoffice_datasourcedevicebinding`（见下），对应模型的 `ManyToManyField(through=...)`。

#### `backoffice_datasourcedevicebinding` — 数据源与设备绑定 `DataSourceDeviceBinding`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | bigint | 主键 |
| `data_source_id` | bigint，FK `backoffice_datasourceconfig` | 数据源配置 |
| `device_id` | bigint，FK `backoffice_device` | 设备 |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

### 3.3 大屏与运行时配置

#### `backoffice_screenconfig` — 大屏屏幕配置 `ScreenConfig`（含混入）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| （混入） | — | 预留与时间戳 |
| `area_id` | bigint，可空，FK `backoffice_area` | 所属区域；空表示兜底配置 |
| `screen_key` | varchar(16) | 左/右屏：left / right |
| `title` | varchar(128) | 大屏标题 |
| `subtitle` | varchar(255) | 副标题 |
| `rotation_interval_seconds` | 正整数 | 子页面轮播间隔（秒） |
| `page_order` | json | 子页面轮播顺序 |
| `module_settings` | json | 模块开关与参数 |
| `theme_settings` | json | 主题配置 |
| `is_active` | bool | 是否启用 |

#### `backoffice_displaycontentconfig` — 大屏展示内容 `DisplayContentConfig`（含混入）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| （混入） | — | 预留与时间戳 |
| `config_key` | varchar(32)，唯一 | 配置键 |
| `company_name` | varchar(128) | 企业或厂区名称 |
| `welcome_message` | varchar(255) | 欢迎语 |
| `logo_url` | varchar(255) | Logo 地址 |
| `promo_image_urls` | json | 宣传图片 URL 列表 |
| `is_active` | bool | 是否启用 |

#### `backoffice_runtimeparameterconfig` — 运行时参数 `RuntimeParameterConfig`（含混入）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| （混入） | — | 预留与时间戳 |
| `config_key` | varchar(32)，唯一 | 配置键 |
| `single_day_effective_work_hours` | decimal(5,2) | 单日有效工时（小时） |
| `default_standard_capacity_per_hour` | decimal(12,2) | 默认标准产能（每小时） |
| `delay_warning_buffer_hours` | decimal(8,2) | 延期预警缓冲（小时） |
| `gantt_window_days` | 正整数 | 甘特图展示窗口（天） |
| `auto_scroll_enabled` | bool | 是否启用列表自动滚动 |
| `auto_scroll_rows_threshold` | 正整数 | 超过该行数触发自动滚动 |
| `recent_capacity_window_hours` | 正整数 | 近期产能统计窗口（小时） |
| `production_trend_window_hours` | 正整数 | 产量趋势统计窗口（小时） |
| `notes` | text | 备注 |
| `is_active` | bool | 是否启用 |

#### `backoffice_pagemoduleswitch` — 页面模块开关 `PageModuleSwitch`（含混入）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| （混入） | — | 预留与时间戳 |
| `screen_key` | varchar(16) | 屏幕侧 |
| `module_key` | varchar(64) | 模块键（与前端约定） |
| `label` | varchar(128) | 模块显示名称 |
| `is_enabled` | bool | 是否启用 |
| `sort_order` | 正整数 | 排序权重 |
| `notes` | text | 备注 |

#### `backoffice_screenpagebinding` — 大屏子页数据源绑定 `ScreenPageBinding`（含混入）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| （混入） | — | 预留与时间戳 |
| `area_id` | bigint，可空 | 所属区域；空表示全局兜底 |
| `screen_key` | varchar(16) | 左/右屏 |
| `page_key` | varchar(64) | 子页面键 |
| `binding_source_type` | varchar(32) | 绑定数据源类型（与 `DataSourceConfig.source_type` 对齐） |
| `data_source_ids` | json | 绑定的数据源 ID 列表 |
| `energy_equipment_ids` | json | 能耗设备 ID（platform_equipment.e_id） |
| `is_enabled` | bool | 是否启用 |
| `notes` | text | 备注 |

### 3.4 快照、缓存与原始采样

以下快照类模型仅继承 `TimestampedModel`，**不含** `reserved_*` 预留字段。

#### `backoffice_devicestatussnapshot` — 设备状态快照 `DeviceStatusSnapshot`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `snapshot_key` | varchar(32)，唯一 | 快照键（区分数据源或视图） |
| `total_count` | 正整数 | 设备总数 |
| `running_count` | 正整数 | 运行台数 |
| `abnormal_count` | 正整数 | 异常台数 |
| `status_breakdown` | json | 状态分布 |
| `generated_at` | datetime | 快照生成时间 |
| `source_updated_at` | datetime | 源数据时间 |
| `last_success_at` | datetime | 最近成功写入时间 |
| `created_at` / `updated_at` | datetime | 记录创建与更新时间 |

#### `backoffice_productionsnapshot` — 产量快照 `ProductionSnapshot`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `snapshot_key` | varchar(32)，唯一 | 快照键 |
| `total_target_quantity` | 正整数 | 总目标产量 |
| `total_produced_quantity` | 正整数 | 总完成产量 |
| `overall_completion_rate` | decimal(5,2) | 总体完成率（%） |
| `line_summaries` | json | 按产线汇总 |
| `trend_points` | json | 趋势点 |
| `generated_at` / `source_updated_at` / `last_success_at` | datetime | 业务时间 |
| `created_at` / `updated_at` | datetime | 入库时间 |

#### `backoffice_schedulesnapshot` — 排产快照 `ScheduleSnapshot`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `snapshot_key` | varchar(32)，唯一 | 快照键 |
| `line_schedules` | json | 按产线排产数据 |
| `risk_summary` | json | 风险摘要 |
| `legend_items` | json | 图例项 |
| `generated_at` / `source_updated_at` / `last_success_at` | datetime | 业务时间 |
| `created_at` / `updated_at` | datetime | 入库时间 |

#### `backoffice_energysnapshot` — 能耗快照 `EnergySnapshot`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `snapshot_key` | varchar(32)，唯一 | 快照键 |
| `total_consumption` | decimal(12,2) | 总能耗 |
| `unit` | varchar(16) | 能耗单位，默认 kWh |
| `area_summaries` | json | 按区域汇总 |
| `generated_at` / `source_updated_at` / `last_success_at` | datetime | 业务时间 |
| `created_at` / `updated_at` | datetime | 入库时间 |

#### `backoffice_energydashboardsnapshot` — 能耗看板聚合缓存 `EnergyDashboardSnapshot`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `cache_key` | varchar(64)，唯一，索引 | 缓存键 |
| `data_source_ids` | json | 关联数据源 ID 列表 |
| `refresh_scope` | varchar(32) | 刷新范围标识 |
| `filters` | json | 筛选条件 |
| `snapshot_data` | json | 聚合结果载荷 |
| `created_at` / `updated_at` | datetime | 入库时间 |

#### `backoffice_energyequipmentcatalog` — 能耗设备目录 `EnergyEquipmentCatalog`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `data_source_id` | bigint，FK `backoffice_datasourceconfig` | 数据来源配置 |
| `equipment_id` | varchar(64)，索引 | 外部设备或表计 ID |
| `display_name` | varchar(255) | 展示名称 |
| `created_at` / `updated_at` | datetime | 入库时间 |

#### `backoffice_datasourcehealthsnapshot` — 数据源健康快照 `DataSourceHealthSnapshot`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `source_key` | varchar(32)，唯一 | 数据源键 |
| `display_name` | varchar(128) | 展示名称 |
| `status` | varchar(16) | healthy / failed |
| `last_success_at` / `last_attempt_at` | datetime，可空 | 最近成功与尝试时间 |
| `is_stale` | bool | 数据是否过期 |
| `fallback_in_use` | bool | 是否使用兜底数据 |
| `error_message` | varchar(255) | 最近错误摘要 |
| `details` | json | 扩展详情 |
| `created_at` / `updated_at` | datetime | 入库时间 |

#### `backoffice_opcuahistorysample` — OPC UA 历史采样 `OpcUaHistorySample`

无 `updated_at` 字段。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `data_source_id` | bigint，FK `backoffice_datasourceconfig` | 数据源配置 |
| `node_id` | varchar(255) | OPC UA NodeId |
| `value` | text | 采样值（文本存储） |
| `quality` | varchar(16) | good / uncertain / bad |
| `sampled_at` | datetime | 采样时间（业务时间） |
| `created_at` | datetime | 入库时间 |

### 3.5 审计

#### `backoffice_operationlog` — 操作日志 `OperationLog`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `actor_id` | bigint，可空，FK 用户表 | 操作人 |
| `action` | varchar(16) | LOGIN / CREATE / UPDATE / DELETE |
| `target_type` | varchar(64) | 目标类型 |
| `target_id` | varchar(64) | 目标主键 |
| `target_label` | varchar(255) | 目标可读标签 |
| `request_method` | varchar(16) | HTTP 方法 |
| `request_path` | varchar(255) | 请求路径 |
| `change_summary` | json | 变更摘要 |
| `created_at` | datetime | 操作时间 |

---

## 4. 一期草案与当前实现的差异（摘要）

| 草案文档中的概念 | 当前仓库实现 |
| --- | --- |
| `device_code`、`area_code` 等前缀字段名 | 模型统一使用 `code` |
| 单表大屏配置与模块开关 | 拆分为 `ScreenConfig`、`DisplayContentConfig`、`RuntimeParameterConfig`、`PageModuleSwitch`、`ScreenPageBinding` 等多表 |
| 按行存储的趋势点、排产行等待事实表 | 聚合结果大量使用 JSON 字段存放在对应 `*Snapshot` 或缓存表中 |
| `data_source_health` 多档健康枚举 | `DataSourceHealthSnapshot` 当前为 healthy / failed 两档 |

---

## 5. 当前可以先 mock 的字段

| 类型 | 字段 |
| --- | --- |
| 主数据 | 设备、产线、区域、订单、物料的本系统编码、名称、启用状态、排序、备注 |
| 展示配置 | 欢迎语、Logo URL、宣传图 URL、轮播开关、轮播间隔、模块开关、甘特图窗口天数 |
| 设备展示 | 设备总数、运行数、异常数、状态占比 |
| 产量展示 | 各产线当前订单、目标产量、已产数量、完成率、近 8 小时产量 |
| 排产展示 | 未完工订单列表、产线分组、计划开始/结束、暂停状态、延期状态、30 日窗口截取结果 |
| 延期预测 | 剩余数量、有效产能、预计完成时间、预测状态 |
| 能耗展示 | 区域能耗值、单位、区域名称、最近更新时间 |
| 健康状态 | mock 数据源状态、最近成功更新时间、是否过期、最近错误信息 |

## 6. 外部系统资料确认状态

本节按 **当前仓库实现** 更新：**能耗 MySQL**、**OPC UA（实时读点与连通探测）** 已在应用内对接；**Modbus TCP** 等在模型中存在类型，但连通探测仍以参数校验为主（见 `connection_test_services.py` 模块说明）。

### 6.1 已接入：能耗数据库（MySQL）

| 项目 | 说明 |
| --- | --- |
| 接入方式 | 在 `DataSourceConfig` 中维护 MySQL 连接（`connection_config`：`host` / `port` / `username` / `password` / `database` 等），类型为数据库类数据源；能耗看板接口、定时任务 `sync_energy_dashboard_snapshots`、表计目录同步均通过该配置直连能耗库。 |
| 主要依赖表 | `platform_equipment`（表计档案与 project/station/transformer 等筛选维度）、`po_day`（日粒度采集）、`po_month`（月粒度）；本地表 `EnergyEquipmentCatalog` 镜像 `platform_equipment` 选项；`EnergyDashboardSnapshot` 缓存聚合后的看板 JSON。 |
| 电量与统计口径（已实现） | **时段用电量**：`SUM(live_data × multiplying_power)`（见 `backend/backoffice/energy_dashboard_services.py` 模块注释及 `_q_kwh_live`）；**列表累计读数展示**列使用 `real_data`。查询侧普遍约束 `types = 1`、`is_flag = '0'`、`del_flag = '0'`，并按 `DATE(create_time)`、`HOUR(create_time)` 等做当日与按小时聚合。 |
| 大屏旋转区块说明 | 轮播中的「产量 / 排产 / 能耗区域概览」聚合快照仍可由 `load_mock_display_data` 生成演示数据；**能耗数据采集与设备状态监测看板**子页走上述真实 SQL（必要时配合本地快照 / `forceRefresh`）。 |

### 6.2 已接入：OPC UA

| 项目 | 说明 |
| --- | --- |
| 配置载体 | `DataSourceConfig`：`source_type = opcua`；`connection_config` 至少包含 **`endpointUrl`（`opc.tcp://…`）**、可选 **用户名/密码**；采集节点列表在 **`node`** 字段（JSON 数组：`nodeId` + `comment`），兼容旧版单字段 `connection_config.nodeId`。序列化校验见 `serializers.py`。 |
| 客户端实现 | `connection_test_services.py`：使用 **asyncua** 同步客户端（`asyncua.sync.Client`）执行 **`test_opcua_connection`**（握手并尝试读节点）与 **`read_opcua_nodes`**（批量读配置的 NodeId）。 |
| 大屏 / 业务用途 | **设备实时监控子页**：`display_services._build_device_realtime_monitor` 按区域或 `ScreenPageBinding` 所选数据源，调用 **`read_opcua_nodes`** 拼 CNC/机器人等卡片（`_build_opcua_realtime_card_payload` 等）。**运行态刷新**：`_refresh_device_runtime_statuses_sync` 仅对各绑定数据源做 **连通性探测**（`test_opcua_connection`），用于更新设备默认状态「运行 / 停机」及 `DeviceStatusSnapshot` 汇总；**报警/离线等细分计数在未接入对应点位规则前常为 0**。 |
| 历史采样 | 模型 **`OpcUaHistorySample`** 用于落库 OPC 历史读数（若现场启用写入 pipeline）。 |
| 与 Modbus 的差异 | **`Modbus TCP`** 等在 `DataSourceConfig` 中可选，但 **`connection_test_services` 当前不对 Modbus 做真实网络读寄存器探测**（模块注释：仍以参数校验为主）；若需与 OPC 同级探测需扩展该模块。 |

### 6.3 仍需真实外部资料确认或现场对齐的系统 / 事项

| 外部系统 / 事项 | 需要确认或对齐的内容 |
| --- | --- |
| OPC UA（深化） | 是否补充 **报警/离线** 等 NodeId 与枚举映射，使 `DeviceStatusSnapshot.status_breakdown` 不止运行/停机两类；各机床/机器人 **node 清单与注释**是否与现场 HMI 一致；刷新间隔与 `DataSourceConfig.refresh_interval_seconds` 协调。 |
| Modbus TCP / SAP RFC / 其它未探测类型 | 点表或 RFC 字段字典、真实连通与读数探测策略（当前多为配置预留）。 |
| SAP RFC | 订单号、物料号、物料名称、目标数量、单位、计划信息、RFC 连接方式、字段类型 |
| 排产系统数据库 | 未完工订单表结构、产线字段、订单状态字段、计划开始/结束字段、暂停/完工/延期口径 |
| 能耗数据库（异构或变更场景） | **默认假设**现场库与现有 SQL 一致（表名、`equipment_ids` 与 `e_id` 关联、`types` / `loop_type` / `energy_consumption` 等）。若其他厂区库结构不同，需另行视图适配或改查询；**MySQL 会话/服务器时区**与业务理解的「本地当日、整点小时」是否一致；源侧 `live_data` 业务语义是否与现行「× multiplying_power 后按小时 SUM」策略一致（增量电能与表码差的差异）。 |
| WMS | 是否进入一期真实接入、补充哪些物料字段 |
| 现场环境 | 拼接屏实际分辨率、浏览器版本、网络访问路径 |
| 安全方案 | 数据源连接信息加密方案或环境密钥方案（与 `DataSourceConfig` 的 `secret_storage_type`、密文及环境变量映射一致） |

## 7. 需要补充确认的问题

| 问题 | 影响 |
| --- | --- |
| 一个订单是否绝对不会同时分配到多条产线 | 影响订单模型、排产甘特图分组、延期预测计算 |
| WMS 是否进入一期真实接入 | 影响物料模型字段来源和 M5 接入范围 |
| 拼接屏实际分辨率和浏览器环境是什么 | 影响大屏布局、字体、自动滚动和全屏适配 |
| 后台连接信息采用数据库加密还是环境密钥引用 | 影响 `DataSourceConfig.connection_config` 与密钥字段的存储方式 |
| 延期预测是否需要“风险”和“延期”两个阈值 | 影响预测状态枚举与后台阈值配置 |
| 近 8 小时产量按整点小时、滚动小时还是采集周期聚合 | 影响产量趋势时间桶与 `ProductionSnapshot.trend_points` 口径 |
| **能耗展示两套口径是否在产品层统一**：旋转区块「能耗区域概览」（`EnergySnapshot` / `load_mock_display_data` 演示 JSON）与 **能耗看板子页**（真实 `po_day`/`po_month` 聚合）是否要对齐展示逻辑或明确标注「演示 / 实测」 | 避免业务误解；若要统一需增加从能耗库写入概览快照或取消演示路径 |
| **OPC UA**：`node` 配置是否覆盖全部需在屏上展示的工况；是否基于 OPC 点位定义 **报警、离线** 判定以替代当前「仅连通性 → 运行/停机」的简化逻辑 | 影响 `DeviceStatusSnapshot`、实时监控卡片字段与运维验收标准 |
| **Modbus TCP**：一期是否需要真实读寄存器探测与数据采集；若需要，寄存器映射与轮询策略 | 影响是否扩展 `connection_test_services` 及下游快照 |
| **能耗看板前端**：`refreshScope: live` 不返回 `hourlySeries`，小时曲线依赖首次 `full` 加载，是否与运维预期的「实时刷新」一致 | 影响是否调整接口合并策略或定时 `full` |
