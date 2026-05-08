# API 契约草案

## 1. 设计前提

| 项目 | 说明 |
| --- | --- |
| 技术前提 | Django + Django REST Framework + React + MySQL + Docker |
| API 风格 | RESTful JSON API |
| 前端访问原则 | 前端只访问本系统后端 API，不直接访问外部系统 |
| 大屏接口原则 | 大屏接口读取标准缓存模型，不读取外部系统原始结构 |
| 后台权限 | 后台需要登录，一期默认管理员拥有全部后台配置权限 |
| 大屏权限 | 大屏访问不登录，仅用于展示 |
| 异常兜底 | 数据源异常时，大屏接口返回最近一次成功缓存数据，不返回空白结构导致页面白屏 |
| 非目标 | 不包含内部 Web 报表、报修真实接入、3D 仿真真实联动 |

## 2. 统一 API 规范

### 2.1 URL 前缀

| 类型 | 前缀 | 说明 |
| --- | --- | --- |
| 后台 API | `/api/admin/` | 登录、台账、配置、健康状态 |
| 大屏 API | `/api/screen/` | 左右屏展示数据 |
| 系统 API | `/api/system/` | 健康检查、基础元信息 |

### 2.2 请求结构

| 类型 | 约定 |
| --- | --- |
| Content-Type | `application/json` |
| 字段命名 | JSON 使用 `snake_case` |
| 认证 | 后台接口使用 Token、Session 或 JWT，工程阶段确定；大屏展示接口一期可不登录 |
| 时间字段 | ISO 8601 字符串，示例：`2026-04-13T15:30:00+08:00` |
| 列表筛选 | 使用 query 参数，例如 `?page=1&page_size=20&keyword=xxx` |
| 创建/更新 | 使用 JSON body |

### 2.3 标准响应结构

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "data": {},
  "meta": {
    "request_id": "req_20260413153000001",
    "server_time": "2026-04-13T15:30:00+08:00"
  }
}
```

### 2.4 标准错误响应结构

```json
{
  "success": false,
  "code": "VALIDATION_ERROR",
  "message": "参数校验失败",
  "data": null,
  "errors": [
    {
      "field": "device_code",
      "message": "设备编码不能为空"
    }
  ],
  "meta": {
    "request_id": "req_20260413153000002",
    "server_time": "2026-04-13T15:30:00+08:00"
  }
}
```

### 2.5 分页结构

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "data": {
    "items": [],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 100,
      "total_pages": 5
    }
  },
  "meta": {
    "request_id": "req_20260413153000003",
    "server_time": "2026-04-13T15:30:00+08:00"
  }
}
```

### 2.6 错误码建议

| 错误码 | HTTP 状态 | 说明 |
| --- | --- | --- |
| `OK` | 200 | 成功 |
| `CREATED` | 201 | 创建成功 |
| `BAD_REQUEST` | 400 | 请求格式错误 |
| `UNAUTHORIZED` | 401 | 未登录或认证失败 |
| `FORBIDDEN` | 403 | 无权限 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `VALIDATION_ERROR` | 400 | 参数校验失败 |
| `CONFLICT` | 409 | 编码重复或状态冲突 |
| `DATA_SOURCE_FAILED` | 502 | 外部数据源访问失败，仅后台健康类接口使用 |
| `CACHE_NOT_READY` | 503 | 缓存尚未初始化，原则上大屏接口应避免返回该错误 |
| `INTERNAL_ERROR` | 500 | 系统内部错误 |

### 2.7 状态字段枚举建议

| 字段 | 枚举 |
| --- | --- |
| `device.status` | `running`、`stopped`、`alarm`、`offline`、`unknown` |
| `order.status` | `not_started`、`running`、`paused`、`completed`、`delayed`、`cancelled`、`unknown` |
| `prediction_status` | `normal`、`risk`、`delayed`、`not_applicable`、`unknown` |
| `health_status` | `healthy`、`degraded`、`failed`、`unknown` |
| `screen_code` | `left`、`right` |
| `module_code` | `welcome`、`device_overview`、`production_overview`、`production_trend`、`energy_overview`、`repair_placeholder`、`schedule_gantt`、`delivery_risk`、`simulation_placeholder` |
| `external_system` | `sap`、`scheduling`、`energy`、`opcua`、`modbus`、`wms` |
| `mapping_status` | `mapped`、`unmapped`、`conflict`、`disabled` |
| `source_type` | `opcua`、`modbus_tcp`、`sap_rfc`、`database`、`mock` |
| `business_domain` | `device`、`production`、`scheduling`、`energy` |

