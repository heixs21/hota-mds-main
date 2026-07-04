import { RESERVED_FIELDS } from "./shared.js";
import { ACTIVE_STATUS_OPTIONS } from "./options.js";

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

export const DATA_SOURCE_BASE_QUERY_FIELDS = [
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
  opcua: [  // OPC UA：长连接订阅 + 节点 subscribe 标记；无轮询间隔字段
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
        "[\n  {\n    \"nodeId\": \"ns=2;s=/Channel/State/chanStatus\",\n    \"comment\": \"机床运行状态\"\n  },\n  {\n    \"nodeId\": \"ns=2;s=/Nck/Configuration/nckVersion\",\n    \"comment\": \"CNC型号\",\n    \"subscribe\": false\n  },\n  {\n    \"nodeId\": \"ns=2;s=/Nck/Spindle/driveLoad\",\n    \"comment\": \"主轴负载\"\n  }\n]",
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
  s7: [
    {
      key: "host",
      label: "PLC 主机",
      type: "text",
      storage: "connectionConfig",
      placeholder: "192.168.31.2",
      defaultValue: "",
      required: true,
    },
    {
      key: "rack",
      label: "机架 (Rack)",
      type: "integer",
      storage: "connectionConfig",
      defaultValue: 0,
      required: true,
    },
    {
      key: "slot",
      label: "槽位 (Slot)",
      type: "integer",
      storage: "connectionConfig",
      defaultValue: 1,
      required: true,
    },
    {
      key: "node",
      label: "DB 点位列表",
      type: "json",
      placeholder:
        "[\n  {\n    \"dbNumber\": 79,\n    \"offset\": 0,\n    \"bit\": 0,\n    \"dataType\": \"bool\",\n    \"comment\": \"4线运行\"\n  },\n  {\n    \"dbNumber\": 79,\n    \"offset\": 2,\n    \"dataType\": \"int\",\n    \"comment\": \"4线东北筐生产计数\"\n  },\n  {\n    \"dbNumber\": 79,\n    \"offset\": 6,\n    \"length\": 10,\n    \"dataType\": \"string\",\n    \"comment\": \"4线物料编码\"\n  }\n]",
      defaultValue: [],
      required: true,
    },
  ],
  sap_rfc: [],
  repair: [],
};

const DATA_SOURCE_TYPE_LABELS = {
  opcua: "OPC UA",
  modbus_tcp: "Modbus TCP",
  s7: "S7 PLC",
  sap_rfc: "SAP RFC",
  database: "数据库",
  repair: "报修系统",
};

/** 列表批量设置轮询间隔：与后端 bulk-refresh-interval + 当前 source_type 筛选一致 */
const DATA_SOURCE_BULK_REFRESH_TOOLBAR = {
  modbus_tcp: { inputLabel: "轮询(s)", toastName: "Modbus TCP" },
  s7: { inputLabel: "轮询(s)", toastName: "S7 PLC" },
  sap_rfc: { inputLabel: "轮询(s)", toastName: "SAP RFC" },
  database: { inputLabel: "轮询(s)", toastName: "数据库" },
  repair: { inputLabel: "轮询(s)", toastName: "报修系统" },
};

export function buildDataSourceResources() {
  const result = {};
  for (const sourceType of Object.keys(DATA_SOURCE_TYPE_FIELDS)) {
    const label = DATA_SOURCE_TYPE_LABELS[sourceType];
    const customFields = DATA_SOURCE_TYPE_FIELDS[sourceType];
    const resourceKey = dataSourceResourceKey(sourceType);
    const isOpcUa = sourceType === "opcua";
    const baseFields = isOpcUa
      ? DATA_SOURCE_BASE_FIELDS.filter((f) => f.key !== "refreshIntervalSeconds")
      : DATA_SOURCE_BASE_FIELDS;
    const columns = isOpcUa
      ? DATA_SOURCE_BASE_COLUMNS.filter((c) => c.key !== "refreshIntervalSeconds")
      : DATA_SOURCE_BASE_COLUMNS;
    const resource = {
      label,
      itemLabel: `${label} 数据源`,
      endpoint: "/api/admin/data-source-configs",
      useModalForm: true,
      fixedSourceType: sourceType,
      fixedListParams: { source_type: sourceType },
      supportsTestConnection: true,
      supportsHistory: sourceType === "opcua",
      supportsCopyAsNew: sourceType === "opcua",
      columns,
      queryFields: DATA_SOURCE_BASE_QUERY_FIELDS,
      fields: [
        ...baseFields,
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
    s7: "dataSourceS7",
    sap_rfc: "dataSourceSapRfc",
    database: "dataSourceDatabase",
    repair: "dataSourceRepair",
  };
  return map[sourceType] ?? `dataSource_${sourceType}`;
}
