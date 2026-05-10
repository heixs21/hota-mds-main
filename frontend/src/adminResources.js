export const OMIT_VALUE = Symbol("omit-value");

const RESERVED_FIELDS = [
  { key: "reserved1", label: "预留字段1", type: "text", defaultValue: "", hideInForm: true },
  { key: "reserved2", label: "预留字段2", type: "text", defaultValue: "", hideInForm: true },
  { key: "reserved3", label: "预留字段3", type: "text", defaultValue: "", hideInForm: true },
  { key: "reserved4", label: "预留字段4", type: "text", defaultValue: "", hideInForm: true },
  { key: "reserved5", label: "预留字段5", type: "text", defaultValue: "", hideInForm: true },
];

/** Keys always sent as empty strings on POST/PATCH; not shown in admin form. */
export const RESERVED_FIELD_KEYS = RESERVED_FIELDS.map((field) => field.key);

const DEVICE_STATUS_OPTIONS = [
  { value: "running", label: "运行" },
  { value: "stopped", label: "停机" },
  { value: "alarm", label: "报警" },
  { value: "offline", label: "离线" },
];

const ACTIVE_STATUS_OPTIONS = [
  { value: "true", label: "启用" },
  { value: "false", label: "停用" },
];

const EMPLOYEE_ROLE_OPTIONS = [
  { value: "employee", label: "员工" },
  { value: "team_leader", label: "班组长" },
  { value: "supervisor", label: "主管" },
];

const ORDER_STATUS_OPTIONS = [
  { value: "planned", label: "计划" },
  { value: "in_progress", label: "生产中" },
  { value: "completed", label: "已完成" },
  { value: "cancelled", label: "已取消" },
];

const SCREEN_KEY_OPTIONS = [
  { value: "left", label: "左屏" },
  { value: "right", label: "右屏" },
];

/** 与后端 RuntimeParameterConfig.gantt_anchor_mode 一致 */
const GANTT_ANCHOR_MODE_OPTIONS = [
  { value: "earliest_order", label: "最早未完成工单" },
  { value: "current_time", label: "当前日期" },
];

/** 全部子页面键与中文名（与大屏前端 PAGE_PRESETS 一致），可自由分配到左或右屏 */
export const ALL_PAGE_KEY_OPTIONS = {
  overview: "综合总览",
  operations: "运行与产量",
  energy: "能耗数据",
  realtime: "设备实时监控",
  schedule: "排产总览",
  risk: "风险说明",
  simulation: "仿真预留",
};

/** 供穿梭框使用：两个屏幕都能看到全部页面，用户自行决定顺序 */
export const SCREEN_PAGE_KEY_OPTIONS = {
  left: ALL_PAGE_KEY_OPTIONS,
  right: ALL_PAGE_KEY_OPTIONS,
};

/** 屏幕子页面绑定表单下拉选项 */
export const SCREEN_PAGE_KEY_FLAT_OPTIONS = Object.entries(ALL_PAGE_KEY_OPTIONS).map(
  ([value, label]) => ({ value, label }),
);

/** 子页面绑定：先选接入类型，再在下拉里多选同类型的具体数据源 */
export const DATA_SOURCE_BINDING_CATEGORY_OPTIONS = [
  { value: "", label: "未指定（沿用内置快照）" },
  { value: "opcua", label: "OPC UA" },
  { value: "database", label: "数据库" },
  { value: "modbus_tcp", label: "Modbus TCP" },
  { value: "sap_rfc", label: "SAP RFC" },
  { value: "repair", label: "报修系统" },
];

const ENTITY_TYPE_OPTIONS = [
  { value: "device", label: "设备" },
  { value: "production_line", label: "产线" },
  { value: "area", label: "区域" },
  { value: "order", label: "订单" },
  { value: "material", label: "物料" },
];

const DATA_SOURCE_TYPE_OPTIONS = [
  { value: "opcua", label: "OPC UA" },
  { value: "modbus_tcp", label: "Modbus TCP" },
  { value: "sap_rfc", label: "SAP RFC" },
  { value: "database", label: "数据库" },
  { value: "repair", label: "报修系统" },
];

/**
 * 后台侧栏一级分组与二级资源键（顺序即展示顺序）。
 * `items` 可以是字符串（资源 key）或者 `{ kind: "submenu", id, label, children }` 形式的二级菜单。
 */
export const ADMIN_MENU_GROUPS = [
  {
    id: "basic",
    label: "基础台账",
    items: ["devices", "productionLines", "areas", "employees", "materials", "orders"],
  },
  {
    id: "screen",
    label: "大屏配置",
    items: ["screenPageBindings", "screenConfigs", "pageModuleSwitches", "displayContentConfigs", "runtimeParameterConfigs"],
  },
  {
    id: "system",
    label: "系统设置",
    items: [
      "codeMappings",
      {
        kind: "submenu",
        id: "dataSources",
        label: "数据源配置",
        children: [
          "dataSourceOpcua",
          "dataSourceModbusTcp",
          "dataSourceSapRfc",
          "dataSourceDatabase",
          "dataSourceRepair",
        ],
      },
      "operationLogs",
    ],
  },
];

export const DEFAULT_ADMIN_RESOURCE = "devices";

