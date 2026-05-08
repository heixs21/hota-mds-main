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

## 3. 主数据模型

### 3.1 设备 `device`

| 字段             | 类型           | 是否必填 | 可先 mock | 等待外部资料 | 说明                                                          |
| -------------- | ------------ | ---- | ------- | ------ | ----------------------------------------------------------- |
| `id`           | bigint       | 是    | 是       | 否      | 主键                                                          |
| `device_code`  | varchar(64)  | 是    | 是       | 否      | 本系统设备编码                                                     |
| `device_name`  | varchar(128) | 是    | 是       | 否      | 设备名称                                                        |
| `line_id`      | bigint       | 否    | 是       | 是      | 所属产线，需结合现场台账确认                                              |
| `area_id`      | bigint       | 否    | 是       | 是      | 所属区域，需结合现场台账确认                                              |
| `device_type`  | varchar(64)  | 否    | 是       | 是      | 设备类型                                                        |
| `status`       | varchar(32)  | 否    | 是       | 是      | 标准设备状态，建议枚举：`running`、`stopped`、`alarm`、`offline`、`unknown` |
| `manufacturer` | varchar(128) | 否    | 是       | 否      | 厂商                                                          |
| `model_no`     | varchar(128) | 否    | 是       | 否      | 型号                                                          |
| `is_active`    | boolean      | 是    | 是       | 否      | 是否启用                                                        |
| `remark`       | varchar(512) | 否    | 是       | 否      | 备注                                                          |
| `created_at`   | datetime     | 是    | 是       | 否      | 创建时间                                                        |
| `updated_at`   | datetime     | 是    | 是       | 否      | 更新时间                                                        |

### 3.2 产线 `production_line`

| 字段 | 类型 | 是否必填 | 可先 mock | 等待外部资料 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `id` | bigint | 是 | 是 | 否 | 主键 |
| `line_code` | varchar(64) | 是 | 是 | 否 | 本系统产线编码 |
| `line_name` | varchar(128) | 是 | 是 | 否 | 产线名称 |
| `area_id` | bigint | 否 | 是 | 是 | 所属区域 |
| `standard_capacity` | decimal(18,4) | 否 | 是 | 是 | 标准产能，用于延期预测兜底 |
| `capacity_unit` | varchar(32) | 否 | 是 | 是 | 产能单位，例如 `pcs/hour` |
| `is_active` | boolean | 是 | 是 | 否 | 是否启用 |
| `sort_order` | int | 否 | 是 | 否 | 展示排序 |
| `remark` | varchar(512) | 否 | 是 | 否 | 备注 |
| `created_at` | datetime | 是 | 是 | 否 | 创建时间 |
| `updated_at` | datetime | 是 | 是 | 否 | 更新时间 |

### 3.3 区域 `area`

| 字段 | 类型 | 是否必填 | 可先 mock | 等待外部资料 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `id` | bigint | 是 | 是 | 否 | 主键 |
| `area_code` | varchar(64) | 是 | 是 | 否 | 本系统区域编码 |
| `area_name` | varchar(128) | 是 | 是 | 否 | 区域名称 |
| `parent_id` | bigint | 否 | 是 | 否 | 上级区域 |
| `area_type` | varchar(64) | 否 | 是 | 否 | 区域类型，例如 `workshop`、`line_area`、`energy_zone` |
| `is_active` | boolean | 是 | 是 | 否 | 是否启用 |
| `sort_order` | int | 否 | 是 | 否 | 展示排序 |
| `created_at` | datetime | 是 | 是 | 否 | 创建时间 |
| `updated_at` | datetime | 是 | 是 | 否 | 更新时间 |

### 3.4 员工 `employee`

