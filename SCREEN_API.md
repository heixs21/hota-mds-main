# 大屏前后端接口说明

本文档描述**综合运行展示大屏**（左屏 `/screen/left`、右屏 `/screen/right`）所依赖的后端接口，以及与大屏配置相关的管理端接口。路由定义见 `backend/hota_mds/urls.py`、`backend/backoffice/urls.py`。

---

## 1. 基址与约定

| 项目 | 说明 |
|------|------|
| API 前缀 | 开发环境中，前端通过环境变量 **`VITE_API_BASE_URL`** 指向 Django 服务根地址（例如 `http://127.0.0.1:8000`），再拼接下文路径。 |
| 路径风格 | 列表类接口**无尾部斜杠**（`trailing_slash=False`）；Health 与部分 auth 路径同时注册了带斜杠变体。 |
| 字段命名 | JSON 使用 **camelCase**（由序列化器与组装逻辑统一输出）。 |
| 内容类型 | `Content-Type: application/json` |

---

## 2. 统一响应结构

成功（HTTP 2xx）：

```json
{
  "success": true,
  "code": "OK",
  "message": "人类可读说明",
  "data": {}
}
```

失败：

```json
{
  "success": false,
  "code": "错误码",
  "message": "错误说明",
  "data": null
}
```

---

## 3. 大屏展示接口（无需登录）

大屏页面由 `frontend/src/ScreenDisplay.jsx` 轮询（默认每 **30 秒**）请求下列接口。

### 3.1 获取左屏载荷

| 项目 | 说明 |
|------|------|
| **Method / Path** | `GET /api/screens/left`（或 `/api/screens/left/`） |
| **鉴权** | 无（`AllowAny`） |

**`data` 顶层结构**

| 字段 | 类型 | 说明 |
|------|------|------|
| `screen` | object | 当前屏的布局与模块开关（来自 `ScreenConfig`，无激活配置时用服务端默认值）。 |
| `content` | object | 欢迎语与左屏业务模块数据。 |
| `meta` | object | 快照合并时间、数据源健康摘要、展示用格式化时间标签。 |

**`data.screen`（左屏示例字段）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `screenKey` | string | 固定为 `"left"` |
| `title` | string | 屏标题 |
| `subtitle` | string | 副标题 |
| `rotationIntervalSeconds` | number | 多页轮播间隔（秒） |
| `pageKeys` | string[] | 页面预设键，如 `["overview"]`，与前端 `PAGE_PRESETS.left` 对应 |
| `moduleSettings` | object | 模块开关，键名示例：`deviceOverview`、`productionOverview`、`productionTrend`、`energyOverview`、`repairPlaceholder` |
| `themeSettings` | object | 主题扩展（可为空对象） |
| `isActive` | boolean | 配置是否启用 |

**`data.content`（左屏）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `welcome` | object | `companyName`、`welcomeMessage`、`logoUrl`、`promoImageUrls`、`currentTime`（服务端生成） |
| `deviceOverview` | object | 设备汇总快照 + 展示字段（见下） |
| `productionOverview` | object | 产量总览：`totalTargetQuantity`、`totalProducedQuantity`、`overallCompletionRate`、`lineSummaries`、`display` |
| `productionTrend` | array | 产量趋势点：`hourLabel`、`producedQuantity`、`display` |
| `energyOverview` | object | `totalConsumption`、`unit`、`areaSummaries`、`display` |
| `repairPlaceholder` | object | 占位模块：`title`、`description`、`enabled` |

**`deviceOverview` 补充字段**

- 除快照序列化字段（如 `snapshotKey`、`totalCount`、`runningCount`、`abnormalCount`、`statusBreakdown`、`generatedAt`、`sourceUpdatedAt`、`lastSuccessAt`）外，还有：
  - **`statusItems`**：`{ key, label, accent, count, countLabel }[]`，对应运行/停机/报警/离线等。
  - **`display`**：`sourceUpdatedAtLabel`、`totalCountLabel`、`runningCountLabel`、`abnormalCountLabel`。

**`productionOverview.lineSummaries[]` 单项（示意）**

| 字段 | 类型 |
|------|------|
| `lineCode`、`lineName`、`areaName` | string |
| `currentOrderCode` | string |
| `targetQuantity`、`producedQuantity` | number |
| `completionRate` | number |
| `plannedStartAt`、`plannedEndAt`、`estimatedCompletionAt` | ISO 8601 字符串 |
| `isDelayed` | boolean |
| `display` | object：`currentOrderLabel`、`targetQuantityLabel`、`producedQuantityLabel`、`completionRateLabel`、`plannedRangeLabel`、`estimatedCompletionLabel`、`progressAccent` |

