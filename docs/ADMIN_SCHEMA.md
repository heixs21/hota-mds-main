# 后台 Resource Schema 说明（初稿）

> 对应 M-C1：原 `adminResources.js` 已拆分为 `frontend/src/admin/schemas/`。本文档描述 **ResourceDefinition** 如何驱动 `ResourceCrudPage` + `useResourceCrud`，供新增/修改后台页时查阅。

## 1. 目录与入口

```
frontend/src/admin/schemas/
├── index.js          # 合并 resourceDefinitions、启动时 validateResourceDefinitions()
├── schemaTypes.js    # JSDoc typedef（ResourceDefinition / Field / Column）
├── schemaRegistry.js # FIELD_TYPES / CELL_FORMATS 注册表
├── validateResourceDefinitions.js  # 轻量校验（构建时 + npm run validate:schemas）
├── shared.js         # OMIT_VALUE、RESERVED_FIELDS
├── options.js        # 下拉选项常量（设备状态、屏幕键、页面键等）
├── menu.js           # ADMIN_MENU_GROUPS、DEFAULT_ADMIN_RESOURCE
├── formUtils.js      # createEmptyForm / formatCellValue / parseFieldValue 等
├── ledger.js         # 基础台账（areas、devices、orders…）
├── screen.js         # 大屏相关（screenConfigs、screenPageBindings…）
├── system.js         # 编码映射、运行参数、操作日志
└── dataSources.js    # 按 source_type 动态生成 6 份数据源 schema
```

对外兼容入口（旧 import 路径不变）：

```js
// frontend/src/adminResources.js
export * from "./admin/schemas/index.js";
```

运行时会在 `index.js` 末尾调用 `validateResourceDefinitions()`：校验菜单覆盖、`label`/`endpoint`、列/字段结构、关联 resource 引用、`bulkApplyToolbar` 形态等。完整校验（含路由注册表与菜单对齐）可单独执行：

```bash
cd frontend && npm run validate:schemas
```

## 2. 数据流

```
/admin/{slug}
  → *Page.jsx（createResourcePage("devices")）
  → ResourceCrudPage
  → useResourceCrud({ resourceKey })
  → resourceDefinitions[resourceKey]
  → adminApi（REST）
```

差异尽量写在 schema 里；引擎负责列表、分页、查询、Modal 表单、批量操作、关联资源预加载等通用行为。

## 3. ResourceDefinition 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `label` | string | 是 | 页面标题（Table 上方 H4） |
| `endpoint` | string | 是 | REST 根路径，如 `/api/admin/devices` |
| `itemLabel` | string | 推荐 | 单条记录称呼，用于「新建设备」「删除设备」等文案 |
| `columns` | Column[] | 是 | 表格列 |
| `fields` | Field[] | 可写 | 编辑表单字段；`readOnly: true` 时可 `[]` |
| `queryFields` | Field[] | 否 | 查询栏；缺省表示无筛选 |
| `useModalForm` | boolean | 否 | `true` 时用 Modal 新建/编辑（当前 19 个菜单页均为 true） |
| `readOnly` | boolean | 否 | 只读列表，无新建/编辑/删除（如 `operationLogs`） |
| `wideModal` | boolean | 否 | Modal 宽度 960px（默认 720px） |
| `relatedResources` | string[] | 否 | 预加载关联 resource 的选项（如 `screenConfigs` → `screenPageBindings`） |
| `fixedListParams` | object | 否 | 列表/查询固定 query（数据源页按 `source_type` 过滤） |
| `fixedSourceType` | string | 否 | 保存时强制写入 `sourceType`（数据源页） |
| `supportsTestConnection` | boolean | 否 | 表单内显示「测试连接」 |
| `supportsHistory` | boolean | 否 | 表格增加「查看历史」列（OPC UA） |
| `supportsCopyAsNew` | boolean | 否 | 工具栏「复制新增」（OPC UA） |
| `bulkApplyToolbar` | object | 否 | 列表上方批量设置工具条（见 §6） |

### Column

| 属性 | 说明 |
|------|------|
| `key` | 行数据字段名（camelCase，与 API 一致） |
| `label` | 表头文案 |
| `options` | 可选；枚举列显示中文 label |
| `cellFormat` | 见 §5 |
| `resource` | `cellFormat: "resourceLinks"` 时跳转目标 resourceKey |
| `showWhenPageKey` | 仅当 `row.pageKey` 匹配时显示该列值，否则 `-` |

### Field（表单 / 查询共用）

| 属性 | 说明 |
|------|------|
| `key` | 字段名；查询字段常用 snake_case（如 `is_active`），表单用 camelCase |
| `label` | 标签 |
| `type` | 见 §4 |
| `required` | 表单校验 |
| `defaultValue` | 新建默认值 |
| `placeholder` | 输入提示 |
| `options` | `select` 的 `{ value, label }[]` |
| `resource` | `resourceSelect` / `resourceMultiSelect*` 关联的 resourceKey |
| `allowBlank` | 关联选择允许空 |
| `storage` | 嵌套写入 `connectionConfig` 等子对象 |
| `omitIfBlank` | 空 JSON 时不提交该字段 |
| `hideInForm` | 不在表单展示（预留字段） |
| `visibleWhen` | `{ field, value }` 条件显示 |
| `screenKeyField` / `areaIdField` | `screenPageTransfer` 联动屏幕与区域 |
| `filterByField` / `filterOptionKey` | `resourceMultiSelectFiltered` 按表单其它字段过滤选项 |
| `dataSourceField` | `energyDatabaseEquipmentMulti` 读取已选数据源 |

