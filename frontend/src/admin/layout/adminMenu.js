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

/** antd Menu items grouped by ADMIN_MENU_GROUPS */
export function buildAdminMenuItems() {
  return ADMIN_MENU_GROUPS.map((group) => ({
    type: "group",
    label: group.label,
    children: group.items.map((item) => buildGroupItem(item)).filter(Boolean),
  }));
}

export function getAdminMenuOpenKeys(activeResource) {
  for (const group of ADMIN_MENU_GROUPS) {
    for (const item of group.items) {
      if (item?.kind === "submenu" && item.children?.includes(activeResource)) {
        return [item.id];
      }
    }
  }
  return [];
}