**`productionTrend[]` 单项**

| 字段 | 说明 |
|------|------|
| `hourLabel` | 如 `"08:00"` |
| `producedQuantity` | number |
| `display` | `timeLabel`、`producedQuantityLabel` |

**`energyOverview.areaSummaries[]`**

| 字段 | 说明 |
|------|------|
| `areaCode`、`areaName` | string |
| `consumption` | string（数值字符串） |
| `unit` | string，如 `"kWh"` |
| `display` | `consumptionLabel` |

**`data.meta`**

| 字段 | 类型 | 说明 |
|------|------|------|
| `lastSuccessfulAt` | string \| null | 各快照 `last_success_at` 的最大值（ISO） |
| `usingFallback` | boolean | 是否存在数据源处于 fallback |
| `dataSources` | array | 与本屏相关的数据源健康记录（左屏包含 `device`、`production`、`energy`） |
| `display` | object | `lastSuccessfulAtLabel`（格式化展示用） |

**`dataSources[]` 单项（`DataSourceHealthSnapshot`）**

| 字段 | 说明 |
|------|------|
| `sourceKey` | `device` \| `production` \| `schedule` \| `energy` |
| `displayName` | 展示名称 |
| `status` | `healthy` \| `failed` |
| `lastSuccessAt`、`lastAttemptAt` | ISO 或 null |
| `isStale`、`fallbackInUse` | boolean |
| `errorMessage` | string |
| `details` | object（如 `{"mode": "mock"}`） |

---

### 3.2 获取右屏载荷

| 项目 | 说明 |
|------|------|
| **Method / Path** | `GET /api/screens/right`（或 `/api/screens/right/`） |
| **鉴权** | 无 |

**`data.screen`**：结构同左屏，`screenKey` 为 **`"right"`**，`moduleSettings` 常见键：`schedule`、`delayLegend`、`simulationPlaceholder`。

**`data.content`（右屏）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `welcome` | object | 同左屏 |
| `schedule` | object | 甘特与排产相关（见下） |
| `delayLegend` | array | 图例项，与排产风险颜色一致（来自快照 `legend_items`） |
| `simulationPlaceholder` | object | `title`、`description`、`enabled` |

**`content.schedule`**

| 字段 | 类型 | 说明 |
|------|------|------|
| `windowDays` | number | 甘特视图天数（来自运行时参数） |
| `autoScrollEnabled` | boolean | 是否启用自动滚动 |
| `autoScrollRowsThreshold` | number | 触发行数阈值 |
| `lineSchedules` | array | 按产线分组的订单甘特数据 |
| `display` | object | `windowDaysLabel`（如 `"30 天"`） |
| `riskSummary` | object | `windowDays`、`counts`（`normal`/`warning`/`delayed`/`paused`）、**`items`**（每项含 `key`、`label`、`accent`、`color`、`count`、`countLabel`） |

**`lineSchedules[]` 单项**

| 字段 | 类型 |
|------|------|
| `lineCode`、`lineName`、`areaName` | string |
| `orders` | array |

**`orders[]` 单项（示意）**

| 字段 | 说明 |
|------|------|
| `orderCode`、`materialCode` | string |
| `status` | string，如 `in_progress`、`planned`、`paused` |
| `riskStatus` | `normal` \| `warning` \| `delayed` \| `paused` |
| `targetQuantity`、`producedQuantity` | number |
| `plannedStartAt`、`plannedEndAt` | ISO 字符串 |
| `displayStartAt`、`displayEndAt` | 日期字符串（甘特轴展示） |
| `completionRate` | number |
| `display` | `riskLabel`、`riskAccent`、`timeRangeLabel`、`completionRateLabel` |

**`data.meta`**：同左屏；右屏 `dataSources` 通常仅筛选 **`schedule`** 对应记录。

---

## 4. 管理端接口（需管理员 Token）

以下路径均在 **`/api/admin/`** 下，需携带 Header：

```http
Authorization: Bearer <access_token>
```

Token 由登录接口返回的 `data.access_token` 提供（见第 5 节）。

### 4.1 与大屏直接相关的资源

