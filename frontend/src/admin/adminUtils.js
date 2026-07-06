import { DEFAULT_ADMIN_RESOURCE, resourceDefinitions } from "../adminResources.js";
import { ACTIVE_RESOURCE_STORAGE_PREFIX } from "./adminConstants.js";

export function buildActiveResourceStorageKey(username) {
  return `${ACTIVE_RESOURCE_STORAGE_PREFIX}:${username || "anonymous"}`;
}

export function pickValidResource(resourceKey) {
  return resourceDefinitions[resourceKey] ? resourceKey : DEFAULT_ADMIN_RESOURCE;
}

export function httpErrorToastVariant(status) {
  if (status === 403 || status === 404) {
    return "warning";
  }
  return "error";
}

/** Page-size Select props so the dropdown renders above fixed table columns. */
export const ADMIN_TABLE_PAGE_SIZE_CHANGER = {
  getPopupContainer: () => document.body,
  popupClassName: "admin-table-page-size-dropdown",
};

export const ADMIN_TABLE_PAGE_SIZE_OPTIONS = [10, 20, 50];

/** Display-only row index column; respects current pagination. */
export function buildRowIndexColumn(page, pageSize) {
  return {
    title: "序号",
    key: "__rowIndex",
    width: 64,
    align: "center",
    render: (_, __, index) => (page - 1) * pageSize + index + 1,
  };
}

/** Placeholder text for antd Select in admin forms or query bars. */
export function buildSelectPlaceholder(field, { query = false } = {}) {
  if (field?.placeholder) {
    return field.placeholder;
  }
  if (query) {
    return "全部";
  }
  if (field?.allowBlank) {
    return "不设置";
  }
  const label = field?.label?.trim();
  return label ? `请选择${label}` : "请选择";
}