const DATA_SOURCE_BASE_FIELDS = [
  { key: "code", label: "编码", type: "text", required: true, defaultValue: "" },
  { key: "name", label: "名称", type: "text", required: true, defaultValue: "" },
  { key: "deviceIds", label: "绑定设备", type: "resourceMultiSelect", resource: "devices", allowBlank: true, defaultValue: [] },
  { key: "isEnabled", label: "启用", type: "checkbox", defaultValue: true },
  {
    key: "refreshIntervalSeconds",
    label: "轮询间隔（秒）",
    type: "integer",
    required: true,
    defaultValue: 300,
  },
];

const DATA_SOURCE_BASE_QUERY_FIELDS = [
  { key: "keyword", label: "关键字", type: "text", placeholder: "编码/名称/备注" },
  { key: "is_enabled", label: "启用状态", type: "select", options: ACTIVE_STATUS_OPTIONS },
];

const DATA_SOURCE_BASE_COLUMNS = [
  { key: "code", label: "编码" },
  { key: "name", label: "名称" },
  { key: "boundDevices", label: "绑定设备", cellFormat: "resourceLinks", resource: "devices" },
  { key: "isEnabled", label: "启用" },
  { key: "refreshIntervalSeconds", label: "轮询(s)" },
];

const DATA_SOURCE_TYPE_FIELDS = {
  opcua: [  // OPC UA stays separate — it has its own connection fields & polling logic
    {
      key: "endpointUrl",
      label: "服务器地址 (Endpoint URL)",
      type: "text",
      storage: "connectionConfig",
      placeholder: "opc.tcp://192.168.32.61:4840",
      defaultValue: "",
      required: true,
    },
    {
      key: "node",
      label: "节点ID列表",
      type: "json",
      placeholder:
        "[\n  {\n    \"nodeId\": \"ns=2;s=/Channel/State/chanStatus\",\n    \"comment\": \"机床运行状态\"\n  },\n  {\n    \"nodeId\": \"ns=2;s=/DriveVsa/Drive/r0035\",\n    \"comment\": \"主轴电机温度\"\n  },\n  {\n    \"nodeId\": \"ns=2;s=/Nck/Spindle/driveLoad\",\n    \"comment\": \"主轴负载\"\n  }\n]",
      defaultValue: [],
      required: true,
    },
    {
      key: "username",
      label: "用户名",
      type: "text",
      storage: "connectionConfig",
      placeholder: "OpcUaClient",
      defaultValue: "",
    },
    {
      key: "password",
      label: "密码",
      type: "text",
      storage: "connectionConfig",
      defaultValue: "",
    },
  ],
    database: [
    {
      key: "engine",
      label: "数据库类型",
      type: "select",
      storage: "connectionConfig",
      defaultValue: "mysql",
      required: true,
      options: [
        { value: "mysql", label: "MySQL / MariaDB" },
        { value: "postgresql", label: "PostgreSQL" },
        { value: "sqlserver", label: "SQL Server" },
        { value: "oracle", label: "Oracle" },
      ],
    },
    { key: "host", label: "主机", type: "text", storage: "connectionConfig", defaultValue: "", required: true, placeholder: "127.0.0.1" },
    { key: "port", label: "端口", type: "integer", storage: "connectionConfig", defaultValue: "", placeholder: "3306" },
    { key: "database", label: "数据库名", type: "text", storage: "connectionConfig", defaultValue: "" },
    { key: "username", label: "用户名", type: "text", storage: "connectionConfig", defaultValue: "" },
    { key: "password", label: "密码", type: "text", storage: "connectionConfig", defaultValue: "" },
  ],
  modbus_tcp: [],
  sap_rfc: [],
  repair: [],
};

const DATA_SOURCE_TYPE_LABELS = {
  opcua: "OPC UA",
  modbus_tcp: "Modbus TCP",
  sap_rfc: "SAP RFC",
  database: "数据库",
  repair: "报修系统",
};

/** 列表批量设置轮询间隔：与后端 bulk-refresh-interval + 当前 source_type 筛选一致 */
const DATA_SOURCE_BULK_REFRESH_TOOLBAR = {
  opcua: { inputLabel: "轮询时间（秒）", toastName: "OPC UA" },
  modbus_tcp: { inputLabel: "轮询(s)", toastName: "Modbus TCP" },
  sap_rfc: { inputLabel: "轮询(s)", toastName: "SAP RFC" },
  database: { inputLabel: "轮询(s)", toastName: "数据库" },
  repair: { inputLabel: "轮询(s)", toastName: "报修系统" },
};

function buildDataSourceResources() {
  const result = {};
  for (const sourceType of Object.keys(DATA_SOURCE_TYPE_FIELDS)) {
    const label = DATA_SOURCE_TYPE_LABELS[sourceType];
    const customFields = DATA_SOURCE_TYPE_FIELDS[sourceType];
    const resourceKey = dataSourceResourceKey(sourceType);
    const resource = {
      label,
      itemLabel: `${label} 数据源`,
      endpoint: "/api/admin/data-source-configs",
      useModalForm: true,
      fixedSourceType: sourceType,
      fixedListParams: { source_type: sourceType },
      supportsTestConnection: true,
      supportsHistory: sourceType === "opcua",
      columns: DATA_SOURCE_BASE_COLUMNS,
      queryFields: DATA_SOURCE_BASE_QUERY_FIELDS,
      fields: [
        ...DATA_SOURCE_BASE_FIELDS,
        ...customFields,
        ...RESERVED_FIELDS,
      ],
    };
    const bulkCfg = DATA_SOURCE_BULK_REFRESH_TOOLBAR[sourceType];
    if (bulkCfg) {
      const toastName = bulkCfg.toastName;
      resource.bulkApplyToolbar = {
        apiPath: "bulk-refresh-interval",
        valueKey: "refreshIntervalSeconds",
        label: bulkCfg.inputLabel,
        defaultInput: "300",
        min: 5,
        max: 86400,
        successMessage: (count, seconds) =>
          `已更新 ${count} 条 ${toastName} 数据源的轮询间隔为 ${seconds} 秒。`,
        errorFallback: "批量设置轮询间隔失败，请稍后重试。",
      };
    }
    result[resourceKey] = resource;
  }
  return result;
}

