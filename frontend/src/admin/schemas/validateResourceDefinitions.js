import { ADMIN_MENU_GROUPS, DEFAULT_ADMIN_RESOURCE } from "./menu.js";
import {
  BULK_FIELD_KINDS,
  BULK_INPUT_KINDS,
  CELL_FORMATS,
  FORM_FIELD_TYPES,
  QUERY_FIELD_TYPES,
} from "./schemaRegistry.js";

/** @typedef {import('./schemaTypes.js').ResourceDefinitionMap} ResourceDefinitionMap */

/**
 * Collect schema validation errors without throwing.
 *
 * @param {ResourceDefinitionMap} resourceDefinitions
 * @param {{ menuGroups?: typeof ADMIN_MENU_GROUPS, defaultAdminResource?: string, adminResourceKeys?: string[] }} [options]
 * @returns {string[]}
 */
export function collectResourceDefinitionErrors(resourceDefinitions, options = {}) {
  const errors = [];
  const menuGroups = options.menuGroups ?? ADMIN_MENU_GROUPS;
  const defaultAdminResource = options.defaultAdminResource ?? DEFAULT_ADMIN_RESOURCE;
  const definitionKeys = new Set(Object.keys(resourceDefinitions));

  function push(message) {
    errors.push(message);
  }

  function collectMenuLeafKeys(items, out) {
    for (const item of items) {
      if (typeof item === "string") {
        out.push(item);
      } else if (item?.kind === "submenu") {
        collectMenuLeafKeys(item.children ?? [], out);
      }
    }
  }

  const menuLeafKeys = [];
  for (const group of menuGroups) {
    collectMenuLeafKeys(group.items ?? [], menuLeafKeys);
  }

  for (const key of menuLeafKeys) {
    if (!resourceDefinitions[key]) {
      push(`Missing resourceDefinitions for menu item: ${key}`);
    }
  }

  if (!resourceDefinitions[defaultAdminResource]) {
    push(`DEFAULT_ADMIN_RESOURCE "${defaultAdminResource}" is missing from resourceDefinitions`);
  }

  const adminResourceKeys = options.adminResourceKeys;
  if (adminResourceKeys) {
    for (const key of adminResourceKeys) {
      if (!resourceDefinitions[key]) {
        push(`ADMIN_RESOURCE_KEYS entry "${key}" is missing from resourceDefinitions`);
      }
    }
    for (const key of menuLeafKeys) {
      if (!adminResourceKeys.includes(key)) {
        push(`Menu leaf "${key}" is not listed in ADMIN_RESOURCE_KEYS`);
      }
    }
    for (const key of adminResourceKeys) {
      if (!menuLeafKeys.includes(key)) {
        push(`ADMIN_RESOURCE_KEYS entry "${key}" is not present in ADMIN_MENU_GROUPS`);
      }
    }
  }

  for (const [resourceKey, definition] of Object.entries(resourceDefinitions)) {
    const prefix = `resourceDefinitions.${resourceKey}`;

    if (!definition || typeof definition !== "object") {
      push(`${prefix}: definition must be an object`);
      continue;
    }

    if (!definition.label || typeof definition.label !== "string") {
      push(`${prefix}: missing string label`);
    }
    if (!definition.endpoint || typeof definition.endpoint !== "string") {
      push(`${prefix}: missing string endpoint`);
    } else if (!definition.endpoint.startsWith("/api/")) {
      push(`${prefix}: endpoint must start with /api/`);
    }

    if (!Array.isArray(definition.columns) || definition.columns.length === 0) {
      push(`${prefix}: columns must be a non-empty array`);
    } else {
      validateColumns(prefix, definition.columns, definitionKeys, push);
    }

    if (definition.fields !== undefined) {
      if (!Array.isArray(definition.fields)) {
        push(`${prefix}: fields must be an array when present`);
      } else {
        validateFields(prefix, definition.fields, definitionKeys, { scope: "fields" }, push);
      }
    } else if (!definition.readOnly) {
      push(`${prefix}: non-readOnly resources should declare fields (can be empty only for readOnly)`);
    }

    if (definition.queryFields !== undefined) {
      if (!Array.isArray(definition.queryFields)) {
        push(`${prefix}: queryFields must be an array when present`);
      } else {
        validateFields(prefix, definition.queryFields, definitionKeys, { scope: "queryFields" }, push);
      }
    }

    if (definition.relatedResources) {
      for (const relatedKey of definition.relatedResources) {
        if (!definitionKeys.has(relatedKey)) {
          push(`${prefix}: relatedResources references unknown key "${relatedKey}"`);
        }
      }
    }

    if (definition.bulkApplyToolbar) {
      validateBulkApplyToolbar(prefix, definition.bulkApplyToolbar, push);
    }
  }

  return errors;
}

/**
 * @param {ResourceDefinitionMap} resourceDefinitions
 * @param {Parameters<typeof collectResourceDefinitionErrors>[1]} [options]
 */
export function validateResourceDefinitions(resourceDefinitions, options) {
  const errors = collectResourceDefinitionErrors(resourceDefinitions, options);
  if (errors.length > 0) {
    throw new Error(`Admin schema validation failed (${errors.length}):\n- ${errors.join("\n- ")}`);
  }
}

