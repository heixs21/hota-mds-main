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
          "dataSourceS7",
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
