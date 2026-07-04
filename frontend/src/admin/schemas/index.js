import { ADMIN_MENU_GROUPS, DEFAULT_ADMIN_RESOURCE } from "./menu.js";
import {
  ALL_PAGE_KEY_OPTIONS,
  DATA_SOURCE_BINDING_CATEGORY_OPTIONS,
  DATA_SOURCE_TYPE_OPTIONS,
  SCREEN_PAGE_KEY_FLAT_OPTIONS,
  SCREEN_PAGE_KEY_OPTIONS,
} from "./options.js";
import { buildDataSourceResources, dataSourceResourceKey } from "./dataSources.js";
import { ledgerResourceDefinitions } from "./ledger.js";
import { screenResourceDefinitions } from "./screen.js";
import { systemResourceDefinitions } from "./system.js";
import { validateResourceDefinitions } from "./validateResourceDefinitions.js";

export { FORM_FIELD_TYPES, QUERY_FIELD_TYPES, CELL_FORMATS } from "./schemaRegistry.js";
export { collectResourceDefinitionErrors, validateResourceDefinitions } from "./validateResourceDefinitions.js";

export { OMIT_VALUE, RESERVED_FIELD_KEYS } from "./shared.js";
export {
  ALL_PAGE_KEY_OPTIONS,
  DATA_SOURCE_BINDING_CATEGORY_OPTIONS,
  DATA_SOURCE_TYPE_OPTIONS,
  SCREEN_PAGE_KEY_FLAT_OPTIONS,
  SCREEN_PAGE_KEY_OPTIONS,
} from "./options.js";
export { ADMIN_MENU_GROUPS, DEFAULT_ADMIN_RESOURCE } from "./menu.js";
export { buildDataSourceResources, dataSourceResourceKey } from "./dataSources.js";
export {
  createCopyFormFromItem,
  createEmptyForm,
  createEmptyQuery,
  createFormFromItem,
  fieldVisibleForForm,
  formatCellValue,
  parseFieldValue,
  stringifyJson,
} from "./formUtils.js";

export const resourceDefinitions = {
  ...ledgerResourceDefinitions,
  ...screenResourceDefinitions,
  ...systemResourceDefinitions,
  ...buildDataSourceResources(),
};

validateResourceDefinitions(resourceDefinitions);
