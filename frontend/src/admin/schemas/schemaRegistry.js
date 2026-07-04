/** Field types rendered in edit forms (`ResourceField.jsx`). Undefined `type` is treated as `text`. */
export const FORM_FIELD_TYPES = new Set([
  "text",
  "textarea",
  "integer",
  "decimal",
  "checkbox",
  "select",
  "json",
  "resourceSelect",
  "resourceMultiSelect",
  "resourceMultiSelectFiltered",
  "energyDatabaseEquipmentMulti",
  "screenPageTransfer",
  "staticHint",
]);

/** Additional types allowed in list query bars (`AntResourceQueryBar.jsx`). */
export const QUERY_FIELD_TYPES = new Set(["text", "select", "date", "resourceSelect"]);

/** Column cell formatters (`formatCellValue`). */
export const CELL_FORMATS = new Set(["cstDateTime", "idCount", "resourceLinks"]);

/** Bulk toolbar multi-field value kinds (`runtimeParameterConfigs`). */
export const BULK_FIELD_KINDS = new Set(["integer", "decimal"]);

export const BULK_INPUT_KINDS = new Set(["booleanSelect"]);