查询专用：`queryFields` 中 `type: "date"` 会渲染日期选择；`resourceSelect` 会加载 `relatedOptions`。

## 4. Field 类型（`ResourceField.jsx`）

| type | 渲染 | 备注 |
|------|------|------|
| `text` | Input | 默认 |
| `textarea` | Input.TextArea | |
| `integer` | InputNumber（整数） | |
| `decimal` | InputNumber（小数） | |
| `checkbox` | Checkbox | 提交 boolean |
| `select` | Select | 需 `options` |
| `date` | DatePicker | 主要用于 queryFields |
| `json` | TextArea（JSON 字符串） | 保存前 `JSON.parse` |
| `resourceSelect` | Select | 选项来自 `relatedOptions[resource]` |
| `resourceMultiSelect` | Select mode=multiple | ID 数组 |
| `resourceMultiSelectFiltered` | 同上 + 联动过滤 | 如按 `areaId` 过滤设备 |
| `energyDatabaseEquipmentMulti` | 专用多选 | 能耗页，依赖 `dataSourceIds` |
| `screenPageTransfer` | Transfer 穿梭框 | 轮播子页面顺序 |
| `staticHint` | 纯展示提示 | 不参与提交 |

嵌套字段：设 `storage: "connectionConfig"` 时，读写 `item.connectionConfig[key]`，提交时由 `resourcePayload.js` 组装。

## 5. 列格式化（`formatCellValue`）

| cellFormat | 行为 |
|------------|------|
| `cstDateTime` | 东八区 `YYYY-MM-DD HH:mm:ss` |
| `idCount` | 数组长度，如 `3 项` |
| `resourceLinks` | 表格内可点击跳转；纯文本模式为名称拼接 |

未指定 `cellFormat` 时：boolean → 是/否；有 `column.options` 时映射 label；object → JSON 或密文摘要。

## 6. bulkApplyToolbar

两种形态：

**单值批量**（如屏幕轮播时长、数据源轮询间隔）：

```js
bulkApplyToolbar: {
  apiPath: "bulk-rotation-interval",
  valueKey: "rotationIntervalSeconds",
  label: "轮播时长（秒）",
  defaultInput: "60",
  min: 5,
  max: 86400,
  successMessage: (count, seconds) => `已更新 ${count} 条…`,
  errorFallback: "批量设置失败…",
}
```

**多字段批量**（`runtimeParameterConfigs`）：

```js
bulkApplyToolbar: {
  apiPath: "bulk-runtime-fields",
  fields: [
    { key: "singleDayEffectiveWorkHours", label: "日有效工时", kind: "decimal", … },
    { key: "ganttWindowDays", label: "甘特窗口天数", kind: "integer", … },
  ],
  successMessage: (count) => `已批量更新 ${count} 条…`,
}
```

勾选表格行后，在查询栏右侧触发；请求路径为 `{endpoint}/{apiPath}`。

## 7. Tier 分级（扩展策略）

> **正式 SOP 与决策流程：** `docs/PLAN.md` §12。本节为速查。

| 级别 | 适用 | 做法 |
|------|------|------|
| **Tier A** | 标准 CRUD 台账/配置 | 只改 `ledger.js` / `screen.js` / `system.js` 或 `dataSources.js`，加 menu 项 + 薄 `*Page.jsx` + 路由注册 |
| **Tier A+** | Tier A + 引擎已有能力 | 使用 `bulkApplyToolbar`、`screenPageTransfer`、`wideModal`、`readOnly` 等，仍不写 Page 逻辑 |
| **Tier B** | 需定制 UI 块，但列表仍用引擎 | schema + 引擎扩展点（**M-C4**，未做前尽量避免） |
| **Tier C** | 流程/布局完全特殊 | 独立 Page 组件，自行调 API |

当前 19 个侧栏页均为 **Tier A / A+**。同一 `resourceKey` 在引擎内出现 **≥2 处硬编码** 时，应升 Tier B/C。

### Tier 决策（速查）

```text
新后台页 → 列表+Modal CRUD？ → 是 → field/column 够用？ → 是 → Tier A(+)
                              → 否 → Tier C
                              → 字段类型不够 → 扩展 ResourceField 或 Tier C
```

## 8. 示例

### Tier A：设备台账 `devices`

文件：`frontend/src/admin/schemas/ledger.js`

要点：

- 标准 `columns` + `queryFields`（关键字、状态、区域、产线、日期）
- 表单含 `resourceSelect` 关联 `areas` / `productionLines`
- `...RESERVED_FIELDS` 保留扩展位
- 页面：`DevicesPage.jsx` → `createResourcePage("devices")`