export function dataSourceResourceKey(sourceType) {
  const map = {
    opcua: "dataSourceOpcua",
    modbus_tcp: "dataSourceModbusTcp",
    sap_rfc: "dataSourceSapRfc",
    database: "dataSourceDatabase",
    repair: "dataSourceRepair",
  };
  return map[sourceType] ?? `dataSource_${sourceType}`;
}

export const resourceDefinitions = {
  areas: {
    label: "区域台账",
    endpoint: "/api/admin/areas",
    itemLabel: "区域",
    useModalForm: true,
    columns: [
      { key: "code", label: "编码" },
      { key: "name", label: "名称" },
      { key: "parentName", label: "上级区域" },
      { key: "isActive", label: "启用" },
    ],
    queryFields: [
      { key: "keyword", label: "关键字", type: "text", placeholder: "编码/名称/备注" },
      { key: "is_active", label: "启用状态", type: "select", options: ACTIVE_STATUS_OPTIONS },
      { key: "parent_id", label: "上级区域", type: "resourceSelect", resource: "areas", allowBlank: true },
      { key: "created_at_start", label: "创建开始", type: "date" },
      { key: "created_at_end", label: "创建结束", type: "date" },
    ],
    fields: [
      { key: "code", label: "编码", type: "text", required: true, defaultValue: "" },
      { key: "name", label: "名称", type: "text", required: true, defaultValue: "" },
      { key: "parentId", label: "上级区域", type: "resourceSelect", resource: "areas", allowBlank: true, defaultValue: "" },
      { key: "isActive", label: "启用", type: "checkbox", defaultValue: true },
      { key: "notes", label: "备注", type: "textarea", defaultValue: "" },
      ...RESERVED_FIELDS,
    ],
  },
  productionLines: {
    label: "产线台账",
    endpoint: "/api/admin/production-lines",
    itemLabel: "产线",
    useModalForm: true,
    columns: [
      { key: "code", label: "编码" },
      { key: "name", label: "名称" },
      { key: "areaName", label: "所属区域" },
      { key: "isActive", label: "启用" },
    ],
    queryFields: [
      { key: "keyword", label: "关键字", type: "text", placeholder: "编码/名称/区域/备注" },
      { key: "is_active", label: "启用状态", type: "select", options: ACTIVE_STATUS_OPTIONS },
      { key: "area_id", label: "所属区域", type: "resourceSelect", resource: "areas", allowBlank: true },
      { key: "created_at_start", label: "创建开始", type: "date" },
      { key: "created_at_end", label: "创建结束", type: "date" },
    ],
    fields: [
      { key: "code", label: "编码", type: "text", required: true, defaultValue: "" },
      { key: "name", label: "名称", type: "text", required: true, defaultValue: "" },
      { key: "areaId", label: "所属区域", type: "resourceSelect", resource: "areas", allowBlank: true, defaultValue: "" },
      { key: "isActive", label: "启用", type: "checkbox", defaultValue: true },
      { key: "notes", label: "备注", type: "textarea", defaultValue: "" },
      ...RESERVED_FIELDS,
    ],
  },
  devices: {
    label: "设备台账",
    endpoint: "/api/admin/devices",
    itemLabel: "设备",
    useModalForm: true,
    columns: [
      { key: "code", label: "编码" },
      { key: "name", label: "名称" },
      { key: "ip", label: "IP" },
      { key: "areaName", label: "区域" },
      { key: "productionLineName", label: "产线" },
      { key: "defaultStatus", label: "状态", options: DEVICE_STATUS_OPTIONS },
    ],
    queryFields: [
      { key: "keyword", label: "关键字", type: "text", placeholder: "编码/名称/IP/区域/产线" },
      { key: "default_status", label: "状态", type: "select", options: DEVICE_STATUS_OPTIONS },
      { key: "is_active", label: "启用状态", type: "select", options: ACTIVE_STATUS_OPTIONS },
      { key: "area_id", label: "区域", type: "resourceSelect", resource: "areas", allowBlank: true },
      { key: "production_line_id", label: "产线", type: "resourceSelect", resource: "productionLines", allowBlank: true },
      { key: "created_at_start", label: "创建开始", type: "date" },
      { key: "created_at_end", label: "创建结束", type: "date" },
    ],
    fields: [
      { key: "code", label: "编码", type: "text", required: true, defaultValue: "" },
      { key: "name", label: "名称", type: "text", required: true, defaultValue: "" },
      { key: "ip", label: "设备IP", type: "text", defaultValue: "" },
      { key: "areaId", label: "所属区域", type: "resourceSelect", resource: "areas", allowBlank: true, defaultValue: "" },
      { key: "productionLineId", label: "所属产线", type: "resourceSelect", resource: "productionLines", allowBlank: true, defaultValue: "" },
      {
        key: "defaultStatus",
        label: "状态",
        type: "select",
        required: true,
        defaultValue: "stopped",
        options: DEVICE_STATUS_OPTIONS,
      },
      { key: "isActive", label: "启用", type: "checkbox", defaultValue: true },
      { key: "notes", label: "备注", type: "textarea", defaultValue: "" },
      ...RESERVED_FIELDS,
    ],
  },
  employees: {
    label: "员工台账",
    endpoint: "/api/admin/employees",
    itemLabel: "员工",
    useModalForm: true,
    columns: [
      { key: "employeeNo", label: "员工号" },
      { key: "name", label: "姓名" },
      { key: "roleLabel", label: "角色" },
      { key: "isActive", label: "启用" },
    ],
    queryFields: [
      { key: "keyword", label: "关键字", type: "text", placeholder: "工号/姓名/备注" },
      { key: "role", label: "角色", type: "select", options: EMPLOYEE_ROLE_OPTIONS },
      { key: "is_active", label: "启用状态", type: "select", options: ACTIVE_STATUS_OPTIONS },
      { key: "created_at_start", label: "创建开始", type: "date" },
      { key: "created_at_end", label: "创建结束", type: "date" },
    ],
    fields: [
      { key: "employeeNo", label: "员工号", type: "text", required: true, defaultValue: "" },
      { key: "name", label: "姓名", type: "text", required: true, defaultValue: "" },
      {
        key: "role",
        label: "角色",
        type: "select",
        required: true,
        defaultValue: "employee",
        options: EMPLOYEE_ROLE_OPTIONS,
      },
      { key: "isActive", label: "启用", type: "checkbox", defaultValue: true },
      { key: "notes", label: "备注", type: "textarea", defaultValue: "" },
      ...RESERVED_FIELDS,
    ],
  },
  materials: {
    label: "物料台账",
    endpoint: "/api/admin/materials",
    itemLabel: "物料",
    useModalForm: true,
    columns: [
      { key: "code", label: "编码" },
      { key: "name", label: "名称" },
      { key: "specification", label: "规格" },
      { key: "unit", label: "单位" },
      { key: "isActive", label: "启用" },
    ],
    queryFields: [
      { key: "keyword", label: "关键字", type: "text", placeholder: "编码/名称/规格/备注" },
      { key: "is_active", label: "启用状态", type: "select", options: ACTIVE_STATUS_OPTIONS },
      { key: "created_at_start", label: "创建开始", type: "date" },
      { key: "created_at_end", label: "创建结束", type: "date" },
    ],
    fields: [
      { key: "code", label: "编码", type: "text", required: true, defaultValue: "" },
      { key: "name", label: "名称", type: "text", required: true, defaultValue: "" },
      { key: "specification", label: "规格", type: "text", defaultValue: "" },
      { key: "unit", label: "单位", type: "text", defaultValue: "" },
      { key: "isActive", label: "启用", type: "checkbox", defaultValue: true },
      { key: "notes", label: "备注", type: "textarea", defaultValue: "" },
      ...RESERVED_FIELDS,
    ],
  },
  orders: {
    label: "订单台账",
    endpoint: "/api/admin/orders",
    itemLabel: "订单",
    useModalForm: true,
    columns: [
      { key: "orderNo", label: "订单号" },
      { key: "materialName", label: "物料" },
      { key: "productionLineName", label: "产线" },
      { key: "quantity", label: "计划数量" },
      { key: "completedQuantity", label: "完成数量" },
      { key: "statusLabel", label: "状态" },
    ],
    queryFields: [
      { key: "keyword", label: "关键字", type: "text", placeholder: "订单号/物料/产线/备注" },
      { key: "status", label: "状态", type: "select", options: ORDER_STATUS_OPTIONS },
      { key: "is_active", label: "启用状态", type: "select", options: ACTIVE_STATUS_OPTIONS },
      { key: "material_id", label: "物料", type: "resourceSelect", resource: "materials", allowBlank: true },
      { key: "production_line_id", label: "产线", type: "resourceSelect", resource: "productionLines", allowBlank: true },
      { key: "created_at_start", label: "创建开始", type: "date" },
      { key: "created_at_end", label: "创建结束", type: "date" },
    ],
    fields: [
      { key: "orderNo", label: "订单号", type: "text", required: true, defaultValue: "" },
      { key: "materialId", label: "物料", type: "resourceSelect", resource: "materials", allowBlank: true, defaultValue: "" },
      { key: "productionLineId", label: "产线", type: "resourceSelect", resource: "productionLines", allowBlank: true, defaultValue: "" },
      { key: "quantity", label: "计划数量", type: "decimal", required: true, defaultValue: "0.00" },
      { key: "completedQuantity", label: "完成数量", type: "decimal", defaultValue: "0.00" },
      { key: "unit", label: "单位", type: "text", defaultValue: "" },
      {
        key: "status",
        label: "状态",
        type: "select",
        required: true,
        defaultValue: "planned",
        options: ORDER_STATUS_OPTIONS,
      },
      { key: "plannedStart", label: "计划开始", type: "text", defaultValue: "", placeholder: "YYYY-MM-DD HH:MM:SS" },
      { key: "plannedEnd", label: "计划结束", type: "text", defaultValue: "", placeholder: "YYYY-MM-DD HH:MM:SS" },
      { key: "actualStart", label: "实际开始", type: "text", defaultValue: "", placeholder: "YYYY-MM-DD HH:MM:SS" },
      { key: "actualEnd", label: "实际结束", type: "text", defaultValue: "", placeholder: "YYYY-MM-DD HH:MM:SS" },
      { key: "isActive", label: "启用", type: "checkbox", defaultValue: true },
      { key: "notes", label: "备注", type: "textarea", defaultValue: "" },
      ...RESERVED_FIELDS,
    ],
  },
  codeMappings: {
    label: "编码映射",
    endpoint: "/api/admin/code-mappings",
    itemLabel: "编码映射",
    useModalForm: true,
    columns: [
      { key: "entityType", label: "对象类型" },
      { key: "sourceSystem", label: "来源系统" },
      { key: "internalCode", label: "内部编码" },
      { key: "externalCode", label: "外部编码" },
    ],
    queryFields: [
      { key: "keyword", label: "关键字", type: "text", placeholder: "来源系统/内外编码/备注" },
      { key: "entity_type", label: "对象类型", type: "select", options: ENTITY_TYPE_OPTIONS },
      { key: "is_active", label: "启用状态", type: "select", options: ACTIVE_STATUS_OPTIONS },
      { key: "created_at_start", label: "创建开始", type: "date" },
      { key: "created_at_end", label: "创建结束", type: "date" },
    ],
    fields: [
      {
        key: "entityType",
        label: "对象类型",
        type: "select",
        required: true,
        defaultValue: "device",
        options: ENTITY_TYPE_OPTIONS,
      },
      { key: "sourceSystem", label: "来源系统", type: "text", required: true, defaultValue: "" },
      { key: "internalCode", label: "内部编码", type: "text", required: true, defaultValue: "" },
      { key: "externalCode", label: "外部编码", type: "text", required: true, defaultValue: "" },
      { key: "isActive", label: "启用", type: "checkbox", defaultValue: true },
      { key: "notes", label: "备注", type: "textarea", defaultValue: "" },
      ...RESERVED_FIELDS,
    ],
  },
  screenConfigs: {
    label: "左右屏配置",
    endpoint: "/api/admin/screen-configs",
    itemLabel: "屏幕配置",
    useModalForm: true,
    wideModal: true,
    bulkApplyToolbar: {
      apiPath: "bulk-rotation-interval",
      valueKey: "rotationIntervalSeconds",
      label: "轮播时长（秒）",
      defaultInput: "60",
      min: 5,
      max: 86400,
      successMessage: (count, seconds) => `已更新 ${count} 条屏幕配置的轮播时长为 ${seconds} 秒。`,
      errorFallback: "批量设置轮播时长失败，请稍后重试。",
    },
    relatedResources: ["screenPageBindings"],
    columns: [
      { key: "areaName", label: "区域" },
      { key: "screenKey", label: "屏幕" },
      { key: "title", label: "标题" },
      { key: "rotationIntervalSeconds", label: "轮播时长（秒）" },
      { key: "isActive", label: "启用" },
    ],
    queryFields: [
      { key: "keyword", label: "关键字", type: "text", placeholder: "屏幕键/标题/副标题" },
      { key: "area_id", label: "区域", type: "resourceSelect", resource: "areas", allowBlank: true },
      { key: "screen_key", label: "屏幕", type: "select", options: SCREEN_KEY_OPTIONS },
      { key: "is_active", label: "启用状态", type: "select", options: ACTIVE_STATUS_OPTIONS },
    ],
    fields: [
      { key: "areaId", label: "区域", type: "resourceSelect", resource: "areas", allowBlank: false, defaultValue: "" },
      {
        key: "screenKey",
        label: "屏幕",
        type: "select",
        required: true,
        defaultValue: "left",
        options: SCREEN_KEY_OPTIONS,
      },
      { key: "title", label: "标题", type: "text", required: true, defaultValue: "" },
      { key: "subtitle", label: "副标题", type: "text", defaultValue: "" },
      { key: "rotationIntervalSeconds", label: "轮播时长（秒）", type: "integer", required: true, defaultValue: 60 },
      {
        key: "pageOrder",
        label: "轮播子页面顺序",
        type: "screenPageTransfer",
        screenKeyField: "screenKey",
        defaultValue: [],
      },
      { key: "moduleSettings", label: "模块开关", type: "json", defaultValue: {} },
      { key: "themeSettings", label: "主题配置", type: "json", defaultValue: {} },
      { key: "isActive", label: "启用", type: "checkbox", defaultValue: true },
      ...RESERVED_FIELDS,
    ],
  },
  dataSourceConfigs: {
    label: "数据源列表",
    endpoint: "/api/admin/data-source-configs",
    itemLabel: "数据源",
    useModalForm: true,
    columns: [
      { key: "code", label: "编码" },
      { key: "name", label: "名称" },
      { key: "sourceType", label: "类型" },
    ],
    queryFields: [],
    fields: [
      { key: "code", label: "编码", type: "text", required: true, defaultValue: "" },
      { key: "name", label: "名称", type: "text", required: true, defaultValue: "" },
      ...RESERVED_FIELDS,
    ],
  },
  screenPageBindings: {
    label: "屏幕子页面",
    endpoint: "/api/admin/screen-page-bindings",
    itemLabel: "子页面",
    useModalForm: true,
    bulkApplyToolbar: {
      apiPath: "bulk-set-enabled",
      inputKind: "booleanSelect",
      valueKey: "isEnabled",
      label: "启用",
      defaultInput: "true",
      selectOptions: [
        { value: "true", label: "启用" },
        { value: "false", label: "停用" },
      ],
      successMessage: (count, enabled) =>
        `已批量更新 ${count} 条子页面绑定为「${enabled ? "启用" : "停用"}」。`,
      errorFallback: "批量设置启用状态失败，请稍后重试。",
    },
    columns: [
      { key: "bindingScopeLabel", label: "屏幕（区域）" },
      { key: "pageKeyLabel", label: "子页面" },
      { key: "bindingSourceType", label: "数据源类型", options: DATA_SOURCE_BINDING_CATEGORY_OPTIONS },
      { key: "dataSourceIds", label: "数据源", cellFormat: "idCount" },
      { key: "energyEquipmentIds", label: "能耗表计", cellFormat: "idCount" },
      { key: "isEnabled", label: "启用" },
    ],
    queryFields: [
      { key: "area_id", label: "区域", type: "resourceSelect", resource: "areas", allowBlank: true },
      { key: "screen_key", label: "屏幕", type: "select", options: SCREEN_KEY_OPTIONS },
      { key: "is_enabled", label: "启用状态", type: "select", options: ACTIVE_STATUS_OPTIONS },
    ],
    fields: [
      {
        key: "areaId",
        label: "所属区域",
        type: "resourceSelect",
        resource: "areas",
        allowBlank: true,
        defaultValue: "",
      },
      {
        key: "pageKey",
        label: "子页面",
        type: "select",
        required: true,
        defaultValue: "overview",
        options: SCREEN_PAGE_KEY_FLAT_OPTIONS,
      },
      {
        key: "screenKey",
        label: "左/右屏",
        type: "select",
        required: true,
        defaultValue: "left",
        options: SCREEN_KEY_OPTIONS,
      },
      {
        key: "bindingSourceType",
        label: "数据源类型",
        type: "select",
        defaultValue: "",
        options: DATA_SOURCE_BINDING_CATEGORY_OPTIONS,
      },
      {
        key: "dataSourceIds",
        label: "数据源（按类型筛选，可多选）",
        type: "resourceMultiSelectFiltered",
        resource: "dataSourceConfigs",
        filterByField: "bindingSourceType",
        filterOptionKey: "sourceType",
        defaultValue: [],
      },
      {
        key: "energyEquipmentIds",
        label: "能耗表计（platform_equipment / p_e_name）",
        type: "energyDatabaseEquipmentMulti",
        dataSourceField: "dataSourceIds",
        defaultValue: [],
        visibleWhen: { field: "pageKey", value: "energy" },
      },
      { key: "isEnabled", label: "启用", type: "checkbox", defaultValue: true },
      { key: "notes", label: "备注", type: "textarea", defaultValue: "" },
      ...RESERVED_FIELDS,
    ],
  },
  pageModuleSwitches: {
    label: "页面模块开关",
    endpoint: "/api/admin/page-module-switches",
    itemLabel: "模块开关",
    useModalForm: true,
    columns: [
      { key: "screenKey", label: "屏幕", options: SCREEN_KEY_OPTIONS },
      { key: "moduleKey", label: "模块标识" },
      { key: "label", label: "模块名称" },
      { key: "sortOrder", label: "排序" },
      { key: "isEnabled", label: "启用" },
    ],
    queryFields: [
      { key: "keyword", label: "关键字", type: "text", placeholder: "模块标识/名称/备注" },
      { key: "screen_key", label: "屏幕", type: "select", options: SCREEN_KEY_OPTIONS },
      { key: "is_enabled", label: "启用状态", type: "select", options: ACTIVE_STATUS_OPTIONS },
    ],
    fields: [
      {
        key: "screenKey",
        label: "屏幕",
        type: "select",
        required: true,
        defaultValue: "left",
        options: SCREEN_KEY_OPTIONS,
      },
      { key: "moduleKey", label: "模块标识", type: "text", required: true, defaultValue: "" },
      { key: "label", label: "模块名称", type: "text", required: true, defaultValue: "" },
      { key: "isEnabled", label: "启用", type: "checkbox", defaultValue: true },
      { key: "sortOrder", label: "排序", type: "integer", required: true, defaultValue: 0 },
      { key: "notes", label: "备注", type: "textarea", defaultValue: "" },
      ...RESERVED_FIELDS,
    ],
  },
  displayContentConfigs: {
    label: "欢迎展示配置",
    endpoint: "/api/admin/display-content-configs",
    itemLabel: "展示内容配置",
    useModalForm: true,
    columns: [
      { key: "configKey", label: "配置键" },
      { key: "companyName", label: "公司名称" },
      { key: "welcomeMessage", label: "欢迎语" },
      { key: "isActive", label: "启用" },
    ],
    queryFields: [
      { key: "keyword", label: "关键字", type: "text", placeholder: "配置键/公司名/欢迎语" },
      { key: "is_active", label: "启用状态", type: "select", options: ACTIVE_STATUS_OPTIONS },
      { key: "created_at_start", label: "创建开始", type: "date" },
      { key: "created_at_end", label: "创建结束", type: "date" },
    ],
    fields: [
      { key: "configKey", label: "配置键", type: "text", required: true, defaultValue: "default" },
      { key: "companyName", label: "公司名称", type: "text", required: true, defaultValue: "" },
      { key: "welcomeMessage", label: "欢迎语", type: "text", required: true, defaultValue: "" },
      { key: "logoUrl", label: "Logo 地址", type: "text", defaultValue: "" },
      { key: "promoImageUrls", label: "宣传图片地址列表", type: "json", defaultValue: [] },
      { key: "isActive", label: "启用", type: "checkbox", defaultValue: true },
      ...RESERVED_FIELDS,
    ],
  },
  runtimeParameterConfigs: {
    label: "运行参数配置",
    endpoint: "/api/admin/runtime-parameter-configs",
    itemLabel: "运行参数",
    useModalForm: true,
    bulkApplyToolbar: {
      apiPath: "bulk-runtime-fields",
      fields: [
        {
          key: "singleDayEffectiveWorkHours",
          label: "日有效工时",
          kind: "decimal",
          defaultInput: "16.00",
          min: 0.01,
          max: 24,
          step: "0.01",
        },
        {
          key: "ganttWindowDays",
          label: "甘特窗口天数",
          kind: "integer",
          defaultInput: "30",
          min: 1,
          max: 36500,
          step: "1",
        },
      ],
      successMessage: (count) => `已批量更新 ${count} 条运行参数配置的日有效工时与甘特窗口天数。`,
      errorFallback: "批量设置失败，请稍后重试。",
    },
    columns: [
      { key: "configKey", label: "配置键" },
      { key: "singleDayEffectiveWorkHours", label: "日有效工时" },
      { key: "defaultStandardCapacityPerHour", label: "标准产能/小时" },
      { key: "ganttWindowDays", label: "甘特窗口天数" },
      { key: "ganttAnchorMode", label: "甘特图开始时间" },
    ],
    queryFields: [
      { key: "keyword", label: "关键字", type: "text", placeholder: "配置键/备注" },
      { key: "is_active", label: "启用状态", type: "select", options: ACTIVE_STATUS_OPTIONS },
    ],
    fields: [
      { key: "configKey", label: "配置键", type: "text", required: true, defaultValue: "default" },
      { key: "singleDayEffectiveWorkHours", label: "单日有效工作时长", type: "decimal", required: true, defaultValue: "16.00" },
      { key: "defaultStandardCapacityPerHour", label: "默认标准产能/小时", type: "decimal", required: true, defaultValue: "0.00" },
      { key: "delayWarningBufferHours", label: "延期预警缓冲小时", type: "decimal", required: true, defaultValue: "0.00" },
      { key: "ganttWindowDays", label: "甘特窗口天数", type: "integer", required: true, defaultValue: 30 },
      {
        key: "ganttAnchorMode",
        label: "甘特图开始时间",
        type: "select",
        options: GANTT_ANCHOR_MODE_OPTIONS,
        defaultValue: "earliest_order",
      },
      { key: "autoScrollEnabled", label: "启用自动滚动", type: "checkbox", defaultValue: true },
      { key: "autoScrollRowsThreshold", label: "自动滚动行数阈值", type: "integer", required: true, defaultValue: 10 },
      { key: "recentCapacityWindowHours", label: "最近产能窗口小时", type: "integer", required: true, defaultValue: 2 },
      { key: "productionTrendWindowHours", label: "产量趋势窗口小时", type: "integer", required: true, defaultValue: 8 },
      { key: "notes", label: "备注", type: "textarea", defaultValue: "" },
      { key: "isActive", label: "启用", type: "checkbox", defaultValue: true },
      ...RESERVED_FIELDS,
    ],
  },
  ...buildDataSourceResources(),
  operationLogs: {
    label: "操作日志",
    endpoint: "/api/admin/operation-logs",
    itemLabel: "日志",
    readOnly: true,
    columns: [
      { key: "createdAt", label: "时间", cellFormat: "cstDateTime" },
      { key: "actorUsername", label: "管理员" },
      { key: "action", label: "动作" },
      { key: "targetType", label: "对象类型" },
      { key: "targetLabel", label: "对象" },
    ],
    fields: [],
  },
};