## 3. 后台登录

### 3.1 登录

| 项目 | 内容 |
| --- | --- |
| Method | `POST` |
| Path | `/api/admin/auth/login/` |
| Auth | 无 |
| 说明 | 管理员登录 |

请求：

```json
{
  "username": "admin",
  "password": "password"
}
```

响应：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "data": {
    "access_token": "token",
    "token_type": "Bearer",
    "expires_in": 7200,
    "user": {
      "id": 1,
      "username": "admin",
      "display_name": "管理员"
    }
  }
}
```

### 3.2 退出登录

| 项目 | 内容 |
| --- | --- |
| Method | `POST` |
| Path | `/api/admin/auth/logout/` |
| Auth | 后台登录 |
| 说明 | 退出登录 |

## 4. 后台台账维护

### 4.1 设备台账

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/api/admin/devices/` | 设备列表 |
| `POST` | `/api/admin/devices/` | 创建设备 |
| `GET` | `/api/admin/devices/{id}/` | 设备详情 |
| `PUT` | `/api/admin/devices/{id}/` | 更新设备 |
| `DELETE` | `/api/admin/devices/{id}/` | 删除或停用设备 |

设备请求字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `device_code` | string | 本系统设备编码 |
| `device_name` | string | 设备名称 |
| `line_id` | number | 所属产线 |
| `area_id` | number | 所属区域 |
| `device_type` | string | 设备类型 |
| `status` | string | 标准设备状态 |
| `is_active` | boolean | 是否启用 |
| `remark` | string | 备注 |

### 4.2 产线台账

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/api/admin/production-lines/` | 产线列表 |
| `POST` | `/api/admin/production-lines/` | 创建产线 |
| `GET` | `/api/admin/production-lines/{id}/` | 产线详情 |
| `PUT` | `/api/admin/production-lines/{id}/` | 更新产线 |
| `DELETE` | `/api/admin/production-lines/{id}/` | 删除或停用产线 |

### 4.3 区域台账

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/api/admin/areas/` | 区域列表 |
| `POST` | `/api/admin/areas/` | 创建区域 |
| `GET` | `/api/admin/areas/{id}/` | 区域详情 |
| `PUT` | `/api/admin/areas/{id}/` | 更新区域 |
| `DELETE` | `/api/admin/areas/{id}/` | 删除或停用区域 |

### 4.4 订单台账

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/api/admin/orders/` | 订单列表 |
| `POST` | `/api/admin/orders/` | 创建订单 |
| `GET` | `/api/admin/orders/{id}/` | 订单详情 |
| `PUT` | `/api/admin/orders/{id}/` | 更新订单 |
| `DELETE` | `/api/admin/orders/{id}/` | 删除或停用订单 |

### 4.5 员工台账

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/api/admin/employees/` | 员工列表 |
| `POST` | `/api/admin/employees/` | 创建员工 |
| `GET` | `/api/admin/employees/{id}/` | 员工详情 |
| `PUT` | `/api/admin/employees/{id}/` | 更新员工 |
| `DELETE` | `/api/admin/employees/{id}/` | 删除或停用员工 |

员工请求字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `employeeNo` | string | 员工号，只允许英文和数字 |
| `name` | string | 员工姓名 |
| `role` | string | `employee`、`team_leader`、`supervisor` |
| `isActive` | boolean | 是否启用 |
| `notes` | string | 备注 |

