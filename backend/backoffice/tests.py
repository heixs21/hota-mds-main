from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.dateparse import parse_datetime
from rest_framework.test import APIClient

from .display_services import (
    DEFAULT_DISPLAY_CONTENT,
    _compute_schedule_window_anchor,
    _display_parameter_value,
    _format_seconds_hms,
    _map_runtime_status_display,
    _normalize_gantt_anchor_mode,
    _resolve_machine_panel_status,
    get_screen_payload,
    load_mock_display_data,
)
from .connection_test_services import ConnectionTestResult
from .models import (
    Area,
    DataSourceConfig,
    Device,
    ScreenConfig,
    DisplayContentConfig,
    Material,
    OperationLog,
    Order,
    PageModuleSwitch,
    ProductionLine,
    RuntimeParameterConfig,
    ScreenPageBinding,
)


class BackofficeApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        user_model.objects.create_user(
            username="admin",
            password="admin123456",
            is_staff=True,
        )
        self.client = APIClient()
        login_response = self.client.post(
            "/api/admin/auth/login",
            {"username": "admin", "password": "admin123456"},
            format="json",
        )
        token = login_response.data["data"]["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_area_line_and_device_crud_flow(self):
        area_response = self.client.post(
            "/api/admin/areas",
            {"code": "A01", "name": "总装区", "isActive": True},
            format="json",
        )
        self.assertEqual(area_response.status_code, 201)
        area_id = area_response.data["data"]["id"]

        line_response = self.client.post(
            "/api/admin/production-lines",
            {"code": "L01", "name": "一号线", "areaId": area_id, "isActive": True},
            format="json",
        )
        self.assertEqual(line_response.status_code, 201)
        line_id = line_response.data["data"]["id"]

        device_response = self.client.post(
            "/api/admin/devices",
            {
                "code": "D01",
                "name": "贴标机",
                "ip": "192.168.1.100",
                "areaId": area_id,
                "productionLineId": line_id,
                "defaultStatus": "running",
                "isActive": True,
            },
            format="json",
        )
        self.assertEqual(device_response.status_code, 201)
        self.assertEqual(device_response.data["data"]["ip"], "192.168.1.100")
        self.assertEqual(device_response.data["data"]["productionLineName"], "一号线")

        list_response = self.client.get("/api/admin/devices")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data["data"]["total"], 1)

    def test_device_list_supports_page_and_page_size(self):
        area = self.client.post(
            "/api/admin/areas",
            {"code": "A-PAGE", "name": "分页区域", "isActive": True},
            format="json",
        ).data["data"]

        line = self.client.post(
            "/api/admin/production-lines",
            {"code": "L-PAGE", "name": "分页产线", "areaId": area["id"], "isActive": True},
            format="json",
        ).data["data"]

        for index in range(25):
            self.client.post(
                "/api/admin/devices",
                {
                    "code": f"DV{index:03d}",
                    "name": f"设备{index:03d}",
                    "ip": f"192.168.10.{index}",
                    "areaId": area["id"],
                    "productionLineId": line["id"],
                    "defaultStatus": "running",
                    "isActive": True,
                },
                format="json",
            )

        first_page = self.client.get("/api/admin/devices?page=1&pageSize=10")
        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(first_page.data["data"]["total"], 25)
        self.assertEqual(first_page.data["data"]["page"], 1)
        self.assertEqual(first_page.data["data"]["pageSize"], 10)
        self.assertEqual(len(first_page.data["data"]["items"]), 10)

        third_page = self.client.get("/api/admin/devices?page=3&pageSize=10")
        self.assertEqual(third_page.status_code, 200)
        self.assertEqual(len(third_page.data["data"]["items"]), 5)

    def test_employee_crud_and_role_validation(self):
        create_response = self.client.post(
            "/api/admin/employees",
            {
                "employeeNo": "EMP001A",
                "name": "张三",
                "role": "team_leader",
                "isActive": True,
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.data["data"]["employeeNo"], "EMP001A")
        self.assertEqual(create_response.data["data"]["role"], "team_leader")

        invalid_response = self.client.post(
            "/api/admin/employees",
            {
                "employeeNo": "EMP-001",
                "name": "李四",
                "role": "employee",
                "isActive": True,
            },
            format="json",
        )
        self.assertEqual(invalid_response.status_code, 400)
        self.assertEqual(invalid_response.data["code"], "INVALID_INPUT")

    def test_code_mapping_and_screen_config_crud(self):
        mapping_response = self.client.post(
            "/api/admin/code-mappings",
            {
                "entityType": "device",
                "sourceSystem": "sap_rfc",
                "internalCode": "D01",
                "externalCode": "EQP-001",
                "isActive": True,
            },
            format="json",
        )
        self.assertEqual(mapping_response.status_code, 201)

        screen_response = self.client.post(
            "/api/admin/screen-configs",
            {
                "screenKey": "left",
                "title": "左屏展示",
                "subtitle": "综合运行",
                "rotationIntervalSeconds": 60,
                "moduleSettings": {"repairPlaceholder": True},
                "themeSettings": {"logoUrl": "/assets/logo.png"},
                "isActive": True,
            },
            format="json",
        )
        self.assertEqual(screen_response.status_code, 201)
        self.assertEqual(screen_response.data["data"]["screenKey"], "left")

    def test_display_content_config_and_runtime_parameter_config_crud(self):
        display_response = self.client.post(
            "/api/admin/display-content-configs",
            {
                "configKey": "default",
                "companyName": "和泰智造",
                "welcomeMessage": "欢迎莅临参观指导",
                "logoUrl": "/assets/hota-logo.png",
                "promoImageUrls": ["/assets/visit-1.png", "/assets/visit-2.png"],
                "isActive": True,
            },
            format="json",
        )
        self.assertEqual(display_response.status_code, 201)
        self.assertEqual(display_response.data["data"]["configKey"], "default")

        runtime_response = self.client.post(
            "/api/admin/runtime-parameter-configs",
            {
                "configKey": "default",
                "singleDayEffectiveWorkHours": "16.50",
                "defaultStandardCapacityPerHour": "120.00",
                "delayWarningBufferHours": "2.00",
                "ganttWindowDays": 30,
                "autoScrollEnabled": True,
                "autoScrollRowsThreshold": 12,
                "recentCapacityWindowHours": 2,
                "productionTrendWindowHours": 8,
                "notes": "一期前段默认参数",
                "isActive": True,
            },
            format="json",
        )
        self.assertEqual(runtime_response.status_code, 201)
        self.assertEqual(runtime_response.data["data"]["singleDayEffectiveWorkHours"], "16.50")

    def test_runtime_parameter_config_rejects_invalid_work_hours(self):
        response = self.client.post(
            "/api/admin/runtime-parameter-configs",
            {
                "configKey": "bad-hours",
                "singleDayEffectiveWorkHours": "25.00",
                "defaultStandardCapacityPerHour": "100.00",
                "delayWarningBufferHours": "1.00",
                "ganttWindowDays": 30,
                "autoScrollEnabled": True,
                "autoScrollRowsThreshold": 10,
                "recentCapacityWindowHours": 2,
                "productionTrendWindowHours": 8,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "INVALID_INPUT")

    def test_data_source_config_supports_env_ref_secret_structure(self):
        response = self.client.post(
            "/api/admin/data-source-configs",
            {
                "code": "sap-main",
                "name": "SAP 主数据源",
                "sourceType": "sap_rfc",
                "isEnabled": True,
                "refreshIntervalSeconds": 300,
                "timeoutSeconds": 30,
                "connectionConfig": {
                    "host": "sap.internal",
                    "client": "100",
                    "username": "svc_hota",
                },
                "secretConfig": {
                    "storageType": "env_ref",
                    "envMapping": {"password": "SAP_MAIN_PASSWORD"},
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["secretSummary"]["storageType"], "env_ref")
        self.assertEqual(response.data["data"]["secretSummary"]["envKeys"], ["password"])
        self.assertEqual(DataSourceConfig.objects.count(), 1)

    def test_data_source_config_rejects_invalid_secret_structure(self):
        response = self.client.post(
            "/api/admin/data-source-configs",
            {
                "code": "energy-main",
                "name": "能耗库",
                "sourceType": "energy_db",
                "secretConfig": {"storageType": "encrypted", "ciphertext": ""},
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "INVALID_INPUT")

    def test_data_source_config_trims_connection_config_to_required_keys(self):
        response = self.client.post(
            "/api/admin/data-source-configs",
            {
                "code": "opcua-trim",
                "name": "OPC UA Trim",
                "sourceType": "opcua",
                "connectionConfig": {
                    "endpointUrl": "opc.tcp://192.168.32.61:4840",
                    "username": "OpcUaClient",
                    "password": "secret",
                    "assets": [{"code": "D01", "name": "设备1"}],
                    "unexpected": "drop-me",
                },
                "node": ["ns=2;s=/Channel/State/chanStatus", "ns=2;s=/Channel/State/chanAlarm"],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        item = DataSourceConfig.objects.get(code="opcua-trim")
        self.assertEqual(
            item.connection_config,
            {
                "endpointUrl": "opc.tcp://192.168.32.61:4840",
                "username": "OpcUaClient",
                "password": "secret",
            },
        )
        self.assertEqual(
            item.node,
            ["ns=2;s=/Channel/State/chanStatus", "ns=2;s=/Channel/State/chanAlarm"],
        )

    def test_opcua_bulk_refresh_interval_updates_matching_rows(self):
        for code, name in (
            ("opcua-bulk-a", "筛选命中甲"),
            ("opcua-bulk-b", "筛选命中乙"),
        ):
            create_response = self.client.post(
                "/api/admin/data-source-configs",
                {
                    "code": code,
                    "name": name,
                    "sourceType": "opcua",
                    "connectionConfig": {"endpointUrl": "opc.tcp://127.0.0.1:4840"},
                    "node": [{"nodeId": "ns=2;s=/x", "comment": "测试节点"}],
                    "refreshIntervalSeconds": 300,
                },
                format="json",
            )
            self.assertEqual(create_response.status_code, 201)

        id_a = DataSourceConfig.objects.get(code="opcua-bulk-a").pk
        id_b = DataSourceConfig.objects.get(code="opcua-bulk-b").pk

        empty_response = self.client.post(
            "/api/admin/data-source-configs/bulk-refresh-interval",
            {"refreshIntervalSeconds": 60, "ids": []},
            format="json",
        )
        self.assertEqual(empty_response.status_code, 400)

        all_response = self.client.post(
            "/api/admin/data-source-configs/bulk-refresh-interval",
            {"refreshIntervalSeconds": 60, "ids": [id_a, id_b]},
            format="json",
        )
        self.assertEqual(all_response.status_code, 200)
        self.assertEqual(all_response.data["data"]["updatedCount"], 2)
        self.assertEqual(DataSourceConfig.objects.get(code="opcua-bulk-a").refresh_interval_seconds, 60)
        self.assertEqual(DataSourceConfig.objects.get(code="opcua-bulk-b").refresh_interval_seconds, 60)

        filtered_response = self.client.post(
            "/api/admin/data-source-configs/bulk-refresh-interval?keyword=bulk-a",
            {"refreshIntervalSeconds": 120, "ids": [id_a]},
            format="json",
        )
        self.assertEqual(filtered_response.status_code, 200)
        self.assertEqual(filtered_response.data["data"]["updatedCount"], 1)
        self.assertEqual(DataSourceConfig.objects.get(code="opcua-bulk-a").refresh_interval_seconds, 120)
        self.assertEqual(DataSourceConfig.objects.get(code="opcua-bulk-b").refresh_interval_seconds, 60)

        bad_response = self.client.post(
            "/api/admin/data-source-configs/bulk-refresh-interval",
            {"refreshIntervalSeconds": 3, "ids": [id_a]},
            format="json",
        )
        self.assertEqual(bad_response.status_code, 400)

    def test_screen_config_bulk_rotation_interval_updates_checked_rows(self):
        area_response = self.client.post(
            "/api/admin/areas",
            {"code": "A-SC-BULK", "name": "屏批量测", "isActive": True},
            format="json",
        )
        self.assertEqual(area_response.status_code, 201)
        aid = area_response.data["data"]["id"]

        created_ids = []
        for screen_key, title in (("left", "左屏"), ("right", "右屏")):
            sc_response = self.client.post(
                "/api/admin/screen-configs",
                {
                    "areaId": aid,
                    "screenKey": screen_key,
                    "title": title,
                    "subtitle": "",
                    "rotationIntervalSeconds": 60,
                    "pageOrder": [],
                    "moduleSettings": {},
                    "themeSettings": {},
                    "isActive": True,
                },
                format="json",
            )
            self.assertEqual(sc_response.status_code, 201)
            created_ids.append(sc_response.data["data"]["id"])

        bulk_response = self.client.post(
            "/api/admin/screen-configs/bulk-rotation-interval",
            {"rotationIntervalSeconds": 120, "ids": created_ids},
            format="json",
        )
        self.assertEqual(bulk_response.status_code, 200)
        self.assertEqual(bulk_response.data["data"]["updatedCount"], 2)
        for pk in created_ids:
            self.assertEqual(ScreenConfig.objects.get(pk=pk).rotation_interval_seconds, 120)

        one_response = self.client.post(
            "/api/admin/screen-configs/bulk-rotation-interval",
            {"rotationIntervalSeconds": 45, "ids": [created_ids[0]]},
            format="json",
        )
        self.assertEqual(one_response.status_code, 200)
        self.assertEqual(ScreenConfig.objects.get(pk=created_ids[0]).rotation_interval_seconds, 45)
        self.assertEqual(ScreenConfig.objects.get(pk=created_ids[1]).rotation_interval_seconds, 120)

    def test_runtime_parameter_config_bulk_runtime_fields(self):
        created_ids = []
        for config_key in ("rt-bulk-a", "rt-bulk-b"):
            r = self.client.post(
                "/api/admin/runtime-parameter-configs",
                {
                    "configKey": config_key,
                    "singleDayEffectiveWorkHours": "8.00",
                    "defaultStandardCapacityPerHour": "1.00",
                    "delayWarningBufferHours": "1.00",
                    "ganttWindowDays": 20,
                    "autoScrollEnabled": True,
                    "autoScrollRowsThreshold": 10,
                    "recentCapacityWindowHours": 2,
                    "productionTrendWindowHours": 8,
                    "isActive": True,
                },
                format="json",
            )
            self.assertEqual(r.status_code, 201)
            created_ids.append(r.data["data"]["id"])

        bulk = self.client.post(
            "/api/admin/runtime-parameter-configs/bulk-runtime-fields",
            {
                "ids": created_ids,
                "singleDayEffectiveWorkHours": "12.50",
                "ganttWindowDays": 45,
            },
            format="json",
        )
        self.assertEqual(bulk.status_code, 200)
        self.assertEqual(bulk.data["data"]["updatedCount"], 2)
        self.assertEqual(
            RuntimeParameterConfig.objects.get(config_key="rt-bulk-a").single_day_effective_work_hours,
            Decimal("12.50"),
        )
        self.assertEqual(RuntimeParameterConfig.objects.get(config_key="rt-bulk-a").gantt_window_days, 45)

    def test_modbus_tcp_bulk_refresh_interval_updates_checked_rows(self):
        ids = []
        for code in ("mb-bulk-a", "mb-bulk-b"):
            r = self.client.post(
                "/api/admin/data-source-configs",
                {
                    "code": code,
                    "name": code,
                    "sourceType": "modbus_tcp",
                    "connectionConfig": {},
                    "refreshIntervalSeconds": 300,
                },
                format="json",
            )
            self.assertEqual(r.status_code, 201, msg=r.data if hasattr(r, "data") else code)
            ids.append(r.data["data"]["id"])

        bulk = self.client.post(
            "/api/admin/data-source-configs/bulk-refresh-interval?source_type=modbus_tcp",
            {"refreshIntervalSeconds": 90, "ids": ids},
            format="json",
        )
        self.assertEqual(bulk.status_code, 200)
        self.assertEqual(bulk.data["data"]["updatedCount"], 2)
        self.assertEqual(DataSourceConfig.objects.get(code="mb-bulk-a").refresh_interval_seconds, 90)

    def test_screen_page_binding_bulk_set_enabled(self):
        list_response = self.client.get("/api/admin/screen-page-bindings?pageSize=50")
        self.assertEqual(list_response.status_code, 200)
        items = list_response.data["data"]["items"]
        self.assertGreaterEqual(len(items), 2)
        ids = [items[0]["id"], items[1]["id"]]

        bulk = self.client.post(
            "/api/admin/screen-page-bindings/bulk-set-enabled",
            {"ids": ids, "isEnabled": False},
            format="json",
        )
        self.assertEqual(bulk.status_code, 200)
        self.assertEqual(bulk.data["data"]["updatedCount"], 2)
        for pk in ids:
            self.assertFalse(ScreenPageBinding.objects.get(pk=pk).is_enabled)

    @patch("backoffice.views.test_opcua_connection")
    def test_opcua_test_connection_forwards_node_list(self, mock_test_opcua_connection):
        mock_test_opcua_connection.return_value = ConnectionTestResult(
            True,
            "成功连接 OPC UA，节点读取结果（按配置顺序）：\n1. A=1\n2. B=2",
        )

        response = self.client.post(
            "/api/admin/data-source-configs/test-connection",
            {
                "sourceType": "opcua",
                "connectionConfig": {
                    "endpointUrl": "opc.tcp://192.168.32.61:4840",
                    "username": "OpcUaClient",
                    "password": "secret",
                },
                "node": [
                    {
                        "nodeId": "ns=2;s=/Channel/State/chanStatus",
                        "comment": "机床运行状态",
                    },
                    {
                        "nodeId": "ns=2;s=/Channel/State/chanAlarm",
                        "comment": "机床报警状态",
                    },
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        mock_test_opcua_connection.assert_called_once_with(
            {
                "endpointUrl": "opc.tcp://192.168.32.61:4840",
                "username": "OpcUaClient",
                "password": "secret",
            },
            node=[
                {
                    "nodeId": "ns=2;s=/Channel/State/chanStatus",
                    "comment": "机床运行状态",
                },
                {
                    "nodeId": "ns=2;s=/Channel/State/chanAlarm",
                    "comment": "机床报警状态",
                },
            ],
        )
        self.assertIn("节点读取结果", response.data["data"]["message"])

    def test_operation_logs_record_admin_actions(self):
        self.client.post("/api/admin/areas", {"code": "A02", "name": "测试区"}, format="json")
        response = self.client.get("/api/admin/operation-logs?page=1&pageSize=10")

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data["data"]["total"], 1)
        self.assertEqual(response.data["data"]["page"], 1)
        self.assertEqual(response.data["data"]["pageSize"], 10)
        self.assertTrue(OperationLog.objects.filter(action="CREATE", target_type="area").exists())

    def test_screen_left_api_returns_mock_snapshot_payload(self):
        area = Area.objects.create(code="A-SCREEN-L", name="总装区", is_active=True)
        line = ProductionLine.objects.create(code="L-SCREEN-L", name="左屏线", area=area, is_active=True)
        Device.objects.create(
            code="D-SCREEN-L",
            name="左屏设备",
            ip="10.0.0.1",
            area=area,
            production_line=line,
            default_status=Device.STATUS_RUNNING,
            is_active=True,
        )
        load_mock_display_data()

        response = self.client.get("/api/screens/A-SCREEN-L/left")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["screen"]["screenKey"], "left")
        self.assertIn("deviceOverview", response.data["data"]["content"])
        self.assertIn("productionOverview", response.data["data"]["content"])
        self.assertIn("energyOverview", response.data["data"]["content"])
        self.assertIn("deviceRealtimeMonitor", response.data["data"]["content"])
        device_overview = response.data["data"]["content"]["deviceOverview"]
        self.assertEqual(
            device_overview["display"],
            {
                "sourceUpdatedAtLabel": parse_datetime(device_overview["sourceUpdatedAt"]).astimezone().strftime("%Y-%m-%d %H:%M:%S"),
                "totalCountLabel": "1",
                "runningCountLabel": "1",
                "abnormalCountLabel": "0",
            },
        )
        po_display = response.data["data"]["content"]["productionOverview"]["display"]
        self.assertEqual(po_display["overallCompletionRateLabel"], "86.01%")
        self.assertEqual(po_display["totalTargetQuantityLabel"], "10720")
        self.assertEqual(po_display["totalProducedQuantityLabel"], "9220")
        self.assertIn("产线台账", po_display["dataSourceNote"])
        self.assertEqual(response.data["data"]["content"]["productionOverview"]["ledgerProductionLineCount"], 1)
        self.assertEqual(response.data["data"]["content"]["productionOverview"]["productionMetricsSource"], "snapshot")
        self.assertEqual(len(response.data["data"]["content"]["productionOverview"]["lineSummaries"]), 8)
        self.assertEqual(
            response.data["data"]["content"]["productionOverview"]["lineSummaries"][0]["display"],
            {
                "currentOrderLabel": "当前订单 MO-001",
                "targetQuantityLabel": "目标 920",
                "producedQuantityLabel": "已产 785",
                "completionRateLabel": "85.33%",
                "plannedRangeLabel": f"{parse_datetime(response.data['data']['content']['productionOverview']['lineSummaries'][0]['plannedStartAt']).astimezone().strftime('%Y-%m-%d')} - {parse_datetime(response.data['data']['content']['productionOverview']['lineSummaries'][0]['plannedEndAt']).astimezone().strftime('%Y-%m-%d')}",
                "estimatedCompletionLabel": parse_datetime(response.data["data"]["content"]["productionOverview"]["lineSummaries"][0]["estimatedCompletionAt"]).astimezone().strftime("%Y-%m-%d"),
                "progressAccent": "blue",
            },
        )
        self.assertTrue(
            any(
                item["display"]["progressAccent"] == "red" and item["isDelayed"] is True
                for item in response.data["data"]["content"]["productionOverview"]["lineSummaries"]
            )
        )
        self.assertEqual(
            response.data["data"]["content"]["energyOverview"]["display"],
            {
                "totalConsumptionLabel": "545.00 kWh",
            },
        )
        self.assertEqual(len(response.data["data"]["content"]["energyOverview"]["areaSummaries"]), 1)
        self.assertEqual(
            response.data["data"]["content"]["energyOverview"]["areaSummaries"][0]["display"],
            {
                "consumptionLabel": "545.00 kWh",
            },
        )
        self.assertIn("pollIntervalSeconds", response.data["data"]["content"]["deviceRealtimeMonitor"])
        self.assertIn("cards", response.data["data"]["content"]["deviceRealtimeMonitor"])
        self.assertEqual(
            response.data["data"]["content"]["productionTrend"][0]["display"],
            {
                "timeLabel": response.data["data"]["content"]["productionTrend"][0]["hourLabel"],
                "producedQuantityLabel": "80",
            },
        )
        self.assertEqual(
            response.data["data"]["content"]["deviceOverview"]["statusItems"],
            [
                {"key": "running", "label": "运行", "accent": "green", "count": 1, "countLabel": "1"},
                {"key": "stopped", "label": "停机", "accent": "amber", "count": 0, "countLabel": "0"},
                {"key": "alarm", "label": "报警", "accent": "red", "count": 0, "countLabel": "0"},
                {"key": "offline", "label": "离线", "accent": "muted", "count": 0, "countLabel": "0"},
            ],
        )
        self.assertEqual(
            response.data["data"]["content"]["repairPlaceholder"]["description"],
            "当前阶段仅保留展示位置，不作为一期前段阻塞项。",
        )
        self.assertIsNotNone(response.data["data"]["meta"]["lastSuccessfulAt"])
        self.assertEqual(
            response.data["data"]["meta"]["display"],
            {
                "lastSuccessfulAtLabel": parse_datetime(response.data["data"]["meta"]["lastSuccessfulAt"]).astimezone().strftime("%Y-%m-%d %H:%M:%S"),
            },
        )
        self.assertFalse(response.data["data"]["meta"]["usingFallback"])

    def test_screen_right_api_keeps_last_successful_data_when_failure_occurs(self):
        area = Area.objects.create(code="A-SCREEN-R", name="总装区", is_active=True)
        for index in range(1, 13):
            ProductionLine.objects.create(
                code=f"L-SCREEN-R-{index:02d}",
                name=f"右屏线 {index:02d}",
                area=area,
                is_active=True,
            )
        initial_result = load_mock_display_data()
        initial_generated_at = initial_result["snapshots"]["schedule"]["generatedAt"]

        load_mock_display_data(simulate_failure=True)
        response = self.client.get("/api/screens/A-SCREEN-R/right")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["screen"]["screenKey"], "right")
        schedule = response.data["data"]["content"]["schedule"]
        line_schedules = schedule["lineSchedules"]
        first_line = line_schedules[0]
        first_order = first_line["orders"][0]
        total_orders = sum(len(line["orders"]) for line in line_schedules)
        risk_display_map = {
            "normal": {"riskLabel": "正常", "riskAccent": "green"},
            "warning": {"riskLabel": "风险", "riskAccent": "amber"},
            "delayed": {"riskLabel": "延期", "riskAccent": "red"},
            "paused": {"riskLabel": "暂停", "riskAccent": "muted"},
        }

        self.assertGreater(len(line_schedules), schedule["autoScrollRowsThreshold"])
        self.assertTrue(schedule["autoScrollEnabled"])
        self.assertEqual(first_order["orderCode"], "PLAN-001-1")
        self.assertEqual(first_line["areaName"], "总装区")
        self.assertEqual(
            first_order["display"],
            {
                **risk_display_map[first_order["riskStatus"]],
                "timeRangeLabel": f"{first_order['displayStartAt']} 至 {first_order['displayEndAt']}",
                "completionRateLabel": f"{first_order['completionRate']}%",
            },
        )
        self.assertEqual(
            schedule["display"],
            {
                "windowDaysLabel": "时间跨度30天",
            },
        )
        risk_summary_items = schedule["riskSummary"]["items"]
        self.assertEqual(sum(item["count"] for item in risk_summary_items), total_orders)
        self.assertTrue(any(item["key"] == "delayed" and item["count"] > 0 for item in risk_summary_items))
        self.assertTrue(any(item["key"] == "paused" and item["count"] > 0 for item in risk_summary_items))
        self.assertEqual(
            response.data["data"]["content"]["simulationPlaceholder"]["description"],
            "当前阶段只保留预留区，优先级低于一期前段核心展示链路。",
        )
        self.assertTrue(response.data["data"]["meta"]["usingFallback"])
        self.assertEqual(
            parse_datetime(response.data["data"]["meta"]["lastSuccessfulAt"]),
            parse_datetime(initial_generated_at),
        )
        self.assertEqual(
            response.data["data"]["meta"]["display"],
            {
                "lastSuccessfulAtLabel": parse_datetime(response.data["data"]["meta"]["lastSuccessfulAt"]).astimezone().strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

    def test_screen_right_uses_mysql_gantt_when_db003_and_query_ok(self):
        area = Area.objects.create(code="A-GANTT-MYSQL", name="测试区", is_active=True)
        ProductionLine.objects.create(code="LINE-GANTT-01", name="测试线", area=area, is_active=True)
        DataSourceConfig.objects.create(
            code="DB_003",
            name="GunT DB",
            source_type="database",
            connection_config={
                "host": "127.0.0.1",
                "port": 3306,
                "database": "test",
                "username": "u",
                "password": "p",
            },
            is_enabled=True,
        )
        load_mock_display_data()
        fake_order = {
            "orderCode": "MOCK-SO-001",
            "materialCode": "MAT-X",
            "materialName": "示例物料",
            "status": "进行中",
            "riskStatus": "normal",
            "targetQuantity": 100,
            "producedQuantity": 10,
            "plannedStartAt": "2026-05-10T08:00:00",
            "plannedEndAt": "2026-05-15T08:00:00",
            "displayStartAt": "2026-05-10",
            "displayEndAt": "2026-05-15",
            "completionRate": 10.0,
            "display": {
                "riskLabel": "正常",
                "riskAccent": "green",
                "timeRangeLabel": "2026-05-10 至 2026-05-15",
                "completionRateLabel": "10.0%",
            },
        }
        with patch("backoffice.schedule_mysql_source.fetch_mysql_schedule_orders_by_line_codes") as mock_fetch:
            mock_fetch.return_value = {"LINE-GANTT-01": [fake_order]}
            payload = get_screen_payload("right", area.code)
        schedule = payload["content"]["schedule"]
        lines = schedule["lineSchedules"]
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["lineCode"], "LINE-GANTT-01")
        self.assertEqual(lines[0]["orders"][0]["orderCode"], "MOCK-SO-001")
        mock_fetch.assert_called_once()

    def test_screen_right_excludes_mysql_orders_with_completion_rate_at_least_100(self):
        area = Area.objects.create(code="A-GANTT-FILTER", name="过滤区", is_active=True)
        ProductionLine.objects.create(code="LINE-GANTT-FILTER", name="过滤线", area=area, is_active=True)
        DataSourceConfig.objects.create(
            code="DB_003",
            name="GunT DB",
            source_type="database",
            connection_config={
                "host": "127.0.0.1",
                "port": 3306,
                "database": "test",
                "username": "u",
                "password": "p",
            },
            is_enabled=True,
        )
        load_mock_display_data()
        open_order = {
            "orderCode": "MOCK-OPEN",
            "materialCode": "MAT-A",
            "materialName": "在制",
            "status": "进行中",
            "riskStatus": "normal",
            "targetQuantity": 100,
            "producedQuantity": 50,
            "plannedStartAt": "2026-05-10T08:00:00",
            "plannedEndAt": "2026-05-15T08:00:00",
            "displayStartAt": "2026-05-10",
            "displayEndAt": "2026-05-15",
            "completionRate": 50.0,
            "display": {},
        }
        dirty_done = {
            "orderCode": "MOCK-DIRTY-DONE",
            "materialCode": "MAT-B",
            "materialName": "脏完工",
            "status": "进行中",
            "riskStatus": "normal",
            "targetQuantity": 100,
            "producedQuantity": 100,
            "plannedStartAt": "2026-05-01T08:00:00",
            "plannedEndAt": "2026-05-02T08:00:00",
            "displayStartAt": "2026-05-01",
            "displayEndAt": "2026-05-02",
            "completionRate": 100.0,
            "display": {},
        }
        with patch("backoffice.schedule_mysql_source.fetch_mysql_schedule_orders_by_line_codes") as mock_fetch:
            mock_fetch.return_value = {"LINE-GANTT-FILTER": [dirty_done, open_order]}
            payload = get_screen_payload("right", area.code)
        orders = payload["content"]["schedule"]["lineSchedules"][0]["orders"]
        self.assertEqual([o["orderCode"] for o in orders], ["MOCK-OPEN"])

    def test_admin_can_view_data_source_health_snapshots(self):
        load_mock_display_data()
        response = self.client.get("/api/admin/data-source-healths")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["total"], 4)
        self.assertEqual(response.data["data"]["items"][0]["status"], "healthy")

    def test_admin_data_source_health_endpoint_bootstraps_mock_snapshots(self):
        response = self.client.get("/api/admin/data-source-healths")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["total"], 4)

    def test_screen_left_api_falls_back_when_display_content_text_is_question_marks(self):
        area = Area.objects.create(code="A-SCREEN-Q", name="总装区", is_active=True)
        ProductionLine.objects.create(code="L-SCREEN-Q", name="问号线", area=area, is_active=True)
        DisplayContentConfig.objects.create(
            config_key="default",
            company_name="????",
            welcome_message="????????",
            logo_url="",
            promo_image_urls=[],
            is_active=True,
        )

        load_mock_display_data()
        response = self.client.get("/api/screens/A-SCREEN-Q/left")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["data"]["content"]["welcome"]["companyName"],
            DEFAULT_DISPLAY_CONTENT["companyName"],
        )
        self.assertEqual(
            response.data["data"]["content"]["welcome"]["welcomeMessage"],
            DEFAULT_DISPLAY_CONTENT["welcomeMessage"],
        )

    def test_delete_area_blocked_when_production_line_references_it(self):
        area = self.client.post(
            "/api/admin/areas",
            {"code": "A-DEL-1", "name": "待删区域", "isActive": True},
            format="json",
        ).data["data"]
        self.client.post(
            "/api/admin/production-lines",
            {"code": "L-DEL-1", "name": "关联产线", "areaId": area["id"], "isActive": True},
            format="json",
        )
        delete_response = self.client.delete(f"/api/admin/areas/{area['id']}")
        self.assertEqual(delete_response.status_code, 409)
        self.assertEqual(delete_response.data["code"], "CONFLICT")
        self.assertIn("protectedObjects", delete_response.data["data"])

    def test_delete_area_allowed_after_clearing_line_reference(self):
        area = self.client.post(
            "/api/admin/areas",
            {"code": "A-DEL-2", "name": "待删区域二", "isActive": True},
            format="json",
        ).data["data"]
        line = self.client.post(
            "/api/admin/production-lines",
            {"code": "L-DEL-2", "name": "产线二", "areaId": area["id"], "isActive": True},
            format="json",
        ).data["data"]
        clear = self.client.patch(
            f"/api/admin/production-lines/{line['id']}",
            {"areaId": None},
            format="json",
        )
        self.assertEqual(clear.status_code, 200)
        delete_response = self.client.delete(f"/api/admin/areas/{area['id']}")
        self.assertEqual(delete_response.status_code, 200)

    def test_delete_production_line_blocked_when_device_references_it(self):
        area = self.client.post(
            "/api/admin/areas",
            {"code": "A-DEL-3", "name": "区域三", "isActive": True},
            format="json",
        ).data["data"]
        line = self.client.post(
            "/api/admin/production-lines",
            {"code": "L-DEL-3", "name": "产线三", "areaId": area["id"], "isActive": True},
            format="json",
        ).data["data"]
        self.client.post(
            "/api/admin/devices",
            {
                "code": "D-DEL-3",
                "name": "设备三",
                "productionLineId": line["id"],
                "defaultStatus": "stopped",
                "isActive": True,
            },
            format="json",
        )
        delete_response = self.client.delete(f"/api/admin/production-lines/{line['id']}")
        self.assertEqual(delete_response.status_code, 409)
        self.assertEqual(delete_response.data["code"], "CONFLICT")


    def test_material_crud(self):
        create = self.client.post(
            "/api/admin/materials",
            {"code": "MAT-001", "name": "铝合金壳体", "specification": "200x100x50mm", "unit": "件", "isActive": True},
            format="json",
        )
        self.assertEqual(create.status_code, 201)
        mat_id = create.data["data"]["id"]
        self.assertEqual(create.data["data"]["code"], "MAT-001")

        detail = self.client.get(f"/api/admin/materials/{mat_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["data"]["specification"], "200x100x50mm")

        update = self.client.patch(
            f"/api/admin/materials/{mat_id}",
            {"specification": "300x150x60mm"},
            format="json",
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.data["data"]["specification"], "300x150x60mm")

        list_resp = self.client.get("/api/admin/materials")
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(list_resp.data["data"]["total"], 1)

    def test_order_crud_with_material_and_line(self):
        mat = self.client.post(
            "/api/admin/materials",
            {"code": "MAT-ORD", "name": "测试物料", "isActive": True},
            format="json",
        ).data["data"]

        area = self.client.post(
            "/api/admin/areas",
            {"code": "A-ORD", "name": "订单区域", "isActive": True},
            format="json",
        ).data["data"]

        line = self.client.post(
            "/api/admin/production-lines",
            {"code": "L-ORD", "name": "订单产线", "areaId": area["id"], "isActive": True},
            format="json",
        ).data["data"]

        create = self.client.post(
            "/api/admin/orders",
            {
                "orderNo": "SO-2025-0001",
                "materialId": mat["id"],
                "productionLineId": line["id"],
                "quantity": "1000.00",
                "completedQuantity": "0.00",
                "unit": "件",
                "status": "planned",
                "plannedStart": "2025-07-01T08:00:00Z",
                "plannedEnd": "2025-07-15T18:00:00Z",
                "isActive": True,
            },
            format="json",
        )
        self.assertEqual(create.status_code, 201)
        self.assertEqual(create.data["data"]["orderNo"], "SO-2025-0001")
        self.assertEqual(create.data["data"]["materialName"], "测试物料")
        self.assertEqual(create.data["data"]["productionLineName"], "订单产线")
        self.assertEqual(create.data["data"]["statusLabel"], "计划")

        order_id = create.data["data"]["id"]
        update = self.client.patch(
            f"/api/admin/orders/{order_id}",
            {"status": "in_progress", "completedQuantity": "250.00"},
            format="json",
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.data["data"]["statusLabel"], "生产中")

        list_resp = self.client.get("/api/admin/orders")
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(list_resp.data["data"]["total"], 1)

    def test_delete_material_blocked_when_order_references_it(self):
        mat = self.client.post(
            "/api/admin/materials",
            {"code": "MAT-DEL", "name": "受保护物料", "isActive": True},
            format="json",
        ).data["data"]
        self.client.post(
            "/api/admin/orders",
            {"orderNo": "SO-DEL-1", "materialId": mat["id"], "quantity": "100", "status": "planned"},
            format="json",
        )
        delete_resp = self.client.delete(f"/api/admin/materials/{mat['id']}")
        self.assertEqual(delete_resp.status_code, 409)
        self.assertEqual(delete_resp.data["code"], "CONFLICT")

    def test_page_module_switch_crud(self):
        create = self.client.post(
            "/api/admin/page-module-switches",
            {
                "screenKey": "left",
                "moduleKey": "device_overview",
                "label": "设备运行概览",
                "isEnabled": True,
                "sortOrder": 1,
            },
            format="json",
        )
        self.assertEqual(create.status_code, 201)
        self.assertEqual(create.data["data"]["screenKey"], "left")
        self.assertEqual(create.data["data"]["moduleKey"], "device_overview")

        switch_id = create.data["data"]["id"]
        update = self.client.patch(
            f"/api/admin/page-module-switches/{switch_id}",
            {"isEnabled": False},
            format="json",
        )
        self.assertEqual(update.status_code, 200)
        self.assertFalse(update.data["data"]["isEnabled"])

        list_resp = self.client.get("/api/admin/page-module-switches?screen_key=left")
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(list_resp.data["data"]["total"], 1)

    def test_page_module_switch_unique_constraint(self):
        self.client.post(
            "/api/admin/page-module-switches",
            {"screenKey": "right", "moduleKey": "gantt_chart", "label": "甘特图", "sortOrder": 0},
            format="json",
        )
        dup = self.client.post(
            "/api/admin/page-module-switches",
            {"screenKey": "right", "moduleKey": "gantt_chart", "label": "甘特图重复", "sortOrder": 1},
            format="json",
        )
        self.assertEqual(dup.status_code, 400)

    def test_screen_page_binding_crud(self):
        create = self.client.post(
            "/api/admin/screen-page-bindings",
            {
                "screenKey": "left",
                "pageKey": "energy",
                "bindingSourceType": "",
                "dataSourceIds": [],
                "deviceIds": [],
                "isEnabled": True,
            },
            format="json",
        )
        self.assertEqual(create.status_code, 201)
        self.assertEqual(create.data["data"]["pageKey"], "energy")
        self.assertEqual(create.data["data"]["pageKeyLabel"], "能耗数据")

    def test_screen_page_binding_rejects_mismatched_screen_page(self):
        bad = self.client.post(
            "/api/admin/screen-page-bindings",
            {
                "screenKey": "left",
                "pageKey": "schedule",
            },
            format="json",
        )
        self.assertEqual(bad.status_code, 400)


class AreaLineDeviceCascadeTests(TestCase):
    def test_area_deactivate_cascades_to_lines_and_devices(self):
        area = Area.objects.create(code="CA1", name="区域一", is_active=True)
        line = ProductionLine.objects.create(code="CL1", name="产线一", area=area, is_active=True)
        device = Device.objects.create(
            code="CD1",
            name="设备一",
            area=area,
            production_line=line,
            is_active=True,
        )
        area.is_active = False
        area.save()
        line.refresh_from_db()
        device.refresh_from_db()
        self.assertFalse(line.is_active)
        self.assertFalse(device.is_active)

    def test_production_line_area_change_updates_device_area(self):
        area_a = Area.objects.create(code="CA2", name="区域甲", is_active=True)
        area_b = Area.objects.create(code="CA3", name="区域乙", is_active=True)
        line = ProductionLine.objects.create(code="CL2", name="产线二", area=area_a, is_active=True)
        device = Device.objects.create(
            code="CD2",
            name="设备二",
            area=area_a,
            production_line=line,
            is_active=True,
        )
        line.area = area_b
        line.save()
        device.refresh_from_db()
        self.assertEqual(device.area_id, area_b.id)

    def test_production_line_deactivate_cascades_to_devices(self):
        area = Area.objects.create(code="CA4", name="区域四", is_active=True)
        line = ProductionLine.objects.create(code="CL4", name="产线四", area=area, is_active=True)
        device = Device.objects.create(
            code="CD4",
            name="设备四",
            area=area,
            production_line=line,
            is_active=True,
        )
        line.is_active = False
        line.save()
        device.refresh_from_db()
        self.assertFalse(device.is_active)

    def test_device_inherits_area_from_production_line(self):
        area = Area.objects.create(code="CA5", name="区域五", is_active=True)
        line = ProductionLine.objects.create(code="CL5", name="产线五", area=area, is_active=True)
        device = Device(code="CD5", name="设备五", production_line=line)
        device.save()
        self.assertEqual(device.area_id, area.id)


class TkRuntimeValueMappingTests(TestCase):
    def test_prog_status_maps_per_tk_md(self):
        path = "/Channel/State/progStatus[u1]"
        self.assertEqual(_map_runtime_status_display(path, 3), "运行")
        self.assertEqual(_map_runtime_status_display(path, "3"), "运行")

    def test_op_mode_maps(self):
        path = "/Bag/State/opMode[u1]"
        self.assertEqual(_map_runtime_status_display(path, 2), "AUTO自动")

    def test_axis_status_maps(self):
        path = "/Nck/MachineAxis/status[1]"
        self.assertEqual(_map_runtime_status_display(path, 0), "正向移动")

    def test_indexed_path_still_matches_prefix(self):
        self.assertEqual(
            _map_runtime_status_display("/Channel/State/progStatus[u2]", 1),
            "中断",
        )

    def test_unknown_enum_code_passthrough(self):
        self.assertEqual(_map_runtime_status_display("/Channel/State/progStatus[u1]", 99), "99")

    def test_display_parameter_value_runtime_group(self):
        nid = "ns=2;s=/Channel/State/progStatus[u1]"
        self.assertEqual(_display_parameter_value(nid, "runtime", True, 3), "运行")

    def test_display_parameter_value_non_runtime_unchanged(self):
        nid = "ns=2;s=/Channel/Spindle/cmdSpeed[u1, 1]"
        self.assertEqual(_display_parameter_value(nid, "speed", True, 1500.0), 1500.0)


class CncDashboardHelpersTests(TestCase):
    def test_format_seconds_hms(self):
        self.assertEqual(_format_seconds_hms(3661), "01:01:01")
        self.assertEqual(_format_seconds_hms("45"), "00:00:45")

    def test_machine_panel_status_rules(self):
        self.assertEqual(_resolve_machine_panel_status(True, 3, 0)["code"], "offline")
        self.assertEqual(_resolve_machine_panel_status(False, 3, 1)["code"], "alarm")
        self.assertEqual(_resolve_machine_panel_status(False, 3, 0)["code"], "running")
        self.assertEqual(_resolve_machine_panel_status(False, 2, 0)["code"], "standby")
        self.assertEqual(_resolve_machine_panel_status(False, 1, 0)["code"], "alarm")
        self.assertEqual(_resolve_machine_panel_status(False, 5, 0)["code"], "alarm")


class ScheduleGanttAnchorModeTests(TestCase):
    def test_normalize_gantt_anchor_mode_aliases(self):
        self.assertEqual(_normalize_gantt_anchor_mode(None), "earliest_order")
        self.assertEqual(_normalize_gantt_anchor_mode(""), "earliest_order")
        self.assertEqual(_normalize_gantt_anchor_mode("currentTime"), "current_time")
        self.assertEqual(_normalize_gantt_anchor_mode("earliestOrder"), "earliest_order")
        self.assertEqual(_normalize_gantt_anchor_mode("bogus"), "earliest_order")

    def test_compute_anchor_current_time_uses_local_today(self):
        line_schedules = [{"orders": [{"displayStartAt": "2020-01-05"}]}]
        with patch("backoffice.display_services.timezone.localdate", return_value=date(2026, 5, 10)):
            self.assertEqual(
                _compute_schedule_window_anchor(line_schedules, "current_time"),
                date(2026, 5, 10),
            )

    def test_compute_anchor_earliest_order_uses_min_start(self):
        line_schedules = [
            {"orders": [{"displayStartAt": "2021-03-01"}, {"displayStartAt": "2020-01-05"}]},
        ]
        self.assertEqual(
            _compute_schedule_window_anchor(line_schedules, "earliest_order"),
            date(2020, 1, 5),
        )

    def test_screen_schedule_payload_includes_gantt_anchor_mode(self):
        area = Area.objects.create(code="A-GANTT-MODE", name="锚点测试区", is_active=True)
        ProductionLine.objects.create(code="L-GANTT-MODE", name="线", area=area, is_active=True)
        load_mock_display_data()
        payload = get_screen_payload("right", area.code)
        schedule = payload["content"]["schedule"]
        self.assertIn(schedule["ganttAnchorMode"], ("earliest_order", "current_time"))
