import { OMIT_VALUE, RESERVED_FIELD_KEYS } from "./shared.js";
import { SCREEN_PAGE_KEY_OPTIONS } from "./options.js";

export function stringifyJson(value) {
  return JSON.stringify(value, null, 2);
}


export function createEmptyForm(resourceDefinition) {
  const nextState = {};
  for (const field of resourceDefinition.fields) {
    if (field.type === "staticHint") {
      continue;
    }
    if (field.type === "json" || field.type === "screenPageTransfer") {
      const rawDefault = field.defaultValue ?? {};
      nextState[field.key] = Object.keys(rawDefault).length === 0 && field.omitIfBlank ? "" : stringifyJson(rawDefault);
    } else if (field.type === "checkbox") {
      nextState[field.key] = Boolean(field.defaultValue);
    } else if (
      field.type === "resourceMultiSelect" ||
      field.type === "resourceMultiSelectFiltered" ||
      field.type === "energyDatabaseEquipmentMulti"
    ) {
      nextState[field.key] = Array.isArray(field.defaultValue) ? [...field.defaultValue] : [];
    } else {
      nextState[field.key] = field.defaultValue ?? "";
    }
  }
  return nextState;
}


function readNestedValue(item, storageKey, fieldKey) {
  const container = item?.[storageKey];
  if (container === null || container === undefined) {
    return undefined;
  }
  if (typeof container !== "object") {
    return undefined;
  }
  return container[fieldKey];
}


export function createEmptyQuery(resourceDefinition) {
  const nextState = {};
  for (const field of resourceDefinition.queryFields ?? []) {
    nextState[field.key] = "";
  }
  return nextState;
}

/** 从已有条目生成「复制新增」表单：编码/名称加后缀，预留字段清空。 */
export function createCopyFormFromItem(resourceDefinition, item, { copyIndex = 0, existingCodes = new Set() } = {}) {
  const form = createFormFromItem(resourceDefinition, item);
  const baseCode = String(form.code || "item").replace(/_copy\d*$/, "");
  let candidate = copyIndex === 0 ? `${baseCode}_copy` : `${baseCode}_copy${copyIndex + 1}`;
  let n = Math.max(copyIndex, 1);
  while (existingCodes.has(candidate)) {
    candidate = `${baseCode}_copy${n}`;
    n += 1;
  }
  existingCodes.add(candidate);
  form.code = candidate;
  const baseName = String(form.name || form.code || "").replace(/\s*\(复制\d*\)\s*$/, "");
  form.name = copyIndex === 0 ? `${baseName} (复制)` : `${baseName} (复制${copyIndex + 1})`;
  for (const key of RESERVED_FIELD_KEYS) {
    form[key] = "";
  }
  return form;
}

export function createFormFromItem(resourceDefinition, item) {
  const nextState = {};
  for (const field of resourceDefinition.fields) {
    if (field.type === "staticHint") {
      continue;
    }
    const rawValue = field.storage
      ? readNestedValue(item, field.storage, field.key)
      : item?.[field.key];
    if (field.type === "json" || field.type === "screenPageTransfer") {
      if (rawValue === undefined && field.omitIfBlank) {
        nextState[field.key] = "";
      } else {
        nextState[field.key] = stringifyJson(rawValue ?? field.defaultValue ?? {});
      }
    } else if (field.type === "checkbox") {
      nextState[field.key] = Boolean(rawValue);
    } else if (field.type === "energyDatabaseEquipmentMulti") {
      if (Array.isArray(rawValue)) {
        nextState[field.key] = rawValue.map((v) => String(v)).filter(Boolean);
      } else {
        nextState[field.key] = [];
      }
    } else if (field.type === "resourceMultiSelect" || field.type === "resourceMultiSelectFiltered") {
      if (Array.isArray(rawValue)) {
        nextState[field.key] = rawValue
          .map((v) => Number(v))
          .filter((n) => Number.isInteger(n) && n > 0);
      } else {
        nextState[field.key] = Array.isArray(field.defaultValue) ? [...field.defaultValue] : [];
      }
    } else if (rawValue === null || rawValue === undefined) {
      nextState[field.key] = field.defaultValue ?? "";
    } else {
      nextState[field.key] = rawValue;
    }
  }
  return nextState;
}