### 4.6 物料台账

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/api/admin/materials/` | 物料列表 |
| `POST` | `/api/admin/materials/` | 创建物料 |
| `GET` | `/api/admin/materials/{id}/` | 物料详情 |
| `PUT` | `/api/admin/materials/{id}/` | 更新物料 |
| `DELETE` | `/api/admin/materials/{id}/` | 删除或停用物料 |

## 5. 编码映射维护

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/api/admin/code-mappings/` | 映射列表，支持按对象类型、外部系统筛选 |
| `POST` | `/api/admin/code-mappings/` | 创建映射 |
| `GET` | `/api/admin/code-mappings/{id}/` | 映射详情 |
| `PUT` | `/api/admin/code-mappings/{id}/` | 更新映射 |
| `DELETE` | `/api/admin/code-mappings/{id}/` | 删除或停用映射 |

请求示例：

```json
{
  "object_type": "device",
  "internal_code": "DEV-001",
  "external_system": "opcua",
  "external_code": "OPCUA.DEVICE.001",
  "external_name": "1号设备",
  "mapping_status": "mapped",
  "is_active": true
}
```

## 6. 左右屏配置读取与维护

### 6.1 后台维护屏幕配置

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/api/admin/screen-configs/` | 左右屏配置列表 |
| `GET` | `/api/admin/screen-configs/{screen_code}/` | 获取指定屏配置 |
| `PUT` | `/api/admin/screen-configs/{screen_code}/` | 更新指定屏配置 |

请求示例：

```json
{
  "screen_code": "left",
  "screen_name": "左屏综合运行展示",
  "welcome_text": "欢迎参观和泰智造",
  "logo_url": "/media/logo.png",
  "banner_image_urls": ["/media/banner-1.png"],
  "rotation_enabled": true,
  "rotation_interval_seconds": 60,
  "gantt_window_days": 30,
  "auto_scroll_enabled": true
}
```

### 6.2 后台维护页面模块开关

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/api/admin/screen-modules/` | 模块开关列表 |
| `PUT` | `/api/admin/screen-modules/{id}/` | 更新模块开关 |

### 6.3 大屏读取屏幕配置

| Method | Path | Auth | 说明 |
| --- | --- | --- | --- |
| `GET` | `/api/screen/configs/left/` | 无 | 左屏读取配置 |
| `GET` | `/api/screen/configs/right/` | 无 | 右屏读取配置 |

## 7. 数据源配置维护

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/api/admin/data-source-configs/` | 数据源配置列表 |
| `POST` | `/api/admin/data-source-configs/` | 创建数据源配置 |
| `GET` | `/api/admin/data-source-configs/{id}/` | 数据源配置详情 |
| `PUT` | `/api/admin/data-source-configs/{id}/` | 更新数据源配置 |
| `DELETE` | `/api/admin/data-source-configs/{id}/` | 删除或停用数据源配置 |

请求示例：

```json
{
  "source_code": "scheduling_db",
  "source_name": "排产系统数据库",
  "source_type": "database",
  "business_domain": "scheduling",
  "refresh_interval_seconds": 300,
  "connection_config": {
    "host": "ENV:SCHEDULING_DB_HOST",
    "port": "ENV:SCHEDULING_DB_PORT",
    "database": "ENV:SCHEDULING_DB_NAME",
    "username": "ENV:SCHEDULING_DB_USER",
    "password": "SECRET:SCHEDULING_DB_PASSWORD"
  },
  "enabled": true
}
```

说明：`connection_config` 中不得写死真实密码，建议使用环境变量或密钥引用。

## 8. 数据源健康状态查询

| Method | Path | Auth | 说明 |
| --- | --- | --- | --- |
| `GET` | `/api/admin/data-source-health/` | 后台登录 | 查询全部数据源健康状态 |
| `GET` | `/api/admin/data-source-health/{source_code}/` | 后台登录 | 查询指定数据源健康状态 |

响应示例：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "data": {
    "items": [
      {
        "source_code": "scheduling_db",
        "source_name": "排产系统数据库",
        "business_domain": "scheduling",
        "health_status": "healthy",
        "last_success_at": "2026-04-13T15:25:00+08:00",
        "last_attempt_at": "2026-04-13T15:25:00+08:00",
        "is_stale": false,
        "stale_after_seconds": 600,
        "last_error_message": ""
      }
    ]
  }
}
```

