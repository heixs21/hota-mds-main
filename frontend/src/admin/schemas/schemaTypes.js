/**
 * JSDoc typedefs for admin resource schemas.
 * Runtime validation lives in `validateResourceDefinitions.js`; registries in `schemaRegistry.js`.
 *
 * @module admin/schemas/schemaTypes
 */

/**
 * @typedef {{ value: string, label: string }} SelectOption
 */

/**
 * @typedef {'cstDateTime'|'idCount'|'resourceLinks'} CellFormat
 */

/**
 * @typedef {Object} ColumnDefinition
 * @property {string} key
 * @property {string} label
 * @property {SelectOption[]} [options]
 * @property {CellFormat} [cellFormat]
 * @property {string} [resource] Required when `cellFormat` is `resourceLinks`.
 * @property {string} [showWhenPageKey]
 */

/**
 * @typedef {Object} VisibleWhen
 * @property {string} field
 * @property {string|number|boolean} value
 */

/**
 * @typedef {Object} FieldDefinition
 * @property {string} key
 * @property {string} label
 * @property {string} [type] See `FORM_FIELD_TYPES` / `QUERY_FIELD_TYPES` in `schemaRegistry.js`.
 * @property {boolean} [required]
 * @property {*} [defaultValue]
 * @property {string} [placeholder]
 * @property {SelectOption[]} [options]
 * @property {string} [resource]
 * @property {boolean} [allowBlank]
 * @property {string} [storage] Nested object key, e.g. `connectionConfig`.
 * @property {boolean} [omitIfBlank]
 * @property {boolean} [hideInForm]
 * @property {VisibleWhen} [visibleWhen]
 * @property {string} [screenKeyField]
 * @property {string} [areaIdField]
 * @property {string} [filterByField]
 * @property {string} [filterOptionKey]
 * @property {string} [dataSourceField]
 * @property {string} [text] Used by `staticHint`.
 */

/**
 * @typedef {Object} BulkToolbarField
 * @property {string} key
 * @property {string} label
 * @property {'integer'|'decimal'} kind
 * @property {number} min
 * @property {number} max
 * @property {string|number} [defaultInput]
 * @property {string|number} [step]
 */

/**
 * @typedef {Object} BulkApplyToolbar
 * @property {string} apiPath Suffix appended to `endpoint`.
 * @property {string} [valueKey] Body field for single-value bulk updates.
 * @property {string} [label]
 * @property {string|number} [defaultInput]
 * @property {number} [min]
 * @property {number} [max]
 * @property {'booleanSelect'} [inputKind]
 * @property {SelectOption[]} [selectOptions]
 * @property {BulkToolbarField[]} [fields] Multi-field bulk form.
 * @property {(count: number, payload?: *) => string} successMessage
 * @property {string} errorFallback
 */

/**
 * @typedef {Object} ResourceDefinition
 * @property {string} label Page title.
 * @property {string} endpoint REST list root, e.g. `/api/admin/devices`.
 * @property {string} [itemLabel] Singular noun for buttons and toasts.
 * @property {ColumnDefinition[]} columns
 * @property {FieldDefinition[]} [fields]
 * @property {FieldDefinition[]} [queryFields]
 * @property {boolean} [useModalForm]
 * @property {boolean} [readOnly]
 * @property {boolean} [wideModal]
 * @property {string[]} [relatedResources]
 * @property {Record<string, string>} [fixedListParams]
 * @property {string} [fixedSourceType]
 * @property {boolean} [supportsTestConnection]
 * @property {boolean} [supportsHistory]
 * @property {boolean} [supportsCopyAsNew]
 * @property {BulkApplyToolbar} [bulkApplyToolbar]
 */

/**
 * @typedef {Record<string, ResourceDefinition>} ResourceDefinitionMap
 */

export {};
