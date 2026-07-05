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

/** 列表 Tag 展示：左/右屏文案与颜色 */
const SCREEN_KEY_TAG_MAP = {
  left: { label: "左屏", color: "blue" },
  right: { label: "右屏", color: "orange" },
};

const REALTIME_LAYOUT_OPTIONS = [
  { value: "", label: "自动识别" },
  { value: "siemens_boring", label: "西门子镗孔" },
  { value: "syntec_cnc", label: "新代 CNC" },
  { value: "parameter_grid", label: "参数列表" },
  { value: "xiaozhou_line", label: "销轴产线布局" },
  { value: "taotong_gunzi_line", label: "套筒滚子产线布局" },
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
  { value: "s7", label: "S7 PLC" },
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

export const DATA_SOURCE_TYPE_OPTIONS = [
  { value: "opcua", label: "OPC UA" },
  { value: "modbus_tcp", label: "Modbus TCP" },
  { value: "s7", label: "S7 PLC" },
  { value: "sap_rfc", label: "SAP RFC" },
  { value: "database", label: "数据库" },
  { value: "repair", label: "报修系统" },
];

export {
  ACTIVE_STATUS_OPTIONS,
  DEVICE_STATUS_OPTIONS,
  EMPLOYEE_ROLE_OPTIONS,
  ENTITY_TYPE_OPTIONS,
  GANTT_ANCHOR_MODE_OPTIONS,
  ORDER_STATUS_OPTIONS,
  REALTIME_LAYOUT_OPTIONS,
  SCREEN_KEY_OPTIONS,
  SCREEN_KEY_TAG_MAP,
};