| 字段 | 类型 | 是否必填 | 可先 mock | 等待外部资料 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `id` | bigint | 是 | 是 | 否 | 主键 |
| `employee_no` | varchar(64) | 是 | 是 | 否 | 员工号，只允许英文和数字 |
| `name` | varchar(128) | 是 | 是 | 否 | 员工姓名 |
| `role` | varchar(32) | 是 | 是 | 否 | 建议枚举：`employee`、`team_leader`、`supervisor` |
| `is_active` | boolean | 是 | 是 | 否 | 是否启用 |
| `remark` | varchar(512) | 否 | 是 | 否 | 备注 |
| `created_at` | datetime | 是 | 是 | 否 | 创建时间 |
| `updated_at` | datetime | 是 | 是 | 否 | 更新时间 |

说明：
- 本轮根据数据库结构审阅意见补入员工表。
- 当前只按一期后台最小能力维护员工号、姓名、角色和启用状态，不扩展复杂组织关系和权限关系。

### 3.5 订单 `production_order`

| 字段 | 类型 | 是否必填 | 可先 mock | 等待外部资料 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `id` | bigint | 是 | 是 | 否 | 主键 |
| `order_code` | varchar(64) | 是 | 是 | 是 | 本系统订单编码或映射后订单号 |
| `external_order_no` | varchar(128) | 否 | 是 | 是 | 外部订单号，例如 SAP 或排产系统订单号 |
| `material_id` | bigint | 否 | 是 | 是 | 物料 |
| `line_id` | bigint | 否 | 是 | 是 | 当前分配产线 |
| `status` | varchar(32) | 是 | 是 | 是 | 建议枚举：`not_started`、`running`、`paused`、`completed`、`delayed`、`cancelled`、`unknown` |
| `target_quantity` | decimal(18,4) | 否 | 是 | 是 | 目标产量 |
| `produced_quantity` | decimal(18,4) | 否 | 是 | 是 | 当前已产数量 |
| `quantity_unit` | varchar(32) | 否 | 是 | 是 | 数量单位 |
| `planned_start_at` | datetime | 否 | 是 | 是 | 计划开始时间 |
| `planned_finish_at` | datetime | 否 | 是 | 是 | 计划完成时间 |
| `actual_start_at` | datetime | 否 | 是 | 是 | 实际开始时间 |
| `actual_finish_at` | datetime | 否 | 是 | 是 | 实际完成时间 |
| `is_active` | boolean | 是 | 是 | 否 | 是否启用 |
| `created_at` | datetime | 是 | 是 | 否 | 创建时间 |
| `updated_at` | datetime | 是 | 是 | 否 | 更新时间 |

### 3.6 物料 `material`

| 字段 | 类型 | 是否必填 | 可先 mock | 等待外部资料 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `id` | bigint | 是 | 是 | 否 | 主键 |
| `material_code` | varchar(64) | 是 | 是 | 是 | 本系统物料编码 |
| `external_material_no` | varchar(128) | 否 | 是 | 是 | 外部物料号 |
| `material_name` | varchar(128) | 是 | 是 | 是 | 物料名称 |
| `specification` | varchar(256) | 否 | 是 | 是 | 规格型号 |
| `unit` | varchar(32) | 否 | 是 | 是 | 计量单位 |
| `is_active` | boolean | 是 | 是 | 否 | 是否启用 |
| `created_at` | datetime | 是 | 是 | 否 | 创建时间 |
| `updated_at` | datetime | 是 | 是 | 否 | 更新时间 |

## 4. 映射与配置模型

### 4.1 编码映射 `code_mapping`

