import { RESERVED_FIELDS } from "./shared.js";
import {
  ACTIVE_STATUS_OPTIONS,
  DATA_SOURCE_BINDING_CATEGORY_OPTIONS,
  REALTIME_LAYOUT_OPTIONS,
  SCREEN_KEY_OPTIONS,
  SCREEN_PAGE_KEY_FLAT_OPTIONS,
} from "./options.js";

export const screenResourceDefinitions = {
  screenConfigs: {
    label: "左右屏配置",
    endpoint: "/api/admin/screen-configs",
    itemLabel: "屏幕配置",
    useModalForm: true,
    modalWidth: 840,
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
    modalFormSections: [
      {
        columns: 2,
        fieldKeys: ["areaId", "screenKey", "title", "subtitle", "rotationIntervalSeconds", "isActive"],
      },
    ],
    columns: [
      { key: "areaName", label: "区域" },
      { key: "screenKey", label: "屏幕", cellFormat: "screenKeyTag" },
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
      { key: "title", label: "标题", type: "text", required: true, defaultValue: "", placeholder: "例如：左屏综合运行展示" },
      { key: "subtitle", label: "副标题", type: "text", defaultValue: "", placeholder: "例如：外部参观综合运行视图" },
      { key: "rotationIntervalSeconds", label: "轮播时长（秒）", type: "integer", required: true, defaultValue: 60 },
      {
        key: "pageOrder",
        label: "轮播子页面顺序",
        type: "screenPageTransfer",
        screenKeyField: "screenKey",
        areaIdField: "areaId",
        defaultValue: [],
      },
      /*
       * 【已隐藏】moduleSettings（模块开关 JSON）
       *
       * 隐藏原因：控制「子页面内部区块」显隐（如 deviceOverview、productionTrend）；
       * 空对象 {} 等价于全部开启，与当前「不做区块级开关」的产品策略一致。
       *
       * 大屏仍会从 ScreenConfig.module_settings 读取该字段；未配置时前端 isModuleEnabled 默认全开。
       * 隐藏仅指后台表单不再暴露 JSON 编辑，不影响现有展示。
       *
       * 后期若需恢复表单编辑：取消下行注释即可。
       * 若需结构化 UI：可新增 moduleSettings 专用表单组件，或恢复「页面模块开关」菜单并接入展示 API。
       *
       * 常用键（左屏）：deviceOverview, productionOverview, productionTrend, energyOverview,
       *   repairPlaceholder, deviceRealtimeMonitor
       * 常用键（右屏）：schedule, delayLegend, simulationPlaceholder
       * 设为 false 隐藏对应区块，示例：{ "repairPlaceholder": false }
       *
       * 参见：frontend/src/ScreenDisplay.jsx（isModuleEnabled）、SCREEN_API.md
       */
      // { key: "moduleSettings", label: "模块开关", type: "json", defaultValue: {} },
      {
        key: "themeSettings",
        label: "主题配置",
        type: "json",
        defaultValue: {},
        collapseByDefault: true,
        collapseHint:
          "预留扩展字段，当前大屏前端尚未读取 themeSettings；一般保持 {} 即可。后期若支持按屏定制主题，在此配置 JSON 并接入 ScreenDisplay。",
        placeholder: "{}",
      },
      { key: "isActive", label: "启用", type: "switch", defaultValue: true },
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
    modalWidth: 840,
    modalFormSections: [
      {
        columns: 2,
        fieldKeys: ["areaId", "screenKey", "pageKey", "bindingSourceType", "isEnabled"],
      },
      {
        columns: 2,
        fieldKeys: ["realtimeLayout", "realtimeDemoMode"],
      },
    ],
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
      {
        key: "dataSourceIds",
        label: "数据源",
        cellFormat: "idCount",
        columnHint: "指定子页面接入的外部数据源，可多选；需先选择数据源类型。",
      },
      { key: "realtimeLayout", label: "实时监控模板", options: REALTIME_LAYOUT_OPTIONS, showWhenPageKey: "realtime" },
      { key: "realtimeDemoMode", label: "使用演示数据", showWhenPageKey: "realtime", width: 128 },
      {
        key: "energyEquipmentIds",
        label: "能耗表计",
        cellFormat: "idCount",
        columnHint: "能耗页展示的电表/设备（platform_equipment）；留空则默认显示进线柜。",
      },
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
        allowBlank: false,
        required: true,
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
        key: "realtimeLayout",
        label: "实时监控模板",
        type: "select",
        defaultValue: "",
        options: REALTIME_LAYOUT_OPTIONS,
        visibleWhen: { field: "pageKey", value: "realtime" },
      },
      {
        key: "realtimeDemoMode",
        label: "使用演示数据（不连接现场设备，全部显示在线演示数据）",
        type: "switch",
        defaultValue: true,
        visibleWhen: { field: "pageKey", value: "realtime" },
      },
      {
        key: "deviceIds",
        label: "监控设备（可选，决定卡片标题）",
        type: "resourceMultiSelectFiltered",
        resource: "devices",
        filterByField: "areaId",
        filterOptionKey: "areaId",
        defaultValue: [],
        visibleWhen: { field: "pageKey", value: "realtime" },
      },
      {
        key: "energyEquipmentIds",
        label: "能耗表计（platform_equipment / p_e_name）",
        type: "energyDatabaseEquipmentMulti",
        dataSourceField: "dataSourceIds",
        defaultValue: [],
        visibleWhen: { field: "pageKey", value: "energy" },
      },
      { key: "isEnabled", label: "启用", type: "switch", defaultValue: true },
      { key: "notes", label: "备注", type: "textarea", defaultValue: "", placeholder: "选填，绑定说明或备注" },
      ...RESERVED_FIELDS,
    ],
  },
  /*
   * 【已隐藏】pageModuleSwitches — 页面模块开关（独立 CRUD）
   * 与 menu.js 中注释说明一致；恢复时取消整块注释，并同步 resourcePaths / adminRouteRegistry。
   *
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
  */
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
      { key: "isActive", label: "启用", type: "switch", defaultValue: true },
      ...RESERVED_FIELDS,
    ],
  },
};