export function stringifyJson(value) {
  return JSON.stringify(value, null, 2);
}


export function createEmptyForm(resourceDefinition) {
  const nextState = {};
  for (const field of resourceDefinition.fields) {
    if (field.type === "staticHint") {
      continue;
    }
    if (field.type === "json" || field.type === "screenPageTransfer") {
      const rawDefault = field.defaultValue ?? {};
      nextState[field.key] = Object.keys(rawDefault).length === 0 && field.omitIfBlank ? "" : stringifyJson(rawDefault);
    } else if (field.type === "checkbox") {
      nextState[field.key] = Boolean(field.defaultValue);
    } else if (
      field.type === "resourceMultiSelect" ||
      field.type === "resourceMultiSelectFiltered" ||
      field.type === "energyDatabaseEquipmentMulti"
    ) {
      nextState[field.key] = Array.isArray(field.defaultValue) ? [...field.defaultValue] : [];
    } else {
      nextState[field.key] = field.defaultValue ?? "";
    }
  }
  return nextState;
}


function readNestedValue(item, storageKey, fieldKey) {
  const container = item?.[storageKey];
  if (container === null || container === undefined) {
    return undefined;
  }
  if (typeof container !== "object") {
    return undefined;
  }
  return container[fieldKey];
}


export function createEmptyQuery(resourceDefinition) {
  const nextState = {};
  for (const field of resourceDefinition.queryFields ?? []) {
    nextState[field.key] = "";
  }
  return nextState;
}


