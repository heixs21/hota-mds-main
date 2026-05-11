# 数据真实性说明（真实接入 vs Mock / 占位）

本文档描述**当前代码行为**：哪些大屏与后台能力已接外部或实时数据，哪些仍依赖本库快照、mock 装载或纯占位文案。部署环境未配置数据源时，多数模块会走兜底路径（快照/mock），与「未接真实库」表现一致。

**相关实现入口**：大屏载荷 `backend/backoffice/display_services.py::get_screen_payload`；左屏产量概览从排产库汇总 `_try_build_left_production_overview_from_schedule_db`；排产 MySQL `backend/backoffice/schedule_mysql_source.py`；能耗看板 `backend/backoffice/energy_dashboard_services.py`；能耗子页前端 `frontend/src/EnergyDashboardBoard.jsx`（请求 `/api/energy-dashboard`）。左屏 `productionOverview.productionMetricsSource` 为 `schedule_database` 时表示当前为排产库真实汇总，为 `snapshot` 时表示回退产量快照。

---

## 1. 总览表

| 能力 | 真实/外部数据 | 说明 |
|------|----------------|------|
| 后台管理（台账、配置、日志） | **本库真实数据** | 区域、产线、设备、编码映射、屏配置、数据源配置等均落库；本地可用 SQLite 测试设置，生产为 MySQL。 |
| 大屏欢迎语 / Logo / 宣传图 | **本库配置** | 来自激活的展示内容配置，非外部 ERP。 |
| 设备运行概览（左屏） | **半真实** | 设备数量与状态来自本库 `Device` 表；运行/停机由后台按数据源**连通性探测**周期性刷新 `default_status`（简化逻辑，非 OPC 全量工况）。时间类展示字段仍带快照辅助字段。 |
| 产量执行概览（左屏） | **条件真实** | 与右屏甘特同源：在 `_resolve_schedule_data_source` 能解析到排产 **database** 数据源（`schedule` 子页绑定或启用编码 `DB_003`）且 MySQL 查询成功时，按产线汇总外部工单（`_try_build_left_production_overview_from_schedule_db`）。失败或未配置则回退 **`ProductionSnapshot`**（mock/`load_mock_screen_data`）。 |
| 近 8 小时产量趋势 | **默认 Mock / 快照** | 仍读取 `ProductionSnapshot.trend_points`，仅由 mock 装载写入；**与产量概览数据源解耦**，尚未接外部产量曲线。 |
| 区域能耗概览（左屏嵌入卡片） | **默认 Mock / 快照** | `EnergySnapshot` 同样主要来自 mock 装载；**与下方「能耗数据子页」的外联能耗库不是同一条链路**。 |
| 报修占位区 | **占位** | 仅展示预留文案，不接报修系统。 |
| 右屏甘特排产 | **条件真实** | 若右屏子页面绑定了 **database 类型**排产数据源，或存在启用且编码为 `DB_003` 的数据库源，则查询外部 MySQL（`orders`/`machines` 等，见 `schedule_mysql_source`）。查询失败或未配置则 **回退 `ScheduleSnapshot`（mock）**。 |
| 延期风险汇总数字 | **随甘特数据源** | `riskSummary.counts` 由当前合并后的 `lineSchedules` 计算；图例 `delayLegend` 仍带快照中的图例项结构。 |
| 3D 仿真区 | **占位** | 仅预留区域与说明文案。 |
| 设备实时监控页（左屏 `realtime`） | **条件真实** | 对绑定 OPC UA 数据源按节点列表**实时读取**（需运行环境可用 OPC UA 客户端库）。连接失败则卡片离线展示。 |
| 能耗数据子页（左屏 `energy`） | **条件真实** | 前端 `POST /api/energy-dashboard`，后端可连**外部能耗 MySQL**（`energy_dashboard_services`），并支持快照缓存与定时同步命令 `sync_energy_dashboard_snapshots`。**依赖后台为「能耗」子页绑定能耗库数据源**。 |
| Collector 服务 | **占位** | `collector/src/main.py` 仅为心跳循环，**未接入任何外部系统**。 |

---

## 2. 按大屏模块细分

### 2.1 左屏综合页（overview / operations 等）

- **设备运行概览**：台账 + 数据源探测结果 → **可反映现场连接配置，但不是 OPC 原始点表明细。**
- **产量执行概览**：排产库可用时为真实工单汇总；否则为快照演示数据。
- **趋势图**：仍为快照/mock（非排产库）。
- **嵌入的区域能耗**：快照/mock（勿与能耗子页混淆）。

### 2.2 左屏「设备实时监控」(`realtime`)

- **真实**：OPC UA 节点轮询（分组展示、基础信息节点排除策略等由后端组装）。
- **降级**：库未安装、网络不通、未配置数据源 → 离线/异常卡片。

### 2.3 左屏「能耗数据」(`energy`)

- **真实**：配置能耗数据库数据源后，`EnergyDashboardBoard` 拉取 `/api/energy-dashboard` 全量看板数据（表树、汇总、曲线等来自外部库字段映射）。
- **兜底**：无缓存且禁止直连时可能返回错误提示；需同步任务或 `forceRefresh` 等行为见 `energy_dashboard_services`。

### 2.4 右屏排产（`schedule`）

- **真实**：MySQL 排产库与产线编码对齐成功时，甘特条为外部订单数据。
- **Mock**：无数据源或查询异常 → 使用库内 `ScheduleSnapshot`（由 `load_mock_screen_data` 生成）。

### 2.5 右屏 3D 仿真（`simulation`）

- **占位**：固定「一期后段接入」类说明，无 3D 渲染与数据。

---

## 3. 配置与验证提示

1. **Mock 基线**：`python manage.py load_mock_screen_data` 可一次性填满四类展示快照与健康快照，便于无外部库演示。
2. **右屏真实排产与左屏真实产量概览**：共用同一套排产库解析逻辑（`schedule` 子页绑定或 `DB_003`）；产线台账 `lineCode` 需与外部 `machines.lineCode` 一致。左屏产量卡片在无排产源或查询失败时自动回退快照。
3. **实时监控**：设备绑定 OPC UA 数据源，`node` 列表配置可读节点。
4. **能耗子页**：在屏配置中为 `energy` 子页绑定 `energy_db` 类型数据源；大屏侧「区域能耗」嵌入卡片仍为快照链路，除非后续产品改为同一 API。

---

## 4. 文档关系

- 里程碑表述仍以 `docs/PLAN.md`、`docs/STATUS.md` 为准；本文档仅澄清**实现层面**真实与 mock 边界。
- 接口字段详见 `SCREEN_API.md`、`docs/API_CONTRACT.md`。