| 字段 | 类型 | 是否必填 | 可先 mock | 等待外部资料 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `id` | bigint | 是 | 是 | 否 | 主键 |
| `object_type` | varchar(32) | 是 | 是 | 否 | 建议枚举：`device`、`line`、`area`、`order`、`material` |
| `internal_code` | varchar(64) | 是 | 是 | 否 | 本系统主编码 |
| `external_system` | varchar(32) | 是 | 是 | 是 | 建议枚举：`sap`、`scheduling`、`energy`、`opcua`、`modbus`、`wms` |
| `external_code` | varchar(128) | 是 | 是 | 是 | 外部系统编码 |
| `external_name` | varchar(128) | 否 | 是 | 是 | 外部名称 |
| `mapping_status` | varchar(32) | 是 | 是 | 否 | 建议枚举：`mapped`、`unmapped`、`conflict`、`disabled` |
| `is_active` | boolean | 是 | 是 | 否 | 是否启用 |
| `created_at` | datetime | 是 | 是 | 否 | 创建时间 |
| `updated_at` | datetime | 是 | 是 | 否 | 更新时间 |

### 4.2 数据源配置 `data_source_config`

| 字段                         | 类型           | 是否必填 | 可先 mock | 等待外部资料 | 说明                                                    |
| -------------------------- | ------------ | ---- | ------- | ------ | ----------------------------------------------------- |
| `id`                       | bigint       | 是    | 是       | 否      | 主键                                                    |
| `source_code`              | varchar(64)  | 是    | 是       | 否      | 数据源编码                                                 |
| `source_name`              | varchar(128) | 是    | 是       | 否      | 数据源名称                                                 |
| `source_type`              | varchar(32)  | 是    | 是       | 否      | 建议枚举：`opcua`、`modbus_tcp`、`sap_rfc`、`database`、`mock` |
| `business_domain`          | varchar(32)  | 是    | 是       | 否      | 建议枚举：`device`、`production`、`scheduling`、`energy`      |
| `refresh_interval_seconds` | int          | 是    | 是       | 否      | 默认 300 秒                                              |
| `connection_config`        | json         | 否    | 是       | 是      | 连接配置，敏感信息需加密或引用环境密钥                                   |
| `enabled`                  | boolean      | 是    | 是       | 否      | 是否启用                                                  |
| `created_at`               | datetime     | 是    | 是       | 否      | 创建时间                                                  |
| `updated_at`               | datetime     | 是    | 是       | 否      | 更新时间                                                  |

### 4.3 左右屏配置 `screen_config`

| 字段 | 类型 | 是否必填 | 可先 mock | 等待外部资料 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `id` | bigint | 是 | 是 | 否 | 主键 |
| `screen_code` | varchar(32) | 是 | 是 | 否 | 建议枚举：`left`、`right` |
| `screen_name` | varchar(128) | 是 | 是 | 否 | 屏幕名称 |
| `welcome_text` | varchar(256) | 否 | 是 | 否 | 欢迎语 |
| `logo_url` | varchar(512) | 否 | 是 | 否 | Logo 地址 |
| `banner_image_urls` | json | 否 | 是 | 否 | 宣传图片列表 |
| `rotation_enabled` | boolean | 是 | 是 | 否 | 是否启用轮播 |
| `rotation_interval_seconds` | int | 是 | 是 | 否 | 默认 60 秒 |
| `gantt_window_days` | int | 否 | 是 | 否 | 甘特图默认 30 天 |
| `auto_scroll_enabled` | boolean | 是 | 是 | 否 | 是否自动滚动 |
| `config_json` | json | 否 | 是 | 否 | 扩展配置 |
| `updated_at` | datetime | 是 | 是 | 否 | 更新时间 |

### 4.4 页面模块开关 `screen_module_config`

| 字段 | 类型 | 是否必填 | 可先 mock | 等待外部资料 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `id` | bigint | 是 | 是 | 否 | 主键 |
| `screen_code` | varchar(32) | 是 | 是 | 否 | `left` 或 `right` |
| `module_code` | varchar(64) | 是 | 是 | 否 | 模块编码 |
| `module_name` | varchar(128) | 是 | 是 | 否 | 模块名称 |
| `enabled` | boolean | 是 | 是 | 否 | 是否显示 |
| `sort_order` | int | 否 | 是 | 否 | 排序 |
| `config_json` | json | 否 | 是 | 否 | 模块配置 |
| `updated_at` | datetime | 是 | 是 | 否 | 更新时间 |

