import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const pages = [
  ["DevicesPage", "devices"],
  ["ProductionLinesPage", "productionLines"],
  ["AreasPage", "areas"],
  ["EmployeesPage", "employees"],
  ["MaterialsPage", "materials"],
  ["OrdersPage", "orders"],
  ["ScreenPageBindingsPage", "screenPageBindings"],
  ["ScreenConfigsPage", "screenConfigs"],
  ["PageModuleSwitchesPage", "pageModuleSwitches"],
  ["DisplayContentConfigsPage", "displayContentConfigs"],
  ["RuntimeParameterConfigsPage", "runtimeParameterConfigs"],
  ["CodeMappingsPage", "codeMappings"],
  ["OpcuaDataSourcePage", "dataSourceOpcua"],
  ["ModbusTcpDataSourcePage", "dataSourceModbusTcp"],
  ["S7DataSourcePage", "dataSourceS7"],
  ["SapRfcDataSourcePage", "dataSourceSapRfc"],
  ["DatabaseDataSourcePage", "dataSourceDatabase"],
  ["RepairDataSourcePage", "dataSourceRepair"],
  ["OperationLogsPage", "operationLogs"],
];

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dir = path.resolve(__dirname, "../src/admin/pages");

for (const [name, key] of pages) {
  const content = `import { createResourcePage } from "./createResourcePage.jsx";

export default createResourcePage("${key}");
`;
  fs.writeFileSync(path.join(dir, `${name}.jsx`), content, "utf8");
}

console.log(`created ${pages.length} pages`);
