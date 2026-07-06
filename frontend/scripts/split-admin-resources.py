"""One-off helper: split adminResources.js into admin/schemas/*.js (M-C1)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src"
SCHEMAS = ROOT / "admin" / "schemas"
lines = (ROOT / "adminResources.js").read_text(encoding="utf-8").splitlines(keepends=True)


def chunk(start: int, end: int) -> str:
    return "".join(lines[start - 1 : end])


SCHEMAS.mkdir(parents=True, exist_ok=True)

(SCHEMAS / "shared.js").write_text(
    chunk(1, 12) + "\nexport { RESERVED_FIELDS, RESERVED_FIELD_KEYS };\n",
    encoding="utf-8",
)

(SCHEMAS / "options.js").write_text(chunk(14, 107), encoding="utf-8")

(SCHEMAS / "menu.js").write_text(chunk(109, 147), encoding="utf-8")

data_sources = chunk(149, 353)
data_sources = data_sources.replace(
    "const DATA_SOURCE_BASE_QUERY_FIELDS",
    "export const DATA_SOURCE_BASE_QUERY_FIELDS",
    1,
)
(SCHEMAS / "dataSources.js").write_text(
    'import { RESERVED_FIELDS } from "./shared.js";\n'
    'import { ACTIVE_STATUS_OPTIONS } from "./options.js";\n\n'
    + data_sources,
    encoding="utf-8",
)

ledger_imports = (
    'import { RESERVED_FIELDS } from "./shared.js";\n'
    "import {\n"
    "  ACTIVE_STATUS_OPTIONS,\n"
    "  DEVICE_STATUS_OPTIONS,\n"
    "  EMPLOYEE_ROLE_OPTIONS,\n"
    "  ORDER_STATUS_OPTIONS,\n"
    "} from \"./options.js\";\n\n"
    "export const ledgerResourceDefinitions = {\n"
)
ledger_body = chunk(356, 558).lstrip()
ledger_body = ledger_body.removeprefix("export const resourceDefinitions = {\n")
(SCHEMAS / "ledger.js").write_text(
    ledger_imports + ledger_body.rstrip().removesuffix("};") + "\n};\n",
    encoding="utf-8",
)

system_imports = (
    'import { RESERVED_FIELDS } from "./shared.js";\n'
    "import {\n"
    "  ACTIVE_STATUS_OPTIONS,\n"
    "  ENTITY_TYPE_OPTIONS,\n"
    "  GANTT_ANCHOR_MODE_OPTIONS,\n"
    "} from \"./options.js\";\n\n"
    "export const systemResourceDefinitions = {\n"
)
system_parts = chunk(559, 593) + chunk(843, 905) + chunk(907, 920)
system_body = system_parts.lstrip()
if system_body.startswith("codeMappings"):
    pass
else:
    system_body = system_body
# Remove operationLogs trailing from chunk 907-920 includes spread line - handle in index
system_body = (
    chunk(559, 593).rstrip().removesuffix(",") + ",\n"
    + chunk(843, 905).rstrip().removesuffix(",") + ",\n"
    + chunk(907, 920).strip().removeprefix("...buildDataSourceResources(),").strip()
)
if not system_body.strip().endswith("},"):
    system_body = system_body.rstrip().rstrip(",") + ",\n"
(SCHEMAS / "system.js").write_text(
    system_imports + system_body + "\n};\n",
    encoding="utf-8",
)

screen_imports = (
    'import { RESERVED_FIELDS } from "./shared.js";\n'
    "import {\n"
    "  ACTIVE_STATUS_OPTIONS,\n"
    "  DATA_SOURCE_BINDING_CATEGORY_OPTIONS,\n"
    "  REALTIME_LAYOUT_OPTIONS,\n"
    "  SCREEN_KEY_OPTIONS,\n"
    "  SCREEN_PAGE_KEY_FLAT_OPTIONS,\n"
    "} from \"./options.js\";\n\n"
    "export const screenResourceDefinitions = {\n"
)
screen_body = chunk(594, 781).rstrip().removesuffix(",") + ",\n" + chunk(782, 841).rstrip().removesuffix(",")
(SCHEMAS / "screen.js").write_text(
    screen_imports + screen_body + ",\n};\n",
    encoding="utf-8",
)

form_utils = chunk(924, 1170)
form_utils = form_utils.replace(
    "export function stringifyJson",
    'import { OMIT_VALUE, RESERVED_FIELD_KEYS } from "./shared.js";\n'
    'import { SCREEN_PAGE_KEY_OPTIONS } from "./options.js";\n\n'
    "export function stringifyJson",
    1,
)
(SCHEMAS / "formUtils.js").write_text(form_utils, encoding="utf-8")

index = '''import { ADMIN_MENU_GROUPS, DEFAULT_ADMIN_RESOURCE } from "./menu.js";
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

function assertResourceDefinitions() {
  for (const group of ADMIN_MENU_GROUPS) {
    for (const item of group.items) {
      if (typeof item === "string") {
        if (!resourceDefinitions[item]) {
          throw new Error(`Missing resourceDefinitions for menu item: ${item}`);
        }
      } else if (item?.kind === "submenu") {
        for (const child of item.children ?? []) {
          if (!resourceDefinitions[child]) {
            throw new Error(`Missing resourceDefinitions for menu item: ${child}`);
          }
        }
      }
    }
  }

  for (const [key, definition] of Object.entries(resourceDefinitions)) {
    if (!definition?.label || !definition?.endpoint) {
      throw new Error(`Invalid resourceDefinitions entry: ${key}`);
    }
  }
}

assertResourceDefinitions();
'''

(SCHEMAS / "index.js").write_text(index, encoding="utf-8")

(ROOT / "adminResources.js").write_text(
    'export * from "./admin/schemas/index.js";\n',
    encoding="utf-8",
)

print("Wrote schemas to", SCHEMAS)
