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
    items: [
      "screenPageBindings",
      "screenConfigs",
      /*
       * 【已隐藏】页面模块开关（pageModuleSwitches）
       *
       * 隐藏原因：
       * - 该菜单对应表 backoffice_pagemoduleswitch，展示 API 尚未读取此表；
       * - 与「左右屏配置 → moduleSettings」职能重复，且后者才是当前大屏实际生效的配置；
       * - 现阶段无「子页面内区块显隐」运营需求。
       *
       * 后期若需要区块级开关，推荐恢复顺序：
       * 1. 取消本行及下方各文件中同类注释；
       * 2. 在 backend/backoffice/display_services.py 的 _get_screen_config 中，
       *    将 PageModuleSwitch 表聚合为 moduleSettings 对象（按 screen_key，可选按 area）；
       * 3. 确认 frontend/src/ScreenDisplay.jsx 中 isModuleEnabled / resolveVisibleSections 的键名与后台一致；
       * 4. 二选一：仅用 PageModuleSwitch 表，或仅用 moduleSettings JSON，避免双轨。
       *
       * 相关文件：
       * - frontend/src/admin/schemas/screen.js（pageModuleSwitches 资源定义、moduleSettings 字段）
       * - frontend/src/admin/routes/resourcePaths.js（ADMIN_RESOURCE_KEYS）
       * - frontend/src/admin/routes/adminRouteRegistry.js（PAGE_LOADERS）
       */
      // "pageModuleSwitches",
      "displayContentConfigs",
      "runtimeParameterConfigs",
    ],
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
