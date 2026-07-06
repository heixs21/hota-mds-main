/**
 * Standalone schema validation for CI / local checks without a full Vite build.
 * Usage: npm run validate:schemas
 */
import { ADMIN_RESOURCE_KEYS } from "../src/admin/routes/resourcePaths.js";
import { ADMIN_MENU_GROUPS, DEFAULT_ADMIN_RESOURCE, resourceDefinitions } from "../src/admin/schemas/index.js";
import { collectResourceDefinitionErrors } from "../src/admin/schemas/validateResourceDefinitions.js";

const errors = collectResourceDefinitionErrors(resourceDefinitions, {
  menuGroups: ADMIN_MENU_GROUPS,
  defaultAdminResource: DEFAULT_ADMIN_RESOURCE,
  adminResourceKeys: ADMIN_RESOURCE_KEYS,
});

if (errors.length > 0) {
  console.error(`Admin schema validation failed (${errors.length}):`);
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(
  `Admin schemas OK: ${Object.keys(resourceDefinitions).length} definitions, ${ADMIN_RESOURCE_KEYS.length} routes.`,
);