## 9. 左屏展示数据接口

| 项目 | 内容 |
| --- | --- |
| Method | `GET` |
| Path | `/api/screen/left/overview/` |
| Auth | 无 |
| 数据来源 | 标准缓存模型 |
| 说明 | 左屏综合运行展示数据，包含欢迎、设备、产量、趋势、能耗、报修占位 |

响应示例：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "data": {
    "screen": {
      "screen_code": "left",
      "screen_name": "左屏综合运行展示",
      "welcome_text": "欢迎参观和泰智造",
      "logo_url": "/media/logo.png",
      "rotation_interval_seconds": 60,
      "server_time": "2026-04-13T15:30:00+08:00"
    },
    "modules": {
      "welcome": {
        "enabled": true
      },
      "device_overview": {
        "enabled": true,
        "snapshot_at": "2026-04-13T15:25:00+08:00",
        "last_success_at": "2026-04-13T15:25:00+08:00",
        "total_count": 120,
        "running_count": 100,
        "abnormal_count": 20,
        "status_distribution": [
          {
            "status": "running",
            "label": "运行",
            "count": 100,
            "ratio": 0.8333
          },
          {
            "status": "alarm",
            "label": "报警",
            "count": 8,
            "ratio": 0.0667
          },
          {
            "status": "offline",
            "label": "离线",
            "count": 12,
            "ratio": 0.1
          }
        ]
      },
      "production_overview": {
        "enabled": true,
        "items": [
          {
            "line_code": "LINE-001",
            "line_name": "1号产线",
            "current_order_code": "ORD-001",
            "material_code": "MAT-001",
            "target_quantity": 1000,
            "produced_quantity": 650,
            "completion_rate": 0.65,
            "quantity_unit": "pcs"
          }
        ]
      },
      "production_trend": {
        "enabled": true,
        "window_hours": 8,
        "items": [
          {
            "bucket_start_at": "2026-04-13T07:00:00+08:00",
            "bucket_end_at": "2026-04-13T08:00:00+08:00",
            "produced_quantity": 120,
            "quantity_unit": "pcs"
          }
        ]
      },
      "energy_overview": {
        "enabled": true,
        "items": [
          {
            "area_code": "AREA-001",
            "area_name": "一车间",
            "energy_value": 1234.56,
            "energy_unit": "kWh",
            "last_success_at": "2026-04-13T15:25:00+08:00"
          }
        ]
      },
      "repair_placeholder": {
        "enabled": true,
        "placeholder_text": "报修数据后续阶段接入"
      }
    },
    "data_fallback": {
      "using_last_success": false,
      "last_success_at": "2026-04-13T15:25:00+08:00"
    }
  }
}
```

说明：`data_fallback.using_last_success` 可供前端内部判断，但大屏 UI 不应展示“数据过期”提示。

## 10. 右屏展示数据接口

| 项目 | 内容 |
| --- | --- |
| Method | `GET` |
| Path | `/api/screen/right/overview/` |
| Auth | 无 |
| 数据来源 | 标准缓存模型 |
| 说明 | 右屏生产动态展示数据，包含排产甘特图、延期风险说明、3D 占位 |

响应示例：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "data": {
    "screen": {
      "screen_code": "right",
      "screen_name": "右屏生产动态展示",
      "rotation_interval_seconds": 60,
      "gantt_window_days": 30,
      "server_time": "2026-04-13T15:30:00+08:00"
    },
    "modules": {
      "schedule_gantt": {
        "enabled": true,
        "window_start": "2026-04-13",
        "window_end": "2026-05-13",
        "time_unit": "day",
        "auto_scroll_enabled": true,
        "lines": [
          {
            "line_code": "LINE-001",
            "line_name": "1号产线",
            "orders": [
              {
                "order_code": "ORD-001",
                "material_code": "MAT-001",
                "material_name": "示例物料",
                "status": "running",
                "planned_start_at": "2026-04-13T08:00:00+08:00",
                "planned_finish_at": "2026-04-15T18:00:00+08:00",
                "visible_start_at": "2026-04-13T08:00:00+08:00",
                "visible_finish_at": "2026-04-15T18:00:00+08:00",
                "target_quantity": 1000,
                "produced_quantity": 650,
                "is_delayed": false,
                "is_paused": false
              }
            ]
          }
        ]
      },
      "delivery_risk": {
        "enabled": true,
        "items": [
          {
            "order_code": "ORD-001",
            "line_code": "LINE-001",
            "remaining_quantity": 350,
            "effective_capacity": 80,
            "capacity_source": "last_2_hours",
            "estimated_finish_at": "2026-04-15T12:30:00+08:00",
            "planned_finish_at": "2026-04-15T18:00:00+08:00",
            "prediction_status": "normal",
            "calculated_at": "2026-04-13T15:30:00+08:00"
          }
        ]
      },
      "simulation_placeholder": {
        "enabled": true,
        "placeholder_text": "3D 仿真后续阶段接入"
      }
    },
    "data_fallback": {
      "using_last_success": false,
      "last_success_at": "2026-04-13T15:25:00+08:00"
    }
  }
}
```