/**
 * @param {object} [fullForm]  全表状态；`screenPageTransfer` 需用其 `screenKey` 与备选项对齐
 */
export function parseFieldValue(field, rawValue, fullForm) {
  if (field.type === "staticHint") {
    return OMIT_VALUE;
  }
  if (field.type === "checkbox") {
    return Boolean(rawValue);
  }
  if (field.type === "integer") {
    return rawValue === "" ? null : Number.parseInt(rawValue, 10);
  }
  if (field.type === "decimal") {
    return rawValue === "" ? null : String(rawValue);
  }
  if (field.type === "resourceSelect") {
    return rawValue === "" ? null : Number(rawValue);
  }
  if (field.type === "energyDatabaseEquipmentMulti") {
    if (!Array.isArray(rawValue)) {
      return [];
    }
    return rawValue.map((value) => String(value)).filter(Boolean);
  }
  if (field.type === "resourceMultiSelect" || field.type === "resourceMultiSelectFiltered") {
    if (!Array.isArray(rawValue)) {
      return [];
    }
    return rawValue
      .map((value) => Number(value))
      .filter((value) => Number.isInteger(value) && value > 0);
  }
  if (field.type === "json" || field.type === "screenPageTransfer") {
    if (rawValue === "" && field.omitIfBlank) {
      return OMIT_VALUE;
    }
    if (rawValue === "") {
      if (field.type === "screenPageTransfer") {
        return Array.isArray(field.defaultValue) ? field.defaultValue : [];
      }
      return field.defaultValue ?? {};
    }
    const parsed = JSON.parse(rawValue);
    if (field.type === "screenPageTransfer") {
      if (!Array.isArray(parsed)) {
        return Array.isArray(field.defaultValue) ? field.defaultValue : [];
      }
      const keys = parsed.filter((k) => typeof k === "string");
      if (fullForm) {
        const sk = fullForm[field.screenKeyField ?? "screenKey"] || "left";
        const valid = Object.keys(SCREEN_PAGE_KEY_OPTIONS[sk] || {});
        const filtered = keys.filter((k) => valid.includes(k));
        if (filtered.length > 0) {
          return filtered;
        }
        return sk === "right" ? ["schedule"] : ["overview"];
      }
      return keys;
    }
    return parsed;
  }
  return rawValue;
}


function formatCstDateTime(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).formatToParts(date);
  const map = {};
  for (const { type, value: partValue } of parts) {
    if (type !== "literal") {
      map[type] = partValue;
    }
  }
  return `${map.year}-${map.month}-${map.day} ${map.hour}:${map.minute}:${map.second}`;
}


export function fieldVisibleForForm(field, formState) {
  const w = field.visibleWhen;
  if (!w) {
    return true;
  }
  return String(formState[w.field] ?? "") === String(w.value);
}


export function formatCellValue(value, column, row) {
  if (column?.showWhenPageKey && row?.pageKey !== column.showWhenPageKey) {
    return "-";
  }
  if (column?.cellFormat === "cstDateTime") {
    return formatCstDateTime(value);
  }
  if (Array.isArray(value) && column?.cellFormat === "idCount") {
    return value.length ? `${value.length} 项` : "-";
  }
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (Array.isArray(column?.options)) {
    const hit = column.options.find((opt) => opt.value === value);
    if (hit) {
      return hit.label;
    }
  }
  if (typeof value === "boolean") {
    return value ? "是" : "否";
  }
  if (typeof value === "object") {
    if (column?.cellFormat === "resourceLinks" && Array.isArray(value)) {
      return value.map((item) => item?.name || item?.code || item?.id).filter(Boolean).join(" / ") || "-";
    }
    if (value.storageType) {
      return `${value.storageType}${value.hasEncryptedSecret ? " / 已有密文" : ""}`;
    }
    return stringifyJson(value);
  }
  return String(value);
}