| 资源 | 路径前缀 | 说明 |
|------|----------|------|
| 屏配置 | `/api/admin/screen-configs` | 左右屏标题、轮播、`pageKeys`、`moduleSettings` 等；支持列表过滤 `screen_key`、`is_active`，关键字搜索 `keyword`。 |
| 展示文案 | `/api/admin/display-content-configs` | 欢迎语、公司名、Logo、宣传图等；大屏 `content.welcome` 读取**当前激活**配置。 |
| 运行时参数 | `/api/admin/runtime-parameter-configs` | 甘特窗口天数、自动滚动、产量趋势窗口小时数等；影响 `schedule` 与 `productionTrend`。 |
| 页面模块开关 | `/api/admin/page-module-switches` | 按 `screen_key` 筛选；与前端模块清单可对照维护。 |
| 数据源健康 | `/api/admin/data-source-healths` | **只读**；列表返回 `{ items, total }`，无分页参数时返回全部匹配项。访问时会触发确保快照存在的引导逻辑（与展示链路一致）。 |

**标准 CRUD（以 ViewSet 为例）**

| 操作 | Method | Path |
|------|--------|------|
| 列表 | GET | `/api/admin/{resource}`，查询参数：`page`、`pageSize`（最大 200）、`keyword`、`ordering`、各资源专用过滤字段 |
| 详情 | GET | `/api/admin/{resource}/{id}` |
| 新建 | POST | `/api/admin/{resource}` |
| 部分更新 | PATCH | `/api/admin/{resource}/{id}` |
| 删除 | DELETE | `/api/admin/{resource}/{id}` |
| 批量删除 | POST | `/api/admin/{resource}/batch-delete`，Body：`{ "ids": [1, 2] }`（最多 200 条） |

序列化字段与校验规则见 `backend/backoffice/serializers.py` 中各 `*Serializer`。

### 4.2 数据源配置（ opcua / database 探测等）

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/admin/data-source-configs/{id}/history` | `source_type` 为 `opcua` 时返回历史采样分页；其它类型返回空列表。支持 `page`、`pageSize`。 |
| POST | `/api/admin/data-source-configs/test-connection` | Body：`sourceType`、`connectionConfig`；用于 OPC UA / 数据库等连接探测，成功返回 `checkedAt`、`message`。 |

### 4.3 主数据（影响演示快照生成逻辑）

大屏快照生成会使用库中的 **`Device`、`ProductionLine`、`Area`** 等（若为空则回落内置演示数据）。对应管理接口：

- `/api/admin/devices`
- `/api/admin/production-lines`
- `/api/admin/areas`

---

## 5. 管理员认证（大屏后台）

| Method | Path | 鉴权 | 说明 |
|--------|------|------|------|
| POST | `/api/admin/auth/login` | 无 | Body：`username`、`password`。成功时 `data` 含 `access_token`、`token_type`（`Bearer`）、`expires_in`、`user`。 |
| POST | `/api/admin/auth/logout` | Bearer | 登出 |
| GET | `/api/admin/auth/me` | Bearer | 当前用户信息 |

---

## 6. 运维与健康检查

| Method | Path | 鉴权 | 说明 |
|--------|------|------|------|
| GET | `/api/health` | 无 | 服务存活探测 |

---

## 7. 服务端命令（非 HTTP）

初次访问大屏或缺少快照记录时，服务端会尝试写入默认快照（见 `display_services.ensure_mock_snapshots`）。亦可手动加载演示快照：

```bash
python manage.py load_mock_screen_data
```

可选：`--simulate-failure` — 将各数据源健康记录标为失败，但保留上次成功快照（用于验证右屏等 fallback 展示）。详见 `backend/backoffice/management/commands/load_mock_screen_data.py`。

---

## 8. 文档与代码对照

| 说明 | 代码位置 |
|------|----------|
| 大屏路由 | `backend/hota_mds/urls.py` |
| 展示载荷组装 | `backend/backoffice/display_services.py` → `get_screen_payload` |
| 展示视图 | `backend/backoffice/views.py` → `LeftScreenDisplayView` / `RightScreenDisplayView` |
| 统一响应 | `backend/hota_mds/responses.py` |
| 前端请求 | `frontend/src/ScreenDisplay.jsx` → `fetchScreenPayload` |

---

*若接口行为变更，请同步更新本文档与集成测试（`backend/backoffice/tests.py` 中与 `screen` 相关的用例）。*
