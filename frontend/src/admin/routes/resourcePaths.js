import { DEFAULT_ADMIN_RESOURCE, resourceDefinitions } from "../../adminResources.js";
import { buildActiveResourceStorageKey, pickValidResource } from "../adminUtils.js";

export const ADMIN_BASE_PATH = "/admin";
export const ADMIN_LOGIN_PATH = `${ADMIN_BASE_PATH}/login`;
export const ADMIN_LEGACY_CONSOLE_PATH = `${ADMIN_BASE_PATH}/console`;

/** camelCase resourceKey → kebab-case URL segment */
export function resourceKeyToSlug(resourceKey) {
  return resourceKey.replace(/([A-Z])/g, "-$1").toLowerCase();
}

export function resourceKeyToPath(resourceKey) {
  return `${ADMIN_BASE_PATH}/${resourceKeyToSlug(resourceKey)}`;
}

const SLUG_TO_RESOURCE_KEY = Object.fromEntries(
  Object.keys(resourceDefinitions).map((resourceKey) => [resourceKeyToSlug(resourceKey), resourceKey]),
);

export function slugToResourceKey(slug) {
  return SLUG_TO_RESOURCE_KEY[slug] ?? null;
}

export function pathToResourceKey(pathname) {
  if (!pathname.startsWith(`${ADMIN_BASE_PATH}/`)) {
    return null;
  }

  const segment = pathname.slice(`${ADMIN_BASE_PATH}/`.length).split("/")[0];
  if (!segment || segment === "login" || segment === "console") {
    return null;
  }

  return slugToResourceKey(segment);
}

export function isAdminResourcePath(pathname) {
  return pathToResourceKey(pathname) !== null;
}

export function getDefaultAdminPath(username) {
  const storageKey = buildActiveResourceStorageKey(username);
  const saved = window.localStorage.getItem(storageKey);
  const resourceKey = pickValidResource(saved || DEFAULT_ADMIN_RESOURCE);
  return resourceKeyToPath(resourceKey);
}

/** Leaf menu resources registered as flat admin routes. */
export const ADMIN_RESOURCE_KEYS = [
  "devices",
  "productionLines",
  "areas",
  "employees",
  "materials",
  "orders",
  "screenPageBindings",
  "screenConfigs",
  "pageModuleSwitches",
  "displayContentConfigs",
  "runtimeParameterConfigs",
  "codeMappings",
  "dataSourceOpcua",
  "dataSourceModbusTcp",
  "dataSourceS7",
  "dataSourceSapRfc",
  "dataSourceDatabase",
  "dataSourceRepair",
  "operationLogs",
];