## 11. 当前可以先 mock 的字段

| 类型 | 字段 |
| --- | --- |
| 大屏配置 | 欢迎语、Logo、图片、轮播间隔、模块开关、自动滚动开关、甘特图 30 日窗口 |
| 左屏设备 | 设备总数、运行数、异常数、状态占比、最近成功更新时间 |
| 左屏产量 | 产线、当前订单、物料、目标产量、已产数量、完成率、单位 |
| 左屏趋势 | 近 8 小时时间桶、每小时产量、单位 |
| 左屏能耗 | 区域名称、能耗值、单位、最近成功更新时间 |
| 左屏报修 | 占位文本和模块开关 |
| 右屏排产 | 产线分组、未完工订单、计划开始/结束、可见窗口、暂停状态、延期状态 |
| 右屏延期预测 | 剩余数量、有效产能、预计完成时间、预测状态 |
| 右屏 3D | 占位文本和模块开关 |
| 后台健康 | mock 数据源健康状态、最近成功时间、过期状态、错误信息 |

## 12. 必须等待真实外部系统资料确认的字段

| 外部系统 | 字段或资料 |
| --- | --- |
| OPCUA / Modbus TCP | 点表、设备编码、设备状态点位、报警点位、离线判定、连接方式 |
| SAP RFC | 订单号、物料号、物料名称、目标产量、单位、计划信息、RFC 字段与连接方式 |
| 排产系统数据库 | 未完工订单表结构、产线字段、订单状态字段、计划开始/结束字段、暂停/完工/延期字段 |
| 能耗数据库 | 区域编码、能耗值字段、单位、统计周期、表结构、连接方式 |
| WMS | 是否进入一期真实接入，若进入需确认物料补充字段 |
| 现场环境 | 拼接屏分辨率、浏览器版本、部署访问路径 |
| 安全方案 | 外部连接信息加密或密钥引用方式 |

## 13. 存在歧义、需要补充确认的问题

| 问题 | 影响 |
| --- | --- |
| 一个订单是否绝对不会同时分配到多条产线 | 影响订单模型、排产甘特图、延期预测 |
| 近 8 小时产量按整点小时还是滚动小时统计 | 影响趋势接口时间桶 |
| 延期预测是否需要“风险”提前量阈值 | 影响 `risk` 与 `delayed` 的判定 |
| 未开工订单是否始终不做延期判断 | 当前文档要求未开工仅显示计划，不做延期判断，需确认是否长期保持 |
| 暂停订单是否参与延期预测 | 影响暂停订单展示和预测状态 |
| 能耗展示口径是实时值、今日累计还是区间累计 | 影响能耗快照字段和展示文案 |
| 拼接屏实际分辨率和浏览器环境是什么 | 影响大屏展示接口是否需要返回布局参数 |
| 后台数据源连接配置采用加密存储还是环境变量引用 | 影响数据源配置 API 的字段设计 |