### 4.5 操作日志 `operation_log`

| 字段 | 类型 | 是否必填 | 可先 mock | 等待外部资料 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `id` | bigint | 是 | 是 | 否 | 主键 |
| `operator_id` | bigint | 否 | 是 | 否 | 操作人 ID |
| `operator_name` | varchar(64) | 否 | 是 | 否 | 操作人名称 |
| `action` | varchar(64) | 是 | 是 | 否 | 操作动作，例如 `create`、`update`、`delete`、`login` |
| `object_type` | varchar(64) | 是 | 是 | 否 | 操作对象类型 |
| `object_id` | varchar(64) | 否 | 是 | 否 | 操作对象 ID |
| `before_json` | json | 否 | 是 | 否 | 变更前 |
| `after_json` | json | 否 | 是 | 否 | 变更后 |
| `ip_address` | varchar(64) | 否 | 是 | 否 | IP |
| `user_agent` | varchar(512) | 否 | 是 | 否 | 浏览器信息 |
| `created_at` | datetime | 是 | 是 | 否 | 操作时间 |

## 5. 标准缓存模型

### 5.1 设备状态快照 `device_status_snapshot`

| 字段 | 类型 | 是否必填 | 可先 mock | 等待外部资料 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `id` | bigint | 是 | 是 | 否 | 主键 |
| `snapshot_at` | datetime | 是 | 是 | 是 | 快照时间 |
| `source_code` | varchar(64) | 是 | 是 | 是 | 数据源编码 |
| `total_count` | int | 是 | 是 | 否 | 设备总数，来自设备台账 |
| `running_count` | int | 是 | 是 | 是 | 运行数 |
| `abnormal_count` | int | 是 | 是 | 是 | 异常数，非运行均计入 |
| `offline_count` | int | 否 | 是 | 是 | 离线数 |
| `alarm_count` | int | 否 | 是 | 是 | 报警数 |
| `status_distribution` | json | 是 | 是 | 是 | 状态占比 |
| `last_success_at` | datetime | 是 | 是 | 否 | 最近成功更新时间 |
| `created_at` | datetime | 是 | 是 | 否 | 创建时间 |

### 5.2 产量统计快照 `production_snapshot`

| 字段 | 类型 | 是否必填 | 可先 mock | 等待外部资料 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `id` | bigint | 是 | 是 | 否 | 主键 |
| `snapshot_at` | datetime | 是 | 是 | 是 | 快照时间 |
| `line_id` | bigint | 是 | 是 | 是 | 产线 |
| `line_code` | varchar(64) | 是 | 是 | 是 | 产线编码 |
| `current_order_id` | bigint | 否 | 是 | 是 | 当前订单 |
| `current_order_code` | varchar(64) | 否 | 是 | 是 | 当前订单编码 |
| `material_code` | varchar(64) | 否 | 是 | 是 | 物料编码 |
| `target_quantity` | decimal(18,4) | 否 | 是 | 是 | 目标产量 |
| `produced_quantity` | decimal(18,4) | 否 | 是 | 是 | 已产数量 |
| `completion_rate` | decimal(8,4) | 否 | 是 | 否 | 完成率，可由缓存计算 |
| `quantity_unit` | varchar(32) | 否 | 是 | 是 | 数量单位 |
| `last_success_at` | datetime | 是 | 是 | 否 | 最近成功更新时间 |
| `created_at` | datetime | 是 | 是 | 否 | 创建时间 |

### 5.3 近 8 小时产量趋势 `production_trend_point`