export function createFormFromItem(resourceDefinition, item) {
  const nextState = {};
  for (const field of resourceDefinition.fields) {
    if (field.type === "staticHint") {
      continue;
    }
    const rawValue = field.storage
      ? readNestedValue(item, field.storage, field.key)
      : item?.[field.key];
    if (field.type === "json" || field.type === "screenPageTransfer") {
      if (rawValue === undefined && field.omitIfBlank) {
        nextState[field.key] = "";
      } else {
        nextState[field.key] = stringifyJson(rawValue ?? field.defaultValue ?? {});
      }
    } else if (field.type === "checkbox") {
      nextState[field.key] = Boolean(rawValue);
    } else if (field.type === "energyDatabaseEquipmentMulti") {
      if (Array.isArray(rawValue)) {
        nextState[field.key] = rawValue.map((v) => String(v)).filter(Boolean);
      } else {
        nextState[field.key] = [];
      }
    } else if (field.type === "resourceMultiSelect" || field.type === "resourceMultiSelectFiltered") {
      if (Array.isArray(rawValue)) {
        nextState[field.key] = rawValue
          .map((v) => Number(v))
          .filter((n) => Number.isInteger(n) && n > 0);
      } else {
        nextState[field.key] = Array.isArray(field.defaultValue) ? [...field.defaultValue] : [];
      }
    } else if (rawValue === null || rawValue === undefined) {
      nextState[field.key] = field.defaultValue ?? "";
    } else {
      nextState[field.key] = rawValue;
    }
  }
  return nextState;
}


