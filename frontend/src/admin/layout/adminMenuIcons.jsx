import {
  ApiOutlined,
  BankOutlined,
  BlockOutlined,
  BookOutlined,
  CloudServerOutlined,
  ClusterOutlined,
  DatabaseOutlined,
  DesktopOutlined,
  EnvironmentOutlined,
  FundProjectionScreenOutlined,
  GatewayOutlined,
  HistoryOutlined,
  InboxOutlined,
  MedicineBoxOutlined,
  MonitorOutlined,
  PartitionOutlined,
  SettingOutlined,
  ShoppingOutlined,
  SlidersOutlined,
  SmileOutlined,
  SwapOutlined,
  TeamOutlined,
} from "@ant-design/icons";
import { createElement } from "react";

/** 一级分组图标 */
const GROUP_ICONS = {
  basic: BookOutlined,
  screen: MonitorOutlined,
  system: SettingOutlined,
};

/** 二级子菜单图标 */
const SUBMENU_ICONS = {
  dataSources: CloudServerOutlined,
};

/** 叶子菜单 / 资源页图标（尽量不重复） */
const RESOURCE_ICONS = {
  areas: EnvironmentOutlined,
  codeMappings: SwapOutlined,
  dataSourceDatabase: DatabaseOutlined,
  dataSourceModbusTcp: ClusterOutlined,
  dataSourceOpcua: ApiOutlined,
  dataSourceRepair: MedicineBoxOutlined,
  dataSourceS7: GatewayOutlined,
  dataSourceSapRfc: BankOutlined,
  devices: DesktopOutlined,
  displayContentConfigs: SmileOutlined,
  employees: TeamOutlined,
  materials: InboxOutlined,
  operationLogs: HistoryOutlined,
  orders: ShoppingOutlined,
  // 【已隐藏】pageModuleSwitches: ControlOutlined,
  productionLines: PartitionOutlined,
  runtimeParameterConfigs: SlidersOutlined,
  screenConfigs: FundProjectionScreenOutlined,
  screenPageBindings: BlockOutlined,
};

export function renderAdminMenuIcon(key) {
  const Icon = RESOURCE_ICONS[key] ?? SUBMENU_ICONS[key] ?? GROUP_ICONS[key];
  return Icon ? createElement(Icon) : null;
}