| 字段 | 类型 | 是否必填 | 可先 mock | 等待外部资料 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `id` | bigint | 是 | 是 | 否 | 主键 |
| `line_id` | bigint | 否 | 是 | 是 | 产线 |
| `line_code` | varchar(64) | 否 | 是 | 是 | 产线编码 |
| `bucket_start_at` | datetime | 是 | 是 | 是 | 时间桶开始 |
| `bucket_end_at` | datetime | 是 | 是 | 是 | 时间桶结束 |
| `produced_quantity` | decimal(18,4) | 是 | 是 | 是 | 该时间段产量 |
| `quantity_unit` | varchar(32) | 否 | 是 | 是 | 数量单位 |
| `source_code` | varchar(64) | 是 | 是 | 是 | 数据源 |
| `created_at` | datetime | 是 | 是 | 否 | 创建时间 |

### 5.4 未完工订单排产数据 `schedule_order_cache`

| 字段 | 类型 | 是否必填 | 可先 mock | 等待外部资料 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `id` | bigint | 是 | 是 | 否 | 主键 |
| `line_id` | bigint | 是 | 是 | 是 | 产线 |
| `line_code` | varchar(64) | 是 | 是 | 是 | 产线编码 |
| `order_id` | bigint | 否 | 是 | 是 | 订单 |
| `order_code` | varchar(64) | 是 | 是 | 是 | 订单编码 |
| `material_code` | varchar(64) | 否 | 是 | 是 | 物料编码 |
| `material_name` | varchar(128) | 否 | 是 | 是 | 物料名称 |
| `status` | varchar(32) | 是 | 是 | 是 | 订单状态 |
| `planned_start_at` | datetime | 是 | 是 | 是 | 计划开始 |
| `planned_finish_at` | datetime | 是 | 是 | 是 | 计划完成 |
| `visible_start_at` | datetime | 否 | 是 | 否 | 在 30 日窗口内的展示开始 |
| `visible_finish_at` | datetime | 否 | 是 | 否 | 在 30 日窗口内的展示结束 |
| `target_quantity` | decimal(18,4) | 否 | 是 | 是 | 目标产量 |
| `produced_quantity` | decimal(18,4) | 否 | 是 | 是 | 已产数量 |
| `is_delayed` | boolean | 是 | 是 | 否 | 是否延期 |
| `is_paused` | boolean | 是 | 是 | 否 | 是否暂停 |
| `last_success_at` | datetime | 是 | 是 | 否 | 最近成功更新时间 |
| `created_at` | datetime | 是 | 是 | 否 | 创建时间 |

### 5.5 延期预测结果 `delivery_prediction_cache`

| 字段 | 类型 | 是否必填 | 可先 mock | 等待外部资料 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `id` | bigint | 是 | 是 | 否 | 主键 |
| `order_code` | varchar(64) | 是 | 是 | 是 | 订单编码 |
| `line_code` | varchar(64) | 是 | 是 | 是 | 产线编码 |
| `target_quantity` | decimal(18,4) | 是 | 是 | 是 | 目标产量 |
| `produced_quantity` | decimal(18,4) | 是 | 是 | 是 | 已产数量 |
| `remaining_quantity` | decimal(18,4) | 是 | 是 | 否 | 剩余数量，可计算 |
| `effective_capacity` | decimal(18,4) | 否 | 是 | 是 | 有效产能 |
| `capacity_source` | varchar(32) | 否 | 是 | 是 | 建议枚举：`last_2_hours`、`last_shift`、`material_history`、`configured_standard` |
| `estimated_finish_at` | datetime | 否 | 是 | 否 | 预计完成时间 |
| `planned_finish_at` | datetime | 是 | 是 | 是 | 计划完成时间 |
| `prediction_status` | varchar(32) | 是 | 是 | 否 | 建议枚举：`normal`、`risk`、`delayed`、`not_applicable`、`unknown` |
| `calculated_at` | datetime | 是 | 是 | 否 | 计算时间 |

### 5.6 区域能耗快照 `energy_area_snapshot`