function validateColumns(prefix, columns, definitionKeys, push) {
  const seen = new Set();
  for (const [index, column] of columns.entries()) {
    const colPrefix = `${prefix}.columns[${index}]`;
    if (!column?.key) {
      push(`${colPrefix}: missing key`);
    } else if (seen.has(column.key)) {
      push(`${colPrefix}: duplicate column key "${column.key}"`);
    } else {
      seen.add(column.key);
    }
    if (!column?.label) {
      push(`${colPrefix}: missing label`);
    }
    if (column?.cellFormat && !CELL_FORMATS.has(column.cellFormat)) {
      push(`${colPrefix}: unknown cellFormat "${column.cellFormat}"`);
    }
    if (column?.cellFormat === "resourceLinks" && !column.resource) {
      push(`${colPrefix}: cellFormat resourceLinks requires resource`);
    }
    if (column?.resource && !definitionKeys.has(column.resource)) {
      push(`${colPrefix}: column.resource references unknown key "${column.resource}"`);
    }
  }
}

function validateFields(prefix, fields, definitionKeys, { scope }, push) {
  const seen = new Set();
  const fieldKeys = new Set(fields.map((field) => field?.key).filter(Boolean));

  for (const [index, field] of fields.entries()) {
    const fieldPrefix = `${prefix}.${scope}[${index}]`;
    if (!field?.key) {
      push(`${fieldPrefix}: missing key`);
      continue;
    }
    if (seen.has(field.key)) {
      push(`${fieldPrefix}: duplicate field key "${field.key}"`);
    } else {
      seen.add(field.key);
    }
    if (!field.label && field.type !== "checkbox") {
      push(`${fieldPrefix}: missing label`);
    }

    const allowedTypes = scope === "queryFields" ? QUERY_FIELD_TYPES : FORM_FIELD_TYPES;
    const fieldType = field.type ?? "text";
    if (!allowedTypes.has(fieldType)) {
      push(`${fieldPrefix}: unknown type "${fieldType}" for ${scope}`);
    }

    if (field.type === "select" || (scope === "queryFields" && fieldType === "select")) {
      if (!Array.isArray(field.options) || field.options.length === 0) {
        push(`${fieldPrefix}: select requires non-empty options`);
      }
    }

    if (
      fieldType === "resourceSelect" ||
      fieldType === "resourceMultiSelect" ||
      fieldType === "resourceMultiSelectFiltered"
    ) {
      if (!field.resource) {
        push(`${fieldPrefix}: ${fieldType} requires resource`);
      } else if (!definitionKeys.has(field.resource)) {
        push(`${fieldPrefix}: resource references unknown key "${field.resource}"`);
      }
    }

    if (field.visibleWhen) {
      if (!field.visibleWhen.field) {
        push(`${fieldPrefix}: visibleWhen.field is required`);
      } else if (scope === "fields" && !fieldKeys.has(field.visibleWhen.field)) {
        push(`${fieldPrefix}: visibleWhen.field "${field.visibleWhen.field}" not found in fields`);
      }
    }

    if (fieldType === "resourceMultiSelectFiltered") {
      if (!field.filterByField) {
        push(`${fieldPrefix}: resourceMultiSelectFiltered requires filterByField`);
      } else if (scope === "fields" && !fieldKeys.has(field.filterByField)) {
        push(`${fieldPrefix}: filterByField "${field.filterByField}" not found in fields`);
      }
    }
  }
}

function validateBulkApplyToolbar(prefix, toolbar, push) {
  const btPrefix = `${prefix}.bulkApplyToolbar`;
  if (!toolbar.apiPath) {
    push(`${btPrefix}: missing apiPath`);
  }
  if (typeof toolbar.successMessage !== "function") {
    push(`${btPrefix}: successMessage must be a function`);
  }
  if (!toolbar.errorFallback) {
    push(`${btPrefix}: missing errorFallback`);
  }

  if (toolbar.fields?.length) {
    for (const [index, field] of toolbar.fields.entries()) {
      const fPrefix = `${btPrefix}.fields[${index}]`;
      if (!field.key) {
        push(`${fPrefix}: missing key`);
      }
      if (!field.label) {
        push(`${fPrefix}: missing label`);
      }
      if (!BULK_FIELD_KINDS.has(field.kind)) {
        push(`${fPrefix}: kind must be one of ${[...BULK_FIELD_KINDS].join(", ")}`);
      }
      if (typeof field.min !== "number" || typeof field.max !== "number") {
        push(`${fPrefix}: min and max must be numbers`);
      }
    }
    return;
  }

  if (toolbar.inputKind) {
    if (!BULK_INPUT_KINDS.has(toolbar.inputKind)) {
      push(`${btPrefix}: unknown inputKind "${toolbar.inputKind}"`);
    }
    if (toolbar.inputKind === "booleanSelect") {
      if (!toolbar.valueKey) {
        push(`${btPrefix}: booleanSelect requires valueKey`);
      }
      if (!Array.isArray(toolbar.selectOptions) || toolbar.selectOptions.length === 0) {
        push(`${btPrefix}: booleanSelect requires selectOptions`);
      }
    }
    return;
  }

  if (!toolbar.valueKey) {
    push(`${btPrefix}: single-value bulk toolbar requires valueKey`);
  }
  if (!toolbar.label) {
    push(`${btPrefix}: single-value bulk toolbar requires label`);
  }
  if (typeof toolbar.min !== "number" || typeof toolbar.max !== "number") {
    push(`${btPrefix}: single-value bulk toolbar requires numeric min and max`);
  }
}
