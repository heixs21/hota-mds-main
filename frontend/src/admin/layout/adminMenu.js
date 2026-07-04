import { ADMIN_MENU_GROUPS, resourceDefinitions } from "../../adminResources.js";
import { resourceKeyToPath } from "../routes/resourcePaths.js";

function buildLeafItem(resourceKey) {
  const definition = resourceDefinitions[resourceKey];
  if (!definition) {
    return null;
  }

  return {
    key: resourceKeyToPath(resourceKey),
    label: definition.label,
  };
}

function buildGroupItem(item) {
  if (typeof item === "string") {
    return buildLeafItem(item);
  }

  if (item?.kind === "submenu") {
    return {
      key: item.id,
      label: item.label,
      children: item.children.map((childKey) => buildLeafItem(childKey)).filter(Boolean),
    };
  }

  return null;
}

/** Top-level collapsible menu keys — default expanded on first load. */
export const DEFAULT_ADMIN_MENU_OPEN_KEYS = ADMIN_MENU_GROUPS.map((group) => group.id);

/** antd Menu: three collapsible first-level groups, each containing leaf routes or nested submenus. */
export function buildAdminMenuItems() {
  return ADMIN_MENU_GROUPS.map((group) => ({
    key: group.id,
    label: group.label,
    children: group.items.map((item) => buildGroupItem(item)).filter(Boolean),
  }));
}

/** Extra open keys for nested submenus (e.g. 数据源配置) when the active page lives inside them. */
export function getAdminMenuNestedOpenKeys(activeResource) {
  for (const group of ADMIN_MENU_GROUPS) {
    for (const item of group.items) {
      if (item?.kind === "submenu" && item.children?.includes(activeResource)) {
        return [group.id, item.id];
      }
    }
  }
  return [];
}

export function getInitialAdminMenuOpenKeys(activeResource) {
  return Array.from(new Set([...DEFAULT_ADMIN_MENU_OPEN_KEYS, ...getAdminMenuNestedOpenKeys(activeResource)]));
}
