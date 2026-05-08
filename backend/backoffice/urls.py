from rest_framework.routers import DefaultRouter

from .views import (
    AreaViewSet,
    CodeMappingViewSet,
    DataSourceConfigViewSet,
    DataSourceHealthSnapshotViewSet,
    DeviceViewSet,
    EmployeeViewSet,
    DisplayContentConfigViewSet,
    MaterialViewSet,
    OperationLogViewSet,
    OrderViewSet,
    PageModuleSwitchViewSet,
    ProductionLineViewSet,
    RuntimeParameterConfigViewSet,
    ScreenConfigViewSet,
)


router = DefaultRouter(trailing_slash=False)
router.register("areas", AreaViewSet, basename="admin-area")
router.register("production-lines", ProductionLineViewSet, basename="admin-production-line")
router.register("devices", DeviceViewSet, basename="admin-device")
router.register("employees", EmployeeViewSet, basename="admin-employee")
router.register("materials", MaterialViewSet, basename="admin-material")
router.register("orders", OrderViewSet, basename="admin-order")
router.register("code-mappings", CodeMappingViewSet, basename="admin-code-mapping")
router.register("screen-configs", ScreenConfigViewSet, basename="admin-screen-config")
router.register("display-content-configs", DisplayContentConfigViewSet, basename="admin-display-content-config")
router.register("runtime-parameter-configs", RuntimeParameterConfigViewSet, basename="admin-runtime-parameter-config")
router.register("page-module-switches", PageModuleSwitchViewSet, basename="admin-page-module-switch")
router.register("data-source-configs", DataSourceConfigViewSet, basename="admin-data-source-config")
router.register("data-source-healths", DataSourceHealthSnapshotViewSet, basename="admin-data-source-health")
router.register("operation-logs", OperationLogViewSet, basename="admin-operation-log")

urlpatterns = router.urls