| 字段 | 类型 | 是否必填 | 可先 mock | 等待外部资料 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `id` | bigint | 是 | 是 | 否 | 主键 |
| `snapshot_at` | datetime | 是 | 是 | 是 | 快照时间 |
| `area_id` | bigint | 是 | 是 | 是 | 区域 |
| `area_code` | varchar(64) | 是 | 是 | 是 | 区域编码 |
| `area_name` | varchar(128) | 是 | 是 | 是 | 区域名称 |
| `energy_value` | decimal(18,4) | 是 | 是 | 是 | 能耗值 |
| `energy_unit` | varchar(32) | 是 | 是 | 是 | 单位，例如 `kWh` |
| `compare_value` | decimal(18,4) | 否 | 是 | 是 | 对比值，可用于环比或目标对比 |
| `last_success_at` | datetime | 是 | 是 | 否 | 最近成功更新时间 |
| `created_at` | datetime | 是 | 是 | 否 | 创建时间 |

### 5.7 数据源健康状态 `data_source_health`

| 字段 | 类型 | 是否必填 | 可先 mock | 等待外部资料 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `id` | bigint | 是 | 是 | 否 | 主键 |
| `source_code` | varchar(64) | 是 | 是 | 否 | 数据源编码 |
| `source_name` | varchar(128) | 是 | 是 | 否 | 数据源名称 |
| `business_domain` | varchar(32) | 是 | 是 | 否 | `device`、`production`、`scheduling`、`energy` |
| `health_status` | varchar(32) | 是 | 是 | 否 | 建议枚举：`healthy`、`degraded`、`failed`、`unknown` |
| `last_success_at` | datetime | 否 | 是 | 否 | 最近成功时间 |
| `last_attempt_at` | datetime | 否 | 是 | 否 | 最近尝试时间 |
| `is_stale` | boolean | 是 | 是 | 否 | 是否过期，仅后台展示 |
| `stale_after_seconds` | int | 是 | 是 | 否 | 过期阈值 |
| `last_error_message` | varchar(1024) | 否 | 是 | 是 | 最近错误信息，仅后台展示 |
| `updated_at` | datetime | 是 | 是 | 否 | 更新时间 |

## 6. 当前可以先 mock 的字段

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

## 7. 必须等待真实外部系统资料确认的字段

| 外部系统 | 需要确认字段或资料 |
| --- | --- |
| OPCUA / Modbus TCP | 点表、设备编码、设备状态点位、报警/停机/离线判定口径、刷新频率、连接方式 |
| SAP RFC | 订单号、物料号、物料名称、目标数量、单位、计划信息、RFC 连接方式、字段类型 |
| 排产系统数据库 | 未完工订单表结构、产线字段、订单状态字段、计划开始/结束字段、暂停/完工/延期口径 |
| 能耗数据库 | 区域编码、区域名称、能耗值字段、单位、统计周期、表结构、连接方式 |
| WMS | 是否进入一期真实接入、补充哪些物料字段 |
| 现场环境 | 拼接屏实际分辨率、浏览器版本、网络访问路径 |
| 安全方案 | 数据源连接信息加密方案或环境密钥方案 |

## 8. 需要补充确认的问题

| 问题 | 影响 |
| --- | --- |
| 一个订单是否绝对不会同时分配到多条产线 | 影响订单模型、排产甘特图分组、延期预测计算 |
| WMS 是否进入一期真实接入 | 影响物料模型字段来源和 M5 接入范围 |
| 拼接屏实际分辨率和浏览器环境是什么 | 影响大屏布局、字体、自动滚动和全屏适配 |
| 后台连接信息采用数据库加密还是环境密钥引用 | 影响 `data_source_config.connection_config` 的存储方式 |
| 延期预测是否需要“风险”和“延期”两个阈值 | 影响 `prediction_status` 和后台阈值配置 |
| 近 8 小时产量按整点小时、滚动小时还是采集周期聚合 | 影响 `production_trend_point` 的时间桶 |
| 能耗按当前值、今日累计、班次累计还是区域周期累计展示 | 影响 `energy_area_snapshot` 的统计口径 |