### Tier A+：左右屏配置 `screenConfigs`

文件：`frontend/src/admin/schemas/screen.js`

要点：

- `wideModal: true`、复杂 JSON 字段、`screenPageTransfer` 穿梭框
- `bulkApplyToolbar` 批量改轮播时长
- `relatedResources: ["screenPageBindings"]` 预加载绑定数据

### 动态 schema：数据源

文件：`frontend/src/admin/schemas/dataSources.js`

- `buildDataSourceResources()` 为 6 种 `source_type` 生成独立 resourceKey（如 `dataSourceOpcua`）
- 共享 `DATA_SOURCE_BASE_FIELDS`，按类型追加 `connectionConfig` 字段
- OPC UA 额外：`supportsHistory`、`supportsCopyAsNew`，且无轮询间隔字段

## 9. 新增 Tier A 页面检查清单

完整十步 SOP 见 **`docs/PLAN.md` §12.4**。以下为文件级速查：

| # | 文件 | 改动 |
|---|------|------|
| 1 | `schemas/{ledger\|screen\|system}.js` 或 `dataSources.js` | 新增 `resourceDefinitions` 条目 |
| 2 | `schemas/menu.js` | `ADMIN_MENU_GROUPS` 增加 key |
| 3 | `routes/resourcePaths.js` | `ADMIN_RESOURCE_KEYS` 增加 key |
| 4 | `routes/adminRouteRegistry.js` | `PAGE_LOADERS` 增加 lazy import |
| 5 | `pages/*Page.jsx` | `createResourcePage("resourceKey")` |
| 6 | 后端 | REST 与字段命名对齐 |
| 7 | — | `npm run validate:schemas` + `npm run build` |
| 8 | 本文档 | 新 pattern 时补充说明 |

**resourceKey 须四处一致：** menu 叶子、`ADMIN_RESOURCE_KEYS`、`PAGE_LOADERS`、schema 对象键名。

## 10. 校验与类型（M-C2）

### JSDoc 类型

`frontend/src/admin/schemas/schemaTypes.js` 定义 `@typedef`：

- `ResourceDefinition`、`ColumnDefinition`、`FieldDefinition`
- `BulkApplyToolbar`、`BulkToolbarField`
- `ResourceDefinitionMap`

IDE 可在 schema 文件顶部添加 `/** @type {import('./schemaTypes.js').ResourceDefinition} */` 获得补全（可选）。

### 注册表（`schemaRegistry.js`）

| 常量 | 用途 |
|------|------|
| `FORM_FIELD_TYPES` | 表单字段 `type` 白名单 |
| `QUERY_FIELD_TYPES` | 查询栏字段 `type` 白名单 |
| `CELL_FORMATS` | 列 `cellFormat` 白名单 |
| `BULK_FIELD_KINDS` | 多字段批量工具条 `kind` |
| `BULK_INPUT_KINDS` | 如 `booleanSelect` |

新增 field 类型或列格式时：**先扩展注册表 + 引擎实现，再写 schema**。

### 校验规则（`validateResourceDefinitions.js`）

| 检查项 | 说明 |
|--------|------|
| 菜单覆盖 | `ADMIN_MENU_GROUPS` 每个叶子 key 有 definition |
| 默认页 | `DEFAULT_ADMIN_RESOURCE` 存在 |
| 路由对齐 | `validate:schemas` 额外比对 `ADMIN_RESOURCE_KEYS` ↔ 菜单 |
| 基础字段 | `label`、`endpoint`（须 `/api/` 前缀）、非空 `columns` |
| 列 | `key`/`label` 唯一；`cellFormat` 合法；`resourceLinks` 需 `resource` |
| 字段 | `type` 合法；`select` 有 `options`；关联 `resource` 存在 |
| 条件显示 | `visibleWhen.field` / `filterByField` 引用同表字段 |
| 批量工具条 | 单值 / booleanSelect / 多字段三种形态必填项 |

构建时 `index.js` 调用精简版（不含路由键比对）；`npm run validate:schemas` 做完整检查。

## 11. 维护文档索引（M-C3）

| 文档 | 内容 |
|------|------|
| **`docs/ADMIN_SCHEMA.md`**（本文） | 字段字典、类型、示例、校验规则 |
| **`docs/PLAN.md` §12** | Tier 决策流程、新增/修改页 SOP、验收标准 |
| **`docs/STATUS.md` §90** | M-B/M-C 完成状态与团队约定 |
| **`docs/HANDOFF.md`** | 每轮具体变更与冒烟建议 |

### 后续（M-C4+，可选）

- [ ] field type / cellFormat 注册表驱动引擎（M-C4）
- [ ] Vitest 单测包装 `collectResourceDefinitionErrors`（M-C5）
- [ ] 菜单 / 路由 / PAGE_LOADERS 单一注册源（M-C5）

---

*文档版本：M-C3，与 `refactor/admin-antd-styles-split` 分支同步。*