/**
 * @param {object} [fullForm]  全表状态；`screenPageTransfer` 需用其 `screenKey` 与备选项对齐
 */
export function parseFieldValue(field, rawValue, fullForm) {
  if (field.type === "staticHint") {
    return OMIT_VALUE;
  }
  if (field.type === "checkbox") {
    return Boolean(rawValue);
  }
  if (field.type === "integer") {
    return rawValue === "" ? null : Number.parseInt(rawValue, 10);
  }
  if (field.type === "decimal") {
    return rawValue === "" ? null : String(rawValue);
  }
  if (field.type === "resourceSelect") {
    return rawValue === "" ? null : Number(rawValue);
  }
  if (field.type === "energyDatabaseEquipmentMulti") {
    if (!Array.isArray(rawValue)) {
      return [];
    }
    return rawValue.map((value) => String(value)).filter(Boolean);
  }
  if (field.type === "resourceMultiSelect" || field.type === "resourceMultiSelectFiltered") {
    if (!Array.isArray(rawValue)) {
      return [];
    }
    return rawValue
      .map((value) => Number(value))
      .filter((value) => Number.isInteger(value) && value > 0);
  }
  if (field.type === "json" || field.type === "screenPageTransfer") {
    if (rawValue === "" && field.omitIfBlank) {
      return OMIT_VALUE;
    }
    if (rawValue === "") {
      if (field.type === "screenPageTransfer") {
        return Array.isArray(field.defaultValue) ? field.defaultValue : [];
      }
      return field.defaultValue ?? {};
    }
    const parsed = JSON.parse(rawValue);
    if (field.type === "screenPageTransfer") {
      if (!Array.isArray(parsed)) {
        return Array.isArray(field.defaultValue) ? field.defaultValue : [];
      }
      const keys = parsed.filter((k) => typeof k === "string");
      if (fullForm) {
        const sk = fullForm[field.screenKeyField ?? "screenKey"] || "left";
        const valid = Object.keys(SCREEN_PAGE_KEY_OPTIONS[sk] || {});
        const filtered = keys.filter((k) => valid.includes(k));
        if (filtered.length > 0) {
          return filtered;
        }
        return sk === "right" ? ["schedule"] : ["overview"];
      }
      return keys;
    }
    return parsed;
  }
  return rawValue;
}


function formatCstDateTime(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).formatToParts(date);
  const map = {};
  for (const { type, value: partValue } of parts) {
    if (type !== "literal") {
      map[type] = partValue;
    }
  }
  return `${map.year}-${map.month}-${map.day} ${map.hour}:${map.minute}:${map.second}`;
}


export function formatCellValue(value, column) {
  if (column?.cellFormat === "cstDateTime") {
    return formatCstDateTime(value);
  }
  if (Array.isArray(value) && column?.cellFormat === "idCount") {
    return value.length ? `${value.length} 项` : "-";
  }
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (Array.isArray(column?.options)) {
    const hit = column.options.find((opt) => opt.value === value);
    if (hit) {
      return hit.label;
    }
  }
  if (typeof value === "boolean") {
    return value ? "是" : "否";
  }
  if (typeof value === "object") {
    if (column?.cellFormat === "resourceLinks" && Array.isArray(value)) {
      return value.map((item) => item?.name || item?.code || item?.id).filter(Boolean).join(" / ") || "-";
    }
    if (value.storageType) {
      return `${value.storageType}${value.hasEncryptedSecret ? " / 已有密文" : ""}`;
    }
    return stringifyJson(value);
  }
  return String(value);
}
