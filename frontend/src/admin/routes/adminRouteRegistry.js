import { lazy } from "react";

import { ADMIN_RESOURCE_KEYS, resourceKeyToSlug } from "./resourcePaths.js";

const PAGE_LOADERS = {
  devices: () => import("../pages/DevicesPage.jsx"),
  productionLines: () => import("../pages/ProductionLinesPage.jsx"),
  areas: () => import("../pages/AreasPage.jsx"),
  employees: () => import("../pages/EmployeesPage.jsx"),
  materials: () => import("../pages/MaterialsPage.jsx"),
  orders: () => import("../pages/OrdersPage.jsx"),
  screenPageBindings: () => import("../pages/ScreenPageBindingsPage.jsx"),
  screenConfigs: () => import("../pages/ScreenConfigsPage.jsx"),
  pageModuleSwitches: () => import("../pages/PageModuleSwitchesPage.jsx"),
  displayContentConfigs: () => import("../pages/DisplayContentConfigsPage.jsx"),
  runtimeParameterConfigs: () => import("../pages/RuntimeParameterConfigsPage.jsx"),
  codeMappings: () => import("../pages/CodeMappingsPage.jsx"),
  dataSourceOpcua: () => import("../pages/OpcuaDataSourcePage.jsx"),
  dataSourceModbusTcp: () => import("../pages/ModbusTcpDataSourcePage.jsx"),
  dataSourceS7: () => import("../pages/S7DataSourcePage.jsx"),
  dataSourceSapRfc: () => import("../pages/SapRfcDataSourcePage.jsx"),
  dataSourceDatabase: () => import("../pages/DatabaseDataSourcePage.jsx"),
  dataSourceRepair: () => import("../pages/RepairDataSourcePage.jsx"),
  operationLogs: () => import("../pages/OperationLogsPage.jsx"),
};

const PAGE_COMPONENTS = Object.fromEntries(
  Object.entries(PAGE_LOADERS).map(([resourceKey, loader]) => [resourceKey, lazy(loader)]),
);

/** Flat admin routes: /admin/{slug} → lazy page component */
export const ADMIN_RESOURCE_ROUTES = ADMIN_RESOURCE_KEYS.map((resourceKey) => ({
  resourceKey,
  slug: resourceKeyToSlug(resourceKey),
  Component: PAGE_COMPONENTS[resourceKey],
}));

export function getResourcePageComponent(resourceKey) {
  return PAGE_COMPONENTS[resourceKey] ?? null;
}
