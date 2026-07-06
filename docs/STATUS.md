# 和泰智造数屏系统 STATUS

## 0. 数据接入现状（真实 vs Mock）

已接入或可接入**真实外部/实时数据**的部分：

- 右屏甘特：在配置排产 MySQL 数据源（子页面绑定或 `DB_003`）且查询成功时，使用外部 `orders`/`machines` 数据；失败或未配置则回退快照/mock。
- 左屏产量执行概览：**与右屏共用排产库解析**（同上）；查询成功时为外部工单汇总（接口 `productionMetricsSource=schedule_database`），失败或未配置则回退 `ProductionSnapshot`（`productionMetricsSource=snapshot`）。
- 左屏设备实时监控页：OPC UA 按节点实时读取（依赖环境与数据源配置）。
- 左屏能耗数据子页：`POST /api/energy-dashboard` 对接外部能耗库（含快照缓存与定时同步）；与左屏嵌入的「区域能耗概览」快照链路不同。
- 设备运行概览：基于本库设备台账 + 数据源连通性探测刷新运行/停机计数（简化语义，非全量工况采集）。

仍主要为 **mock / 快照演示数据** 的部分：

- 左屏近 8 小时产量趋势（仍读 `ProductionSnapshot.trend_points`，未接外部曲线）。
- 左屏嵌入的区域能耗概览（`EnergySnapshot`，主要由 `load_mock_screen_data` 写入）。
- 未配置排产库或查询失败时的左屏产量概览与右屏甘特。

**纯占位**：报修区、3D 仿真区。**Collector** 仍为心跳占位，未采数。

完整对照表见 **`docs/DATA_REALITY.md`**。

## 1. 当前阶段

当前已完成 M4（一期前段双屏页面与展示链路），并已在代码中实现部分 **M5 向** 的真实接入路径（排产 MySQL、OPC UA 实时监控、能耗看板 API）；是否在生产环境呈现真实数据取决于后台数据源与字段配置是否到位。按 `docs/PLAN.md`，报修与 3D 仍非一期前段阻塞项；未在该文档单独列为「整体验收完成 M5」前，默认仍存在 mock/兜底并存状态。

当前已具备的能力：

- 管理员登录
- 设备台账管理
- 员工台账管理
- 产线台账管理
- 区域台账管理
- 编码映射管理
- 左右屏配置管理
- 数据源配置管理
- 基础操作日志
- 最小后台前端界面
- 设备状态快照缓存
- 产量统计快照缓存
- 排产甘特图快照缓存
- 能耗快照缓存
- 数据源健康状态快照
- mock 数据装载命令
- 左右屏展示 API
- 数据源失败时返回最近一次成功快照
- 左右屏前端展示页
- 前端保留最近一次成功展示内容
- 左右屏按各自配置读取标题、页面顺序、模块开关和轮播秒数
- 左右屏全屏按钮与双击全屏支持
- 右屏未来 30 日窗口排产甘特图
- 右屏排产超量时自动纵向滚动

本阶段要求：

- M4 已完成，一期前段仍只做外部参观双屏大屏。
- 真实接入已部分落地（见上文第 0 节与 `docs/DATA_REALITY.md`）；未配置外部源时行为与 mock 阶段一致。
- 前端仍不得直连外部系统（统一走后端 API）。
- 不实现报修、3D 仿真或内部 Web 报表。
- 前端仍不得直连外部系统。
- 左屏产量概览已与排产库打通（见第 0 节）；近 8 小时趋势与嵌入能耗快照仍以 mock/快照为主，完整 M5 产量曲线与能耗快照自动化采集待对接。

## 2. 已知信息

### 2.1 产品范围

- 一期前段为外部客户参观大屏。
- 一期前段核心验收为设备、产量、排产、能耗稳定展示。
- 报修系统接入放到一期后段。
- 3D 仿真放到一期后段低优先级，优先级低于报修。
- 内部 Web 报表作为二期项目。

### 2.2 页面与流程

- 左右双屏分别使用独立 URL。
- 左右屏需要分别配置内容和轮播策略。
- 默认轮播时间为 60 秒，可后台配置。
- 报修未接入前显示占位。
- 3D 仿真未实施前显示预留区或占位。

### 2.3 数据接入

一期前段必须真实接入：

- 设备数据。
- 产量数据。
- 排产数据。
- 能耗数据。

接入方式：

- 后端定时拉取并缓存。
- 前端不直接访问外部系统。
- 默认刷新频率 5 分钟，可后台配置。
- 当前点表和外部数据库结构正在整理，暂时无法提供。
- 允许先做标准数据模型、mock 数据与适配器接口。

### 2.4 编码策略

- 本系统自建主数据编码。
- 外部系统编码映射到本系统主编码。

### 2.5 延期预测

- 不考虑班次、非工作时间、计划停机、换型时间。
- 仅支持后台配置单日有效工作时间。

### 2.6 权限

- 后台需要登录。
- 一期不做复杂角色拆分。
- 默认管理员拥有全部配置能力。

### 2.7 异常策略

- 大屏显示最近一次成功数据。
- 大屏不提示数据过期。
- 后台提示数据源健康状态和数据过期状态。

### 2.8 部署

- Ubuntu。
- Docker。
- MySQL 独立部署。
- 服务拆分为 backend、frontend/nginx、collector。

### 2.9 数据保留

- 数据库历史数据要求永久保留。

## 3. 未确认事项

- 一个订单是否绝对不会同时分配到多条产线。
- OPCUA / Modbus 点表。
- SAP RFC 字段和连接方式。
- 排产系统数据库表结构。
- 能耗数据库表结构。
- 报修系统最终接入方式。
- WMS 是否进入一期真实接入。
- 后台连接信息加密方案。
- 拼接屏实际分辨率和浏览器运行环境。

## 4. 当前优先级

P0：

- 一期前段范围固化。
- 标准数据模型。
- API 契约。
- 后端缓存层。
- 左右屏独立 URL。
- 后台基础配置。
- 数据源健康状态。
- 设备、产量、排产、能耗真实接入。

P1：

- 报修系统接入。
- 报修统计展示。
- 报修占位区替换为真实数据。

P2：

- 3D 仿真。
- 3D 模型管理。
- 实时状态联动预留。

P3：

- 内部 Web 报表二期。

## 5. 下一步行动

1. 进入 M5 前置准备或真实数据源接入，但前提仍是外部系统资料到位。
2. 继续保持现有 M4 双屏页面与 M3/M6 mock/cache 兜底逻辑稳定，不做无必要重构。
3. 进入 M5 时只能由后端/collector 负责定时拉取、标准化与缓存，前端仍只依赖标准 API。
4. 报修、3D 仿真和内部 Web 报表继续排除在当前优先级之外。

## 6. 本轮更新记录

- 已新增 `docs/IMPLEMENTATION_PLAN.md`，作为一期前段开发实施 WBS 文档。
- WBS 明确一期前段范围不包含内部 Web 报表。
- WBS 明确报修和 3D 仿真列为后续阶段，不作为一期前段阻塞任务。
- WBS 明确当前可先做任务、必须等待外部系统资料的任务、适合前后端并行的任务。
- WBS 明确甘特图、延期预测、数据源映射为高风险任务。

## 7. 本轮更新记录

- 已新增 `docs/API_CONTRACT.md`，作为一期前段 API 契约草案。
- 已新增 `docs/DB_MODEL_DRAFT.md`，作为一期前段数据模型草案。
- 两份草案均明确前端不得依赖外部系统原始结构，大屏接口应面向标准缓存模型。
- 两份草案均列出了当前可先 mock 的字段、必须等待真实外部系统资料确认的字段，以及需要补充确认的问题。

## 8. 本轮更新记录

- 已完成 M1 工程骨架与基础部署的最小实现。
- backend：新增 Django + DRF 工程骨架，并配置 MySQL 连接参数来自环境变量。
- backend：新增 `/api/health` 健康检查接口，接口会尝试检查数据库连接状态。
- frontend：新增 React 工程骨架，并提供 `/screen/left`、`/screen/right`、`/admin/login` 占位路由。
- collector：新增独立服务目录和占位心跳服务，不连接任何外部系统。
- deploy：新增 `docker-compose.yml`、backend/frontend/collector Dockerfile、`.env.example`。
- README：新增启动说明与基础验证命令。
- 验证结果：Python 语法编译通过，`docker compose config` 通过，`frontend/package.json` JSON 校验通过。
- 验证限制：当前 Docker Desktop/Linux engine 未运行，无法完成容器启动和 `/api/health` 实际访问验证；`npm install` 多次超时，未生成 `node_modules` 或 `package-lock.json`。

## 9. 本轮更新记录

- 已完成 M2 的最小可交付目标：管理员登录能力。
- backend：新增 `accounts` 应用，并提供 `/api/admin/auth/login` 与 `/api/admin/auth/me` 两个接口。
- backend：登录接口仅允许 `is_staff` 管理员账号通过，返回带签名的管理员令牌，不写死任何外部系统连接信息。
- backend：新增基于 SQLite 的 `hota_mds.test_settings`，仅用于本轮自动化测试与本地验证，不改变正式 MySQL 架构约束。
- backend：新增 4 条认证相关测试，覆盖管理员登录成功、非管理员拒绝、未带令牌访问拒绝、获取当前管理员信息。
- frontend：`/admin/login` 从占位页升级为可提交账号密码、保存会话令牌并回读当前管理员信息的最小登录页面。
- frontend：新增 `vite.config.js`，开发环境下将 `/api` 代理到本地 backend，便于前后端联调。
- 验证结果：`python -m compileall backend` 通过；`python manage.py test accounts --settings=hota_mds.test_settings` 4/4 通过；`npm install` 成功并生成 `package-lock.json`；`npm run build` 通过。
- 运行验证：已使用 `hota_mds.test_settings` 完成 `migrate`、创建本地管理员账号，并验证 `POST /api/admin/auth/login` 与 `GET /api/admin/auth/me` 均返回 200。

## 10. 本轮更新记录

- 本轮继续停留在 M2，不进入大屏展示、不接真实数据源。
- backend：新增 `backoffice` 应用，提供区域、产线、设备、编码映射、左右屏配置、数据源配置、操作日志等后台基础模型。
- backend：新增 `/api/admin/areas`、`/api/admin/production-lines`、`/api/admin/devices`、`/api/admin/code-mappings`、`/api/admin/screen-configs`、`/api/admin/data-source-configs`、`/api/admin/operation-logs`。
- backend：所有后台管理接口统一使用管理员 Bearer Token 鉴权，仅允许管理员访问。
- backend：统一后台接口响应包裹格式，并新增异常处理器，保证常见错误返回结构一致。
- backend：数据源配置支持 `env_ref` 与 `encrypted` 两种敏感信息保护结构，不要求把敏感连接信息写死在代码中，也不在接口响应与日志中回显敏感值。
- backend：基础操作日志已记录管理员登录、创建、更新、删除动作，包含目标对象、请求路径、请求方法和变更摘要。
- backend：已新增 `backoffice` 迁移文件 `0001_initial.py`。
- 验证结果：`python manage.py makemigrations backoffice --settings=hota_mds.test_settings` 通过；`python manage.py test accounts backoffice --settings=hota_mds.test_settings` 9/9 通过。
- 冒烟验证：使用 `hota_mds.test_settings` 迁移后，实测管理员登录成功、区域创建成功、操作日志列表可读，结果为 `loginStatus=200`、`areaStatus=201`、`logTotal=2`。

## 11. 本轮更新记录

- 本轮继续停留在 M2，补齐后台参数配置能力，不进入大屏展示、不接真实数据源。
- backend：新增 `DisplayContentConfig`，用于维护公司名称、欢迎语、Logo、宣传图片等欢迎展示内容配置。
- backend：新增 `RuntimeParameterConfig`，用于维护单日有效工作时间、标准产能、延期预警缓冲、甘特窗口天数、自动滚动阈值、产量窗口等运行参数。
- backend：新增 `/api/admin/display-content-configs` 与 `/api/admin/runtime-parameter-configs`。
- backend：`ScreenConfigSerializer` 新增对 `pageKeys`、`moduleSettings`、`themeSettings` 的结构校验，减少后续配置脏数据。
- backend：新增迁移文件 `backoffice/migrations/0002_displaycontentconfig_runtimeparameterconfig.py`。
- backend：自动化测试新增展示内容配置和运行参数配置的创建校验，以及无效工时参数拒绝校验。
- 验证结果：`python manage.py test accounts backoffice --settings=hota_mds.test_settings` 11/11 通过。
- 冒烟验证：使用 `hota_mds.test_settings` 迁移后，实测管理员登录成功、展示内容配置创建成功、运行参数配置创建成功，结果为 `loginStatus=200`、`displayStatus=201`、`runtimeStatus=201`。

## 12. 本轮更新记录

- 本轮在不进入大屏展示和真实数据源接入的前提下，补齐了最基础的后台前端界面。
- frontend：新增 `/admin/console` 最小后台控制台，登录后可直接维护区域、产线、设备、编码映射、左右屏配置、展示内容配置、运行参数配置、数据源配置，并查看操作日志。
- frontend：后台控制台提供资源切换、列表展示、基础新增/编辑/删除表单，以及日志详情查看。
- frontend：登录页保留在 `/admin/login`，管理员登录成功后自动进入 `/admin/console`。
- frontend：控制台直接对接现有 M2 API，继续通过本系统后端访问，不直连任何外部系统。
- frontend：样式从骨架占位页调整为可用的管理界面布局，适配桌面和移动宽度的基本使用。
- 验证结果：`npm run build` 通过；`python manage.py test accounts backoffice --settings=hota_mds.test_settings` 11/11 通过。
- 联调验证：`http://127.0.0.1:3000/admin/console` 返回 200，`http://127.0.0.1:8000/api/health` 返回健康结果。

## 13. 本轮更新记录

- 已新增 `docs/DECISIONS.md`，用于记录开发中“为什么这么做”的技术决策背景。
- 当前已补录的一期关键决策包括：一期范围边界、报修与 3D 的阶段定位、前端不直连外部系统、管理员权限简化、签名 Token 认证、统一 API 响应风格、数据源敏感配置结构预留、M2 先补最小后台界面等。

## 14. 本轮更新记录

- 根据数据库结构审阅意见，已补充员工台账模型、接口和后台前端入口。
- backend：新增员工模型 `Employee`，字段包含 `employee_no`、`name`、`role`、`is_active`、`notes`。
- backend：员工号格式限制为仅允许英文和数字；角色固定为 `employee`、`team_leader`、`supervisor`。
- backend：新增 `/api/admin/employees` 系列接口，并纳入统一管理员鉴权、统一响应结构和操作日志体系。
- frontend：后台控制台新增“员工台账”入口，可直接维护员工号、姓名、角色和启用状态。
- docs：已同步更新 `DECISIONS.md`、`DB_MODEL_DRAFT.md`、`API_CONTRACT.md`，记录员工表补充原因和接口约束。
## 15. 本轮收尾状态

### 当前阶段

- 当前仍处于 M2 收尾阶段。
- M2 最小后台能力已经补齐到管理员可维护台账和配置的程度。
- 本轮在既有 M2 基础上补充了缺失的员工台账，不进入 M3，不接真实数据源，不进入大屏展示。

### 本轮已完成

- 新增员工表 `Employee`，字段包含 `employee_no`、`name`、`role`、`is_active`、`notes`。
- 员工号格式限制为仅允许英文和数字。
- 员工角色固定为 `employee`、`team_leader`、`supervisor`。
- 新增员工台账后台接口 `/api/admin/employees`，纳入现有管理员鉴权、统一响应结构与操作日志。
- 后台最小前端界面增加“员工台账”入口，可新增、编辑、删除员工记录。
- 已同步更新 `API_CONTRACT.md`、`DB_MODEL_DRAFT.md`、`DECISIONS.md`、`HANDOFF.md`。
- 已完成迁移、自动化测试、前端构建和接口冒烟验证。

### 未完成

- 尚未进入 M3 的标准化缓存模型、mock 采集结果和左右屏展示 API。
- 尚未接入任何真实外部系统。
- 尚未实现大屏展示链路中的“最近一次成功数据兜底”运行态能力。
- 尚未实现员工与部门、班组、用户账号之间的扩展关系。

### 当前已知问题

- 当前生产数据库仍未实际联调，验证主要基于 `hota_mds.test_settings` 与本地测试链路完成。
- 员工台账目前仅覆盖最小字段，不包含组织关系、联系方式、班次等扩展信息。
- 本轮 shell 冒烟验证中，`APIClient` 需显式指定 `HTTP_HOST=localhost` 才能稳定复用本地测试环境，请继续沿用该方式。

### 下一个最优先任务

- 进入 M3，先实现标准化缓存模型、mock 数据装载和左右屏展示 API。
- 优先把“数据源异常时返回最近一次成功数据”的兜底机制落到后端缓存与展示接口，不接真实数据源。

## 16. 本轮更新记录

- 本轮正式进入 M3，但范围严格控制在后端最小闭环，不进入真实数据源接入、不进入报修、不进入 3D 仿真、不进入内部 Web 报表。
- backend：新增标准化缓存快照模型：
  - `DeviceStatusSnapshot`
  - `ProductionSnapshot`
  - `ScheduleSnapshot`
  - `EnergySnapshot`
  - `DataSourceHealthSnapshot`
- backend：新增 `backoffice/display_services.py`，统一承担 mock 数据生成、缓存快照写入、默认配置兜底和左右屏展示数据拼装。
- backend：新增公开展示接口：
  - `/api/screens/left`
  - `/api/screens/right`
- backend：新增后台只读接口：
  - `/api/admin/data-source-healths`
- backend：新增管理命令 `python manage.py load_mock_screen_data`，用于装载 M3 mock 快照；支持 `--simulate-failure`，用于验证“保留最近一次成功数据”的兜底逻辑。
- backend：展示接口会优先读取缓存快照；若 mock 快照尚未生成，会自动补装默认 mock 数据，避免接口空返回。
- backend：当 mock 刷新失败时，只更新 `DataSourceHealthSnapshot` 为失败状态，不覆盖既有展示快照；左右屏接口继续返回上一次成功快照，并在 `meta.usingFallback` 中标记兜底状态。
- backend：新增 `backoffice` 迁移文件 `0004_datasourcehealthsnapshot_devicestatussnapshot_and_more.py`。
- 自动化验证结果：
  - `python -m compileall backoffice hota_mds` 通过
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 15/15 通过
  - `npm run build` 通过
- 运行态冒烟验证结果：
  - `python manage.py migrate --settings=hota_mds.test_settings` 通过
  - `python manage.py load_mock_screen_data --settings=hota_mds.test_settings` 通过
  - `GET /api/screens/left` 返回成功，`screenKey=left`
  - `GET /api/screens/right` 返回成功，`screenKey=right`
  - `python manage.py load_mock_screen_data --simulate-failure --settings=hota_mds.test_settings` 后，再次读取右屏接口，`meta.usingFallback=True`
- 验证注意事项：
  - 使用 SQLite 测试库做本地冒烟时，不要并行执行会写同一库的命令，否则可能出现 `database is locked`。

## 17. 本轮更新记录

- 本轮继续停留在 M3，不接真实外部系统，不做报修真实接入，不做 3D 仿真，不进入内部 Web 报表。
- frontend：新增 `src/ScreenDisplay.jsx`，将左右屏从占位页升级为真实展示页。
- frontend：`/screen/left` 现已接入 `/api/screens/left`，展示欢迎信息、设备概览、产量概览、近 8 小时产量趋势、区域能耗概览和报修占位区。
- frontend：`/screen/right` 现已接入 `/api/screens/right`，展示未完工订单排产、延期风险概览和 3D 仿真预留区。
- frontend：`src/App.jsx` 已改为按路由直接渲染左右屏展示组件，不再停留在大屏占位页。
- frontend：当屏幕页已拿到成功数据后，如果后续接口请求失败，页面会继续保留当前内容，只更新状态提示，避免前端自身导致白屏。
- frontend：`src/styles.css` 新增大屏布局与展示样式，适配桌面和窄屏宽度下的基础展示。
- 自动化验证结果：
  - `npm run build` 通过
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 15/15 通过
- 运行态冒烟验证结果：
  - `http://127.0.0.1:8000/api/screens/left` 返回 200
  - `http://127.0.0.1:3000/screen/left` 返回 200
  - `http://127.0.0.1:3000/screen/right` 返回 200

## 18. 本轮更新记录

- 修复了左右屏前端在 IAB/浏览器中打开时白屏的问题。
- 根因不是后端接口无数据，而是前端当前未启用 React 专用 Vite 插件，JSX 仍按经典运行时编译为 `React.createElement(...)`。
- 由于多个 `.jsx` 文件运行时未自动注入 `React`，页面加载后直接触发 `React is not defined`，导致 `#root` 没有任何内容渲染。
- 修复方式：
  - `frontend/vite.config.js` 新增 `esbuild.jsxInject = 'import React from "react"'`
  - `frontend/src/main.jsx` 改为显式使用 `StrictMode`
- 修复后验证结果：
  - 通过无头浏览器复现并确认旧错误为 `React is not defined`
  - 重启前端 dev/preview 服务后，再次验证 `http://127.0.0.1:3000/screen/left` 与 `http://127.0.0.1:4173/screen/left` 均已渲染正文内容，不再是空白页

## 19. 本轮更新记录

- 本轮继续停留在 M3，没有接真实外部系统，没有进入报修、3D 仿真或内部 Web 报表。
- backend：`/api/admin/data-source-healths` 现在会在健康快照不存在时自动补装默认 mock 快照，避免后台首次进入时空列表。
- backend：新增自动化测试，验证数据源健康接口在未预先装载 mock 数据时也能返回 4 条健康记录。
- frontend：后台控制台新增“数据源健康”只读资源入口，读取 `/api/admin/data-source-healths`。
- frontend：控制台可查看数据源名称、状态、是否兜底、最近成功时间、是否过期，并可点击查看完整记录详情。
- frontend：重写 `AdminConsole.jsx`，清理历史乱码字符串，修正只读详情面板标题与提示文案。
- 自动化验证结果：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 16/16 通过
  - `npm run build` 通过
- 运行态冒烟验证结果：
  - `GET /api/admin/data-source-healths` 在未手工装载 mock 数据时返回 200，`total=4`
  - `http://127.0.0.1:3000/admin/console` 返回 200
  - 使用无头浏览器登录后台后，“数据源健康”标签可见、可点击，列表加载成功，右侧详情面板显示“健康详情”

## 20. 本轮更新记录

- 本轮继续停留在 M3，只优化后台“数据源健康”页面的可读性，不涉及真实数据接入。
- frontend：重写 `src/adminResources.js`，清理资源定义中的历史乱码，并保持现有后台资源行为不变。
- frontend：为“数据源健康”资源新增只读展示格式化能力：
  - `healthy/failed` 显示为“正常/失败”
  - 布尔值显示为“是/否”
  - ISO 时间显示为本地可读格式 `YYYY-MM-DD HH:mm:ss`
  - 详情面板改为按字段分行展示，不再直接暴露原始 JSON 为唯一阅读方式
- frontend：`src/AdminConsole.jsx` 已支持资源自定义表格单元格格式化和详情格式化。
- 自动化验证结果：
  - `npm run build` 通过
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 16/16 通过
- 运行态冒烟验证结果：
  - 无头浏览器登录后台并进入“数据源健康”后，列表中可见“正常”“否”和格式化后的时间字符串

## 21. 本轮更新记录

- 本轮继续停留在 M3，只修复一期双屏展示链路中的可见脏数据，不扩展到真实外部系统、报修接入、3D 仿真或内部 Web 报表。
- frontend：重写 `src/AdminApp.jsx`、`src/App.jsx`、`src/PlaceholderScreen.jsx` 中仍残留的历史乱码文案，保持既有登录、路由和展示行为不变。
- backend：在 `backoffice/display_services.py` 中为展示内容配置增加脏值兜底；当 `company_name` 或 `welcome_message` 为仅由 `?` 组成的历史坏值时，自动回退到默认展示文案。
- backend：补充自动化测试，验证左屏接口在展示内容配置存在 `????` / `????????` 时，仍返回默认欢迎语与公司名。
- 本地运行环境：已修正 `hota_mds.test_settings` 测试库中的坏欢迎语记录，使当前 `runserver` 页面无需手工重建快照即可恢复正常显示。
- 自动化验证结果：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 17/17 通过
  - `npm run build` 通过
- 运行态冒烟验证结果：
  - `GET http://127.0.0.1:8000/api/screens/left` 返回 `welcomeMessage='欢迎莅临参观指导'`、`companyName='和泰智造'`
  - 无头浏览器访问 `http://127.0.0.1:3000/admin/login`，登录页文案显示正常
  - 无头浏览器访问 `http://127.0.0.1:3000/screen/left`，左屏欢迎语与公司名已恢复正常，不再显示 `?`

## 22. 本轮更新记录

- 本轮继续停留在 M3，只收敛一期双屏展示里仍暴露给参观者的原始状态枚举与占位说明，不扩展到真实外部系统、报修真实接入、3D 仿真或内部 Web 报表。
- backend：`backoffice/display_services.py` 现在会为左屏设备状态输出标准化展示列表 `statusItems`，每项包含 `key`、`label`、`accent`、`count`，前端不再直接消费 `running/stopped/alarm/offline` 原始键。
- backend：右屏排产风险汇总现在输出标准化展示列表 `riskSummary.items`，每项包含 `key`、`label`、`accent`、`color`、`count`，前端不再自己维护风险标签映射。
- backend：为一期后段占位模块补充接口文案字段：
  - `repairPlaceholder.description`
  - `simulationPlaceholder.description`
- frontend：重写 `src/ScreenDisplay.jsx`，改为直接渲染后端提供的标准化状态项与占位说明，保留原有双屏轮询刷新和“最近一次成功数据”前端兜底行为不变。
- 自动化验证结果：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 17/17 通过
  - `npm run build` 通过
- 运行态冒烟验证结果：
  - `GET http://127.0.0.1:8000/api/screens/left` 返回 `statusItems=[运行, 停机, 报警, 离线]`
  - `GET http://127.0.0.1:8000/api/screens/right` 返回 `riskSummary.items=[正常, 风险, 延期, 暂停]`
  - 无头浏览器访问 `http://127.0.0.1:3000/screen/left`，左屏已显示“运行/停机/报警/离线”，不再显示英文状态键
  - 无头浏览器访问 `http://127.0.0.1:3000/screen/right`，右屏风险汇总显示“正常/风险/延期/暂停”，并正常显示 3D 预留说明

## 23. 本轮状态总结

### 当前阶段

- 当前 M3 已完成，可进入 M4。
- 一期前段范围仍然只做外部参观双屏大屏，不进入内部 Web 报表。
- 当前左右屏已经接入标准化缓存 API，并具备“最近一次成功数据”兜底能力。
- 当前双屏可见动态字段已全部由后端标准化输出或后端直接提供稳定展示语义。
- 当前仍未进入真实外部系统接入。

### 本轮已完成

- 后端为左屏设备状态增加标准化展示字段 `statusItems`，统一输出“运行 / 停机 / 报警 / 离线”。
- 后端为右屏风险汇总增加标准化展示字段 `riskSummary.items`，统一输出“正常 / 风险 / 延期 / 暂停”。
- 后端为报修占位和 3D 预留区补充说明文案字段：
  - `repairPlaceholder.description`
  - `simulationPlaceholder.description`
- 前端重写 `frontend/src/ScreenDisplay.jsx`，改为直接渲染后端标准化字段，不再自行解释状态枚举。
- 已完成后端测试、前端构建、接口校验和浏览器冒烟验证。

### 未完成

- 仍未接入任何真实外部系统。
- 仍未实现一期之外的内部 Web 报表。
- 仍未进入报修真实接入。
- 仍未进入 3D 仿真真实开发。
- M4 里的轮播、全屏适配和左右屏独立配置读取仍需继续完善并补齐验收。

### 当前已知问题

- 文档中较早期历史段落仍存在编码乱码，但本轮新增记录为正常中文，不影响继续交接。
- 当前验证主要基于 `hota_mds.test_settings` 和本地 mock 链路完成，还没有真实外部系统联调结果。
- 工作区仍存在本轮之外的既有改动，例如 `README.md` 等，当前未处理，也未回退。

### 下一个最优先任务

- 正式进入 M4，基于现有 mock/cache API 优先补齐左右屏轮播、全屏适配和独立配置读取能力，但仍不接真实外部系统。

## 24. 本轮更新记录

- 本轮继续停留在 M3，只收敛右屏排产卡片里仍由前端自己解释的动态展示字段，不扩展到真实外部系统、报修真实接入、3D 仿真或内部 Web 报表。
- backend：在 `backoffice/display_services.py` 中为右屏排产订单新增标准化展示字段 `order.display`，当前包含：
  - `riskLabel`
  - `riskAccent`
  - `timeRangeLabel`
  - `completionRateLabel`
- backend：右屏订单仍保留原始业务字段以兼容现有快照结构，但前端不再依赖 `riskStatus`、`displayStartAt/displayEndAt` 拼接文本或 `completionRate` 百分号拼接来完成展示。
- frontend：`src/ScreenDisplay.jsx` 改为直接渲染后端返回的 `order.display`，右屏排产卡片不再自己解释风险状态，也不再自己拼接时间区间和完成率文案。
- frontend：`src/styles.css` 将右屏排产卡片样式从基于 `risk-*` 原始状态键切换为基于后端标准化输出的 `accent-*` 视觉语义。
- 自动化验证结果：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 17/17 通过
  - `npm run build` 通过
- 运行态冒烟验证结果：
  - 在 `hota_mds.test_settings` 下执行 `load_mock_screen_data` 后，`GET /api/screens/right` 返回 200
  - 首个排产订单返回 `display={'riskLabel': '正常', 'riskAccent': 'green', 'timeRangeLabel': '2026-04-21 - 2026-04-24', 'completionRateLabel': '85.33%'}`，说明右屏卡片展示语义已由后端直接给出

## 25. 本轮更新记录

- 本轮继续停留在 M3，只收敛左屏“产量执行概览”里仍由前端自己拼装的展示语义，不扩展到真实外部系统、报修真实接入、3D 仿真或内部 Web 报表。
- backend：在 `backoffice/display_services.py` 中为左屏产量概览新增标准化展示字段：
  - `productionOverview.display`
  - `productionOverview.lineSummaries[].display`
- backend：当前产量概览标准化字段包含：
  - `overallCompletionRateLabel`
  - `totalTargetQuantityLabel`
  - `totalProducedQuantityLabel`
  - `currentOrderLabel`
  - `targetQuantityLabel`
  - `producedQuantityLabel`
  - `completionRateLabel`
- backend：产量概览仍保留原始数量和百分比字段以兼容现有快照结构，但左屏展示不再依赖前端自己拼接“当前订单 / 目标 / 已产 / %”等文案。
- frontend：`src/ScreenDisplay.jsx` 改为优先渲染后端返回的产量概览标准化字段，左屏产线摘要不再自己拼装订单、数量和完成率文本。
- 自动化验证结果：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 17/17 通过
  - `npm run build` 通过
- 运行态冒烟验证结果：
  - 在 `hota_mds.test_settings` 下执行 `load_mock_screen_data` 后，`GET /api/screens/left` 返回 200
  - 接口返回 `productionOverview.display={'overallCompletionRateLabel': '85.58%', 'totalTargetQuantityLabel': '3120', 'totalProducedQuantityLabel': '2670'}`
  - 首条产线返回 `display={'currentOrderLabel': '当前订单 MO-001', 'targetQuantityLabel': '目标 920', 'producedQuantityLabel': '已产 785', 'completionRateLabel': '85.33%'}`，说明左屏产量概览展示语义已由后端直接给出

## 26. 本轮更新记录

- 本轮继续停留在 M3，只收敛左屏“区域能耗概览”里仍由前端自己格式化和拼接单位的展示语义，不扩展到真实外部系统、报修真实接入、3D 仿真或内部 Web 报表。
- backend：在 `backoffice/display_services.py` 中为左屏能耗概览新增标准化展示字段：
  - `energyOverview.display`
  - `energyOverview.areaSummaries[].display`
- backend：当前能耗概览标准化字段包含：
  - `totalConsumptionLabel`
  - `consumptionLabel`
- backend：能耗概览仍保留原始 `totalConsumption`、`unit`、`consumption` 字段以兼容现有快照结构，但左屏展示不再依赖前端自己拼接 “数值 + 单位” 文案。
- frontend：`src/ScreenDisplay.jsx` 改为优先渲染后端返回的能耗概览标准化字段，左屏总能耗与分区能耗不再由前端自行格式化和拼接单位。
- 自动化验证结果：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 17/17 通过
  - `npm run build` 通过
- 运行态冒烟验证结果：
  - 在 `hota_mds.test_settings` 下执行 `load_mock_screen_data` 后，`GET /api/screens/left` 返回 200
  - 当前本地测试数据下接口返回 `energyOverview.display={'totalConsumptionLabel': '545.00 kWh'}`
  - 首个区域返回 `display={'consumptionLabel': '545.00 kWh'}`
  - 说明左屏能耗概览展示语义已由后端直接给出；具体数值会随当前本地测试数据中的区域数量变化

## 27. 本轮更新记录

- 本轮继续停留在 M3，只收敛左屏“设备运行概览”里仍由前端自己格式化时间和数量的展示语义，不扩展到真实外部系统、报修真实接入、3D 仿真或内部 Web 报表。
- backend：在 `backoffice/display_services.py` 中为左屏设备概览新增标准化展示字段 `deviceOverview.display`。
- backend：当前设备概览标准化字段包含：
  - `sourceUpdatedAtLabel`
  - `totalCountLabel`
  - `runningCountLabel`
  - `abnormalCountLabel`
- backend：设备概览仍保留原始 `sourceUpdatedAt`、`totalCount`、`runningCount`、`abnormalCount` 字段以兼容现有快照结构，但左屏展示不再依赖前端自己格式化时间和数量文案。
- frontend：`src/ScreenDisplay.jsx` 改为优先渲染后端返回的设备概览标准化字段，左屏设备更新时间和三项设备指标不再由前端自行拼装。
- 自动化验证结果：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 17/17 通过
  - `npm run build` 通过
- 运行态冒烟验证结果：
  - 在 `hota_mds.test_settings` 下执行 `load_mock_screen_data` 后，`GET /api/screens/left` 返回 200
  - 接口返回 `deviceOverview.display={'sourceUpdatedAtLabel': '2026-04-21 14:46:53', 'totalCountLabel': '6', 'runningCountLabel': '4', 'abnormalCountLabel': '2'}`
  - 说明左屏设备运行概览展示语义已由后端直接给出

## 28. 本轮更新记录

- 本轮继续留在 M3 做收尾，不扩展到真实外部系统、报修真实接入、3D 仿真或内部 Web 报表；目标是把双屏剩余可见动态字段全部收口到后端标准化输出，并据此完成 M3 验收。
- backend：在 `backoffice/display_services.py` 中新增或补齐以下标准化展示字段：
  - `meta.display.lastSuccessfulAtLabel`
  - `deviceOverview.statusItems[].countLabel`
  - `productionTrend[].display.timeLabel`
  - `productionTrend[].display.producedQuantityLabel`
  - `schedule.display.windowDaysLabel`
  - `schedule.riskSummary.items[].countLabel`
- frontend：`src/ScreenDisplay.jsx` 改为优先渲染上述标准化展示字段，左右屏状态栏、状态分解、趋势图、排产窗口文案和风险概览计数不再由前端自行格式化。
- backend：保留原始 `lastSuccessfulAt`、`count`、`hourLabel`、`producedQuantity`、`windowDays` 等字段作为兼容字段，避免无必要重构。
- M3 完成结论：
  - 已具备设备、产量、排产、能耗 mock API
  - 前端已基于 mock/cache API 完成双屏展示开发
  - 后端已具备缓存数据读取接口与最近一次成功数据兜底
  - 后台已可查看 mock 数据源健康状态
- 自动化验证结果：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 17/17 通过
  - `npm run build` 通过
- 运行态冒烟验证结果：
  - 在 `hota_mds.test_settings` 下执行 `load_mock_screen_data` 后，`GET /api/screens/left` 返回 200
  - 左屏返回 `meta.display={'lastSuccessfulAtLabel': '2026-04-21 14:57:20'}`
  - 左屏首个状态项返回 `countLabel='4'`
  - 左屏首个趋势点返回 `display={'timeLabel': '07:00', 'producedQuantityLabel': '80'}`
  - `GET /api/screens/right` 返回 200
  - 右屏返回 `schedule.display={'windowDaysLabel': '30 天'}`
  - 右屏首个风险项返回 `countLabel='1'`
  - 说明双屏剩余可见动态字段也已由后端直接提供稳定展示语义

## 29. 收尾摘要

### 当前阶段

- 当前已完成 M3，可进入 M4。
- 当前阶段仍然只面向一期前段外部参观双屏大屏，不进入内部 Web 报表。
- 当前仍未接入真实外部系统，前端仍不得直连外部系统。

### 本轮已完成

- 已把双屏剩余可见动态字段继续收口到后端标准化输出。
- 已为左右屏状态栏补齐 `meta.display.lastSuccessfulAtLabel`。
- 已为左屏状态分解补齐 `deviceOverview.statusItems[].countLabel`。
- 已为左屏趋势区补齐 `productionTrend[].display.timeLabel` 与 `productionTrend[].display.producedQuantityLabel`。
- 已为右屏排产窗口补齐 `schedule.display.windowDaysLabel`。
- 已为右屏风险概览补齐 `schedule.riskSummary.items[].countLabel`。
- 已完成自动化测试、前端构建和左右屏接口冒烟验证。

### 未完成

- 尚未进入 M4 的轮播、全屏适配和左右屏独立配置读取完善。
- 尚未接入任何真实外部系统。
- 尚未进入报修真实接入、3D 仿真真实开发和内部 Web 报表。

### 当前已知问题

- 当前验证仍主要基于 `hota_mds.test_settings` 与 mock 链路，暂无真实外部系统联调结果。
- 文档较早历史段落仍存在少量编码乱码，但本轮新增记录为正常中文。
- 工作区仍有本轮之外的既有改动，例如 `README.md`、`frontend/src/styles.css` 与 `.codex-logs/`，本轮未处理也未回退。

### 下一个最优先任务

- 正式进入 M4，优先基于现有 `/api/screens/left` 与 `/api/screens/right` 补齐左右屏轮播、全屏适配和独立配置读取，但仍不接真实外部系统。

## 30. 本轮更新记录

- 本轮正式进入 M4，只完成一期前段外部参观双屏大屏页面，继续基于 mock/cache API 开发，不接真实外部系统。
- 已完成 `frontend/src/ScreenDisplay.jsx` 的双屏页面实现：
  - 支持 `/screen/left` 与 `/screen/right` 独立通过 URL 打开。
  - 左屏实现 Logo / 欢迎语 / 当前时间、设备运行概览、产量执行概览、近 8 小时产量趋势、区域能耗概览、报修占位区。
  - 右屏实现未完工订单排产展示、延期风险说明、3D 仿真占位区。
  - 左右屏分别根据各自配置读取标题、页面集合、轮播顺序与轮播间隔。
  - 支持用户触发全屏展示，提供按钮与双击进入/退出全屏。
  - 支持自动轮播，在存在多个页面预设时按配置间隔自动切换。
  - 在接口异常或单模块缺失时继续保留最近一次成功数据，避免整页白屏。
- 已完成右屏甘特图可用版：
  - 按产线分组展示。
  - 基于未来 30 日窗口渲染任务条。
  - 当产线数量超过阈值时自动纵向滚动。
- 已完成大屏视觉样式升级：
  - 基于 `frontend/framer.md` 与 `frontend/sentry.md` 重做双屏展示层。
  - 风格调整为深色、冷色调、访客驾驶舱风格的大数字 KPI 与玻璃质感卡片。
- 本轮未扩展到真实外部系统、报修真实接入、3D 仿真真实开发、内部 Web 报表，严格保持在 M4 范围内。
- 验证结果：
  - `npm run build` 通过。
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 17/17 通过。
  - 基于 `hota_mds.test_settings` 的接口冒烟校验通过：
    - `GET /api/screens/left` 返回 200，`pageKeys=['overview', 'operations']`，`rotationIntervalSeconds=45`
    - `GET /api/screens/right` 返回 200，`pageKeys=['schedule', 'risk']`，`rotationIntervalSeconds=50`
    - 右屏排产窗口返回 `windowDays=30`

## 31. 本轮收尾状态

### 当前阶段

- 当前已完成 M4：一期前段大屏页面，可基于 mock/cache API 运行左右双屏展示。
- 当前仍严格限定在一期前段外部参观双屏范围内，不进入内部 Web 报表。
- 前端仍不直连外部系统，真实数据接入仍由后端后续统一承担。

### 本轮已完成

- `/screen/left` 页面实现完成。
- `/screen/right` 页面实现完成。
- 左右屏独立 URL 打开完成。
- 左右屏独立配置读取完成。
- 全屏展示支持完成。
- 自动轮播支持完成。
- 接口异常不白屏保护完成。
- 报修与 3D 区域占位完成。
- 甘特图可用版完成。

### 本轮未完成

- 尚未接入任何真实外部系统。
- 尚未实现报修真实业务数据。
- 尚未实现 3D 仿真真实模块。
- 尚未进入内部 Web 报表开发。
- 尚未完成真实大屏现场拼屏与浏览器全屏联调。

### 当前已知问题

- 当前全屏能力受浏览器安全策略限制，只能由用户手动触发，不能在页面加载后自动进入全屏。
- 当前自动轮播基于前端页面预设与后端配置组合实现，后续若页面模型扩展，需同步补充新的预设页定义。
- 当前验证以构建、自动化测试和 API 冒烟为主，尚未覆盖真实大屏设备上的视觉验收。

### 下一个最优先任务

- 下一轮进入 M5 准备阶段，优先在保持前端与外部系统解耦的前提下，推进后端真实数据接入方案、缓存策略完善与现场联调准备。

## 32. 本轮更新记录

- 本轮继续停留在 M4 范围内，只收口右屏甘特图可读性和 mock 数据验证能力，不进入真实外部系统、报修真实接入、3D 仿真真实开发或内部 Web 报表。
- frontend：
  - `frontend/src/ScreenDisplay.jsx`
  - 右屏甘特图区新增产线数、订单数和滚动状态信息。
  - 甘特图行头补充区域名称、可见订单数和延期数提示。
  - 甘特条进一步区分完整 / 紧凑 / 极窄三种展示密度。
  - 甘特条补充时间范围显示，并为跨窗口条增加左右裁剪提示。
- frontend：
  - `frontend/src/styles.css`
  - 甘特图区头部改为 sticky，便于滚动时持续对齐日期窗口。
  - 调整行高、条内信息层级、省略样式和裁剪指示样式，减少文字显示不全与短条误判。
- backend：
  - `backend/backoffice/display_services.py`
  - 扩充右屏 mock 排产数据为多产线、多订单混合场景。
  - 当前 mock 右屏可稳定生成 16 条产线、32 个订单，覆盖正常 / 风险 / 延期 / 暂停四类风险状态。
  - mock 数据规模已超过默认自动滚动阈值 12，可用于验证右屏自动纵向滚动能力。
- test：
  - `backend/backoffice/tests.py`
  - 调整右屏接口测试为校验多产线、多订单、自动滚动阈值满足和风险汇总正确，不再写死旧的 3 线 3 单 mock 结构。
- 本轮验证结果：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 17/17 通过。
  - `npm run build` 通过。
  - 运行态接口校验：`GET /api/screens/right` 返回 200，当前返回 `lineCount=16`、`totalOrders=32`、`threshold=12`、`shouldAutoScroll=true`。
  - 运行态页面校验：`GET /screen/right` 返回 200。

## 33. 本轮收尾状态

### 当前阶段

- 当前仍为 M4 收口阶段，重点是把右屏甘特图做到可演示、可验证、可持续调优。
- 当前双屏仍只基于 mock/cache API 展示，符合一期前段不直连外部系统的约束。

### 本轮已完成

- 甘特图短条与窄条显示优化完成。
- 甘特图行头信息增强完成。
- 甘特图滚动时日期头固定完成。
- 右屏 mock 数据扩容完成。
- 自动滚动验证数据准备完成。
- 自动化测试与构建验证完成。

### 本轮未完成

- 尚未进行真实大屏硬件上的远距离可读性验收。
- 尚未对右屏甘特图做现场拼屏字体和行高微调。
- 尚未接入任何真实排产系统。

### 当前已知问题

- 当前自动滚动验证已具备数据条件，但仍主要通过本地浏览器环境验证，尚未覆盖真实 kiosk/拼屏环境。
- 右屏 mock 数据为演示目的构造，后续进入 M5 时仍需要以后端真实标准化结果替换。

### 下一个最优先任务

- 下一步优先做右屏现场演示收口验收，重点确认真实大屏场景下的行高、字体、风险颜色层级和自动滚动节奏。

## 34. 本轮更新记录

- 本轮继续停留在 M4 范围内，只优化右屏甘特图短周期任务的订单号可读性，不扩展到真实外部系统、报修真实接入、3D 仿真或内部 Web 报表。
- frontend：
  - `frontend/src/styles.css`
  - 针对短周期任务条继续压缩字号、字距和左右内边距。
  - 对 `compact` 与 `tiny` 两类窄条取消省略号优先策略，尽量完整显示订单号。
  - 该轮不改动已修复好的纵向布局计算，只在短条文本样式层做增强。
- 本轮验证结果：
  - `npm run build` 通过。
  - `GET /screen/right` 返回 200。

## 35. 本轮收尾状态

### 当前阶段

- 当前仍处于 M4 右屏甘特图展示层收口阶段。
- 当前已在保持自动滚动与纵向不截断的前提下，进一步增强短周期任务订单号的可读性。

### 本轮已完成

- 短周期任务条字体继续缩小。
- 短周期任务条内边距继续压缩。
- 短周期任务条优先完整显示订单号。

### 本轮未完成

- 尚未在真实拼屏距离下验证短周期任务条的最终最佳字号。
- 若出现极端更短的任务宽度，后续仍可能需要继续微调字体与字距。

### 下一个最优先任务

- 下一步优先做右屏甘特图短条与长条混排场景的现场可读性验收，确认当前字号方案是否已足够支撑远距离观看。

## 36. 本轮更新记录

- 本轮继续停留在 M4 范围内，只处理右屏甘特图区滚动条视觉问题，不扩展到真实外部系统、报修、3D 仿真或内部 Web 报表。
- frontend：
  - `frontend/src/styles.css`
  - 对 `.gantt-rows` 增加跨浏览器隐藏滚动条样式。
  - 当前保持纵向可滚动与自动滚动能力不变，只隐藏滚动条本身，避免右侧拖动条破坏大屏观感。
- 本轮验证结果：
  - `npm run build` 通过。
  - `GET /screen/right` 返回 200。

## 37. 本轮收尾状态

### 当前阶段

- 当前仍处于 M4 右屏甘特图展示层收口阶段。
- 当前右屏甘特图区已隐藏显式滚动条，同时保留滚动能力。

### 本轮已完成

- 甘特图区右侧纵向滚动条隐藏完成。
- 自动滚动与手动滚动能力保留完成。

### 本轮未完成

- 尚未在真实拼屏硬件上确认隐藏滚动条后的观感是否完全符合现场要求。

### 下一个最优先任务

- 下一步优先继续做右屏甘特图现场观感收口，重点确认远距离观看下的短条文字与整体密度是否还需微调。

## 38. 本轮更新记录

- 本轮继续停留在 M4 范围内，集中收口右屏甘特图展示问题，不扩展到真实外部系统、报修真实接入、3D 仿真或内部 Web 报表。
- frontend：
  - `frontend/src/ScreenDisplay.jsx`
  - 调整右屏甘特图任务条的纵向槽位、底部安全区与轨道布局，修复部分任务块底部被截断的问题。
  - 去掉任务条上的“风险 / 延期”等文字，仅保留颜色作为风险区分方式。
  - 保留订单号、物料、完成率、时间范围等必要展示信息。
- frontend：
  - `frontend/src/styles.css`
  - 继续收口短周期任务条样式，缩小字号、字距与内边距，尽量完整显示订单号。
  - 隐藏甘特图区右侧显式纵向滚动条，但保留自动滚动与手动滚动能力。
- docs：
  - 已同步更新 `STATUS.md`、`HANDOFF.md`、`DECISIONS.md`，将右屏甘特图这一轮展示层收口结果统一记录。
- 本轮验证结果：
  - `npm run build` 通过。
  - `GET /screen/right` 返回 200。

## 39. 本轮收尾状态

### 当前阶段

- 当前仍处于 M4：一期前段双屏大屏展示层收口阶段。
- 当前右屏甘特图已完成可用版基础上的一轮集中优化，重点解决短条可读性、任务块截断与滚动条观感问题。

### 本轮已完成

- 修复右屏甘特图部分任务块底部被截断的问题。
- 任务条移除风险文字，仅保留颜色作为状态区分。
- 短周期任务条进一步缩小字体与内边距，提升完整订单号显示概率。
- 隐藏甘特图区右侧显式滚动条，同时保留滚动与自动滚动能力。
- 保持当前 mock 数据规模，可继续验证自动滚动逻辑。

### 未完成

- 尚未在真实拼屏硬件与远距离观看场景下确认短条字号是否已经达到最终可用状态。
- 尚未接入真实排产系统数据，当前仍为 mock/cache API 展示。
- 尚未完成右屏甘特图在现场演示环境下的最终视觉微调。

### 当前已知问题

- 极端更短的任务条在特定窗口宽度下，仍可能需要进一步压缩字号或采用更激进的超短条策略。
- 当前自动滚动与滚动条隐藏已在本地浏览器环境验证，但尚未在真实 kiosk/拼屏环境完成终验。
- 当前 mock 排产数据为展示验证 purpose 放大构造，进入 M5 后仍需基于真实标准化结果重新验收密度分布。

### 下一个最优先任务

- 下一步优先做右屏甘特图现场演示验收，重点确认真实拼屏距离下的短条订单号可读性、整体行密度与自动滚动节奏是否需要最后一轮微调。

## 40. 本轮更新记录

- 本轮严格控制为一个最小可交付目标：同步更新 `README.md`，不进入代码实现、不扩展到 M5 真实数据接入。
- `README.md` 已按当前文档事实源对齐到 M4 状态：
  - 明确当前已完成 `M4`，真实数据源接入尚未开始。
  - 明确一期前段只做外部参观双屏大屏，不包含内部 Web 报表。
  - 明确报修与 3D 仿真不是一期前段阻塞项。
  - 明确前端不得直连外部系统，后端负责定时拉取、标准化、缓存和 API 提供。
  - 明确数据源异常时大屏显示最近一次成功数据，不白屏。
- `README.md` 已修正文档入口与项目路径：
  - 必读文档改为当前实际存在的 7 份核心文档路径。
  - PRD 路径改为 `docs/PRD/PRD_和泰智屏系统.md`。
- `README.md` 已同步更新当前路由、双屏页面状态、mock 装载命令和后台资源清单，避免继续误导为 M2 阶段或占位页阶段。
- 本轮未修改任何后端、前端或数据模型实现。

## 41. 本轮收尾状态

### 当前阶段

- 当前仍处于 `M4` 已完成、`M5` 未开始的状态。
- 本轮仅做文档同步，不改变一期前段范围，不改变技术方案。

### 本轮已完成

- 已更新根目录 `README.md`，使其与 `PRD/SPEC/PLAN/STATUS/HANDOFF/AGENTS/DECISIONS` 保持一致。
- 已将 README 中过时的 M2 阶段描述修正为当前 M4 状态。
- 已修正 README 中错误的 PRD 路径与过时的“占位页”描述。

### 本轮未完成

- 未进入真实外部系统接入。
- 未继续推进右屏甘特图现场验收。
- 未进行报修、3D 仿真或内部 Web 报表开发。

### 当前已知问题

- README 已同步到当前项目状态，但现场拼屏终验与真实数据源接入仍未开始，文档中的下一步仍以 M5 前置准备为准。
- 工作区仍存在 `.codex-logs/` 未跟踪目录，本轮未处理。

### 下一个最优先任务

- 回到既定计划，继续在不扩展范围的前提下推进 M5 前置准备，或根据现场需要继续做右屏甘特图展示层终验收口。

## 42. 本轮更新记录

- 本轮目标是启动当前项目，供本地查看前端效果；不进入新功能开发，不扩大里程碑范围。
- 由于本机 Docker Engine 未启动，未采用 `docker compose up` 方案。
- 本轮采用本地开发启动方式：
  - 后端：基于 `hota_mds.test_settings` 的 SQLite 测试库启动 Django。
  - 前端：基于 Vite 开发服务器启动 React 页面。
- 运行前先处理本地测试库：
  - 发现 `backend/test.sqlite3` 为历史本地产物，迁移状态与当前代码不一致。
  - 删除旧的 `backend/test.sqlite3` 后重新执行迁移。
  - 串行执行 `load_mock_screen_data` 装载 mock 数据。
- 本轮已成功启动：
  - 后端：`http://127.0.0.1:8000`
  - 前端：`http://127.0.0.1:3000`
- 本轮验证结果：
  - `GET http://127.0.0.1:8000/api/health` 返回 200
  - `GET http://127.0.0.1:8000/api/screens/left` 返回 200
  - `GET http://127.0.0.1:3000/screen/left` 返回 200
  - `GET http://127.0.0.1:3000/screen/right` 返回 200
- 运行日志已输出到：
  - `.codex-logs/backend.out.log`
  - `.codex-logs/backend.err.log`
  - `.codex-logs/frontend.out.log`
  - `.codex-logs/frontend.err.log`
- 本轮未修改任何业务代码，仅进行了本地运行与验证。

## 43. 本轮收尾状态

### 当前阶段

- 当前项目阶段仍为 `M4` 已完成、`M5` 未开始。
- 本轮仅完成本地启动与展示验证，不改变项目范围与技术边界。

### 本轮已完成

- 已完成本地后端启动。
- 已完成本地前端启动。
- 已完成 mock 数据装载。
- 已完成左右屏页面可访问性验证。

### 本轮未完成

- 未启动 Docker Compose 方案。
- 未接入真实外部系统。
- 未继续推进现场拼屏终验。

### 当前已知问题

- 本机 Docker Desktop 的 Linux Engine 当前未启动，因此本轮只能采用本地开发方式查看页面效果。
- `backend/test.sqlite3` 是易失的本地产物，如后续再次出现迁移不一致，仍应优先重建而不是带病沿用。

### 下一个最优先任务

- 如需继续看页面效果，可直接使用当前已启动的本地服务；如需进入下一轮开发，应回到既定计划推进 M5 前置准备或继续做现场展示验收。

## 44. 本轮更新记录

- 本轮继续严格停留在 `M4` 展示层收口范围内，只处理左屏“产量执行概览”模块的可读性与 mock 验证能力，不进入真实外部系统、报修、3D 仿真或内部 Web 报表。
- frontend：
  - `frontend/src/ScreenDisplay.jsx`
  - 左屏产量概览中的每条产线摘要新增可视化进度条，不再只显示百分比文本。
  - 当产线摘要数量超过 6 条时，模块进入自动纵向滚动模式，便于大屏场景验证多产线展示。
  - 模块头部新增产线总数与“自动滚动中”状态提示。
- frontend：
  - `frontend/src/styles.css`
  - 新增左屏产量概览进度条样式。
  - 新增产线摘要滚动容器样式，并隐藏显式滚动条，保留滚动能力。
  - 调整产线摘要布局，保证进度条、订单信息和目标/已产信息可同时展示。
- backend：
  - `backend/backoffice/display_services.py`
  - 左屏 mock 产量摘要从默认 3 条扩充为最少 8 条，便于直接验证滚动。
  - 保持首条产线的既有 mock 语义不变，避免无必要破坏原有验证口径。
- test：
  - `backend/backoffice/tests.py`
  - 同步更新左屏 mock 总量断言，并新增 8 条产线摘要数量断言。
- 本轮验证结果：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 32/32 通过。
  - `npm run build` 通过。
  - `python manage.py load_mock_screen_data --settings=hota_mds.test_settings` 通过。
  - `GET http://127.0.0.1:8000/api/screens/left` 返回 200，当前 `lineCount=8`。
  - `GET http://127.0.0.1:3000/screen/left` 返回 200。

## 45. 本轮收尾状态

### 当前阶段

- 当前仍为 `M4` 已完成后的展示层优化阶段。
- 本轮只增强左屏产量概览的展示表达与 mock 验证能力，不改变项目边界。

### 本轮已完成

- 左屏产量概览为每条产线新增进度条展示。
- 左屏产量概览支持超量自动滚动。
- 左屏 mock 产线摘要已扩充到 8 条，可直接验证滚动效果。
- 已完成后端测试、前端构建和左屏接口/页面访问验证。

### 本轮未完成

- 未接入真实产量系统数据。
- 未在真实拼屏硬件上完成左屏产量概览的现场可读性终验。
- 未推进 M5 真实数据接入。

### 当前已知问题

- 当前左屏自动滚动验证仍基于 mock/cache API 与本地浏览器环境，尚未完成真实现场终验。
- 当前本地后端采用 `hota_mds.test_settings` 启动，便于演示验证，但不代表正式 MySQL 部署方式。

### 下一个最优先任务

- 如继续收口 M4，优先在真实大屏观看距离下验收左屏产量概览的进度条可读性与滚动节奏；如进入下一阶段，则回到既定计划推进 M5 前置准备。

## 46. 本轮更新记录

- 本轮继续停留在 `M4` 左屏展示层优化范围内，只增强“产量执行概览”的进度语义和时间信息，不进入真实数据接入。
- backend：
  - `backend/backoffice/display_services.py`
  - 左屏产线摘要新增：
    - `plannedStartAt`
    - `plannedEndAt`
    - `estimatedCompletionAt`
    - `isDelayed`
  - 左屏产线摘要 `display` 新增：
    - `plannedRangeLabel`
    - `estimatedCompletionLabel`
    - `progressAccent`
  - 当前 mock 中已稳定制造延期样本；若预计完成时间晚于计划结束时间，则 `progressAccent='red'`。
- frontend：
  - `frontend/src/ScreenDisplay.jsx`
  - 左屏进度条加粗。
  - 完成率百分比移动到进度条右侧。
  - 每条产线新增“起始时间 - 结束时间”显示。
  - 每条产线新增“预计完成时间”显示。
  - 延期样本的进度条改为红色。
- frontend：
  - `frontend/src/styles.css`
  - 新增蓝色/红色两种进度条样式。
  - 调整左屏产量摘要布局，兼容更粗的进度条与新增时间文案。
- test：
  - `backend/backoffice/tests.py`
  - 新增时间标签与 `progressAccent` 断言。
  - 新增“至少存在红色延期样本”的断言。
- 本轮验证结果：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 32/32 通过。
  - `npm run build` 通过。
  - `GET http://127.0.0.1:8000/api/screens/left` 返回 200。
  - 当前左屏接口返回 `lineCount=8`。
  - 当前左屏接口返回 `delayedCount=2`，已可验证红色延期进度条。
  - `GET http://127.0.0.1:3000/screen/left` 返回 200。

## 47. 本轮收尾状态

### 当前阶段

- 当前仍处于 `M4` 左屏展示层收口阶段。
- 本轮只增强左屏产量概览的可读性与延期表达，不改变项目边界。

### 本轮已完成

- 左屏进度条已变粗。
- 左屏百分比已移到进度条右侧。
- 左屏每条产线已显示计划起止时间。
- 左屏每条产线已显示预计完成时间。
- mock 中已具备红色延期样本。

### 本轮未完成

- 未接入真实产量/订单系统。
- 未在真实拼屏硬件上完成时间信息的远距离可读性终验。
- 未推进 M5 真实数据接入。

### 当前已知问题

- 当前时间信息展示仍基于 mock/cache API 和本地浏览器环境验证，尚未完成真实现场终验。
- 本地后端为保证稳定访问，当前采用 `runserver --noreload` 常驻方式启动，仅用于本地演示和验证。

### 下一个最优先任务

- 如果继续收口 M4，优先在真实观看距离下确认左屏时间文案密度、红条警示强度和滚动节奏是否还需微调；否则按计划推进 M5 前置准备。

## 48. 本轮更新记录

- 本轮继续停留在 `M4` 左屏展示层微调范围内，只处理“任务进度条横向过短”的问题，不改变数据结构和项目边界。
- frontend：
  - `frontend/src/styles.css`
  - 为左屏产量概览卡片补充主信息区的弹性拉伸能力，使其占满任务块剩余宽度。
  - 将进度条行宽度调整为约 `88%`，落在用户要求的 `85%-90%` 区间内。
  - 保持百分比数字仍位于进度条右方。
  - 右侧数量信息列宽度收敛为固定窄列，避免继续压缩进度条横向空间。
- 本轮验证结果：
  - `npm run build` 通过。
  - `GET http://127.0.0.1:3000/screen/left` 返回 200。

## 49. 本轮收尾状态

### 当前阶段

- 当前仍处于 `M4` 左屏展示层细节收口阶段。
- 本轮只处理进度条长度问题，不改变已确认的时间信息、预计完成时间和延期红条逻辑。

### 本轮已完成

- 左屏任务进度条横向已拉长。
- 进度条与百分比组合占据任务块约 `88%` 的横向空间。
- 百分比仍保留在进度条右方。

### 本轮未完成

- 未在真实拼屏硬件上确认当前 88% 是否就是最终最佳占比。
- 未推进真实数据接入。

### 当前已知问题

- 当前 88% 的占比基于本地浏览器收口，真实拼屏环境下仍可能需要微调到更接近 85% 或 90%。

### 下一个最优先任务

- 如果继续收口 M4，优先在真实观看距离下确认当前进度条长度、百分比间距和时间信息密度是否已经合适。

## 50. 本轮更新记录

- 本轮继续停留在 `M4` 左屏展示层微调范围内，只处理“进度条仍然偏短”的问题。
- frontend：
  - `frontend/src/styles.css`
  - 将右侧数量信息列进一步压窄到更小的固定宽度。
  - 将进度条行宽度从上轮的近满宽继续推到主信息区满宽。
  - 同时缩小百分比最小宽度与进度条/百分比之间的间距，减少对横向长度的占用。
  - 略微缩小时间信息字号，避免主区域被文案继续挤压。
- 本轮验证结果：
  - `npm run build` 通过。
  - `GET http://127.0.0.1:3000/screen/left` 返回 200。

## 51. 本轮收尾状态

### 当前阶段

- 当前仍处于 `M4` 左屏展示层细节收口阶段。
- 本轮只继续拉长进度条，不改变业务逻辑和数据结构。

### 本轮已完成

- 左屏进度条横向空间进一步增大。
- 百分比仍保持在进度条右方。
- 右侧数量列已进一步压窄。

### 本轮未完成

- 未在真实拼屏硬件上确认这次拉长后是否已达到最终要求。
- 未推进真实数据接入。

### 当前已知问题

- 当前已经把进度条区域尽量推向主区域满宽；如果仍觉得不够长，下一轮需要改动卡片整体信息布局，而不只是继续微调间距。

### 下一个最优先任务

- 如果继续收口 M4，优先根据你的现场观感决定是否要进入“改卡片整体布局换更长进度条”的方案。

## 52. 本轮更新记录

- 本轮继续停留在 `M4` 左屏展示层微调范围内，重点不是再压缩宽度，而是让进度条真正跨越卡片内部的纵向分栏。
- frontend：
  - `frontend/src/ScreenDisplay.jsx`
  - 将左屏任务卡片结构调整为：
    - 第一行：主信息 + 右侧目标/已产信息
    - 第二行：整行进度条 + 百分比
    - 第三行：整行时间信息
  - 进度条和百分比不再放在左侧主信息区内部，而是独立成跨列一整行。
- frontend：
  - `frontend/src/styles.css`
  - 左屏任务卡片改为真正的 CSS Grid 布局。
  - 进度条行设置为 `grid-column: 1 / -1`，跨越整张卡片，包括原先右侧信息列所在区域。
  - 时间信息行同样改为跨列整行，避免继续受纵向分栏限制。
- 本轮验证结果：
  - `npm run build` 通过。
  - `GET http://127.0.0.1:3000/screen/left` 返回 200。

## 53. 本轮收尾状态

### 当前阶段

- 当前仍处于 `M4` 左屏展示层细节收口阶段。
- 本轮核心是修正布局根因，让进度条突破内部纵向隔断，而不是继续做纯样式压缩。

### 本轮已完成

- 左屏进度条已改为跨整卡宽度显示。
- 百分比仍保留在进度条右方，但现在位于任务块最右侧。
- 时间信息也已改为整行显示。

### 本轮未完成

- 未在真实拼屏硬件上确认当前跨列布局是否就是最终效果。
- 未推进真实数据接入。

### 当前已知问题

- 当前已解决“进度条被内部纵向隔断限制”的根因；若后续仍觉得不够长，就需要进一步减少卡片左右内边距，而不再是处理分栏问题。

### 下一个最优先任务

- 如果继续收口 M4，优先根据你刷新后的实际观感决定，下一步是否只再微调卡片左右内边距和百分比占位宽度。

## 54. 本轮更新记录

- 本轮继续停留在 `M4` 展示层稳定性修复范围内，只处理“滚动到最后一个任务后不会重新从第一条开始滚动”的问题。
- frontend：
  - `frontend/src/ScreenDisplay.jsx`
  - 修正通用自动纵向滚动 hook。
  - 旧逻辑只有在 `scrollTop >= maxScrollTop` 时才回到顶部，存在滚动值接近底部但未精确命中的情况，导致不回卷。
  - 新逻辑改为提前判断下一步滚动位置；当 `nextScrollTop >= maxScrollTop - 1` 时，直接重置到 `scrollTop = 0`。
  - 该修复同时覆盖左屏产量列表和右屏甘特图区的自动纵向滚动。
- 本轮验证结果：
  - `npm run build` 通过。
  - `GET http://127.0.0.1:3000/screen/left` 返回 200。
  - `GET http://127.0.0.1:3000/screen/right` 返回 200。

## 55. 本轮收尾状态

### 当前阶段

- 当前仍处于 `M4` 展示层细节收口阶段。
- 本轮只修复自动滚动回卷逻辑，不改变展示数据和布局结构。

### 本轮已完成

- 左屏滚动到底后可重新从第一条开始滚动。
- 右屏共用滚动 hook 的回卷逻辑一并增强。

### 本轮未完成

- 未在真实拼屏硬件上做滚动回卷终验。
- 未推进真实数据接入。

### 当前已知问题

- 当前修复基于前端自动滚动逻辑本身完成，本地构建与页面访问验证通过；真实大屏环境下仍建议再做一次长时间连续播放观察。

### 下一个最优先任务

- 如果继续收口 M4，优先在真实展示环境下观察左屏和右屏是否都能稳定循环滚动，不出现再次停在底部的问题。

## 56. 本轮更新记录

- 本轮继续严格停留在 `M4` 左屏展示层调整范围内，不进入真实数据源接入，不扩展到报修真实接入、3D 仿真或内部 Web 报表。
- frontend：
  - `frontend/src/ScreenDisplay.jsx`
  - 左屏“设备运行概览”模块移除原先单独展示的运行、停机、报警、离线四块状态明细。
  - 左屏“报修占位区”不再作为独立卡片渲染，改为并入“设备运行概览”卡片下半区。
  - 左屏“区域能耗概览”不再作为独立卡片渲染，改为并入“近 8 小时产量趋势”卡片下半区。
  - 为兼容既有 `pageKeys` 与 `moduleSettings` 配置，左屏页面 section 解析新增嵌入映射：`repairPlaceholder -> deviceOverview`、`energyOverview -> productionTrend`，避免旧配置下重复渲染或空白页。
- frontend：
  - `frontend/src/styles.css`
  - 新增左屏卡片内嵌子模块样式，用于设备概览中的报修占位区和产量趋势中的能耗区。
  - 内嵌报修区改为同卡片下半区展示，不再占用独立大卡片高度。
  - 内嵌能耗区改为同卡片下半区展示，充分利用原趋势卡片下半部分空间。
- 本轮验证结果：
  - `npm run build` 通过。
  - `GET http://127.0.0.1:3000/screen/left` 返回 200。
  - `GET http://127.0.0.1:8000/api/screens/left` 返回 200。

## 57. 本轮收尾状态

### 当前阶段

- 当前仍处于 `M4` 已完成后的左屏展示层收口阶段。
- 本轮只调整左屏卡片组织方式，不改变后端接口边界，不推进 `M5` 真实数据接入。

### 本轮已完成

- 左屏设备概览已移除运行、停机、报警、离线四块状态明细展示。
- 左屏报修占位区已整合进设备概览卡片。
- 左屏区域能耗概览已整合进近 8 小时产量趋势卡片。
- 旧的左屏页面配置 key 和模块开关语义仍保持兼容。
- 已完成前端构建与左屏路由/API 可访问性验证。

### 本轮未完成

- 未接入真实设备、产量、排产、能耗数据源。
- 未在真实拼屏硬件上完成本轮左屏重组后的现场观感终验。
- 未推进报修真实接入、3D 仿真或内部 Web 报表。

### 当前已知问题

- 本轮验证覆盖了构建成功与本地访问返回 200，但未做真实大屏观看距离下的视觉终验。
- 左屏本轮为前端展示层重组，是否还需继续微调卡片内边距、模块高度和文案密度，需要以现场观感为准。

### 下一个最优先任务

- 如果继续收口 `M4`，优先在真实左屏展示距离下确认两处整合后的模块密度是否合适；否则继续等待外部系统资料到位，再按计划推进 `M5` 前置准备。

## 58. 本轮更新记录

- 本轮继续严格停留在 `M4` 左屏展示层 bug 修复范围内，不进入真实数据接入，不扩大到报修真实接入、3D 仿真或内部 Web 报表。
- frontend：
  - `frontend/src/ScreenDisplay.jsx`
  - 左屏“产量执行概览”卡片新增独立布局类 `production-overview-panel`。
  - 左屏产线摘要列表新增 `production-overview-list` 容器，使列表区域占用卡片剩余高度，而不是继续向下撑出卡片。
- frontend：
  - `frontend/src/styles.css`
  - 将“产量执行概览”卡片改为纵向弹性布局：头部和总览信息固定，产线列表占用剩余高度。
  - 产线列表统一改为在卡片内部滚动，避免底部条目被卡片 `overflow: hidden` 裁切。
  - 去掉原先基于固定 `max-height: 372px` 的约束，改为按卡片实际剩余高度自适应。
- 本轮验证结果：
  - `npm run build` 通过。
  - `GET http://127.0.0.1:3000/screen/left` 返回 200。

## 59. 本轮收尾状态

### 当前阶段

- 当前仍处于 `M4` 左屏展示层收口阶段。
- 本轮只修复左屏“产量执行概览”底部内容被裁切的问题，不改变数据结构和项目边界。

### 本轮已完成

- 左屏“产量执行概览”卡片内部列表已改为占满剩余高度。
- 左屏产线摘要底部数据不再因卡片高度限制被直接裁掉。
- 产线摘要列表仍保留滚动能力，并兼容现有自动滚动逻辑。
- 已完成前端构建和左屏页面可访问性验证。

### 本轮未完成

- 未在真实拼屏硬件上确认修复后的最终观感。
- 未接入真实外部系统。
- 未推进 `M5` 真实数据接入。

### 当前已知问题

- 本轮验证确认了构建成功和本地页面返回 200，但还没有在真实拼屏环境下观察修复后底部列表的现场观感。
- 如果现场仍觉得卡片内部可见条目数偏少，下一轮应继续在展示层微调卡片上下留白和列表密度，而不是回退本轮滚动容器修复。

### 下一个最优先任务

- 如果继续收口 `M4`，优先在真实左屏展示距离下确认本轮修复后底部条目是否已经完整可读；否则继续等待外部系统资料到位，按计划推进 `M5` 前置准备。

## 60. 本轮更新记录

- 本轮继续严格停留在 `M4` 左屏展示层 bug 修复范围内，不进入真实数据接入，不扩展到报修真实接入、3D 仿真或内部 Web 报表。
- frontend：
  - `frontend/src/styles.css`
  - `screen-shell` 改为纵向弹性布局，确保头部之外的页面区域使用剩余可视高度，而不是继续被内容自然撑高。
  - `screen-page` 改为 `flex: 1` 且 `min-height: 0`，允许左屏内容区在全屏时被严格限制到可见范围内。
  - 左屏 `screen-grid-left` 新增高度约束与 `grid-auto-rows: minmax(0, 1fr)`，使左屏当前这一行三张主卡片共享同一受限高度，而不是被“产量执行概览”单卡内容一起撑大。
  - 左屏卡片统一增加 `height: 100%` 与 `min-height: 0`，保证“设备概览 / 产量执行概览 / 8 小时趋势”三张卡片整体可在全屏内完整看到。
- 本轮验证结果：
  - `npm run build` 通过。
  - `GET http://127.0.0.1:3000/screen/left` 返回 200。
  - `GET http://127.0.0.1:8000/api/screens/left` 返回 200。

## 61. 本轮收尾状态

### 当前阶段

- 当前仍处于 `M4` 左屏展示层收口阶段。
- 本轮只修复“上一轮把左屏整行三张卡片一起撑高，导致全屏下无法完整看到三个模块整体”的问题。

### 本轮已完成

- 左屏整页高度现在受全屏剩余可视区域约束。
- 左屏三张主卡片现在共享同一行受限高度，不再因为产量卡片内容多而整体变高。
- “产量执行概览”仍保持列表在卡片内部滚动，不再改为一次性展开全部。
- 已完成前端构建和左屏路由/API 可访问性验证。

### 本轮未完成

- 未在真实拼屏硬件上确认本轮高度约束后的最终现场观感。
- 未接入真实外部系统。
- 未推进 `M5` 真实数据接入。

### 当前已知问题

- 本轮验证覆盖了构建成功与本地访问返回 200，但还没有在真实拼屏环境下确认全屏后这三张卡片的最终高度比例是否最优。
- 如果现场仍觉得产量卡片可视条目数过少，下一轮应继续微调卡片内部留白和单条摘要密度，而不是再放开整行高度约束。

### 下一个最优先任务

- 如果继续收口 `M4`，优先在真实左屏全屏场景下确认三张卡片整体是否都能完整看到，以及产量卡片内部滚动节奏是否合适；否则继续等待外部系统资料到位，按计划推进 `M5` 前置准备。

## 62. 本轮更新记录

- 本轮继续严格停留在 `M4` 左屏展示层优化范围内，不进入真实数据接入，不扩展到报修真实接入、3D 仿真或内部 Web 报表。
- frontend：
  - `frontend/src/ScreenDisplay.jsx`
  - 左屏“区域能耗概览”新增独立滚动引用与自动滚动判断，滚动触发阈值为区域数大于 4。
  - 左屏“近 8 小时产量趋势”卡片新增 `production-trend-panel` 布局类，使其兼容上半区趋势图 + 下半区能耗滚动区。
  - 左屏“区域能耗概览”标题区新增区域数量和“自动滚动中”状态提示。
  - 左屏“区域能耗概览”展示总能耗摘要，并在区域条目过多时于卡片内部自动滚动。
- frontend：
  - `frontend/src/styles.css`
  - 新增 `production-trend-panel`、`embedded-panel-block-fill`、`embedded-panel-summary`、`energy-list-scrollable` 等样式。
  - 左屏能耗区改为和产量概览类似的内部滚动容器，保留滚动条隐藏与自动滚动能力。
- backend：
  - `backend/backoffice/display_services.py`
  - mock 能耗区域从原先 3 条扩充为最少 8 条，便于直接验证左屏能耗区滚动。
  - 保持前 3 条区域数据口径不变，仅在后续追加 mock 区域。
- test：
  - `backend/backoffice/tests.py`
  - 同步更新总能耗断言为 `6180.00 kWh`。
  - 新增左屏能耗区域数量为 8 的断言。
- 本轮验证结果：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 32/32 通过。
  - `npm run build` 通过。
  - `python manage.py load_mock_screen_data --settings=hota_mds.test_settings` 通过。
  - `GET http://127.0.0.1:8000/api/screens/left` 返回 200，当前 `areaCount=8`，`totalConsumptionLabel=6180.00 kWh`。

## 63. 本轮收尾状态

### 当前阶段

- 当前仍处于 `M4` 左屏展示层收口阶段。
- 本轮只增强左屏“区域能耗概览”的滚动能力与 mock 验证规模，不改变项目边界。

### 本轮已完成

- 左屏能耗概览现在具备和产量概览同类的卡片内部滚动能力。
- 左屏能耗概览在区域数较多时会自动滚动。
- 左屏 mock 能耗区域已扩充到 8 条，可直接观察滚动效果。
- 已完成后端测试、前端构建、mock 装载和左屏 API 验证。

### 本轮未完成

- 未在真实拼屏硬件上完成能耗区滚动的现场终验。
- 未接入真实能耗数据库。
- 未推进 `M5` 真实数据接入。

### 当前已知问题

- 当前能耗滚动效果基于 mock/cache API 与本地浏览器环境验证，尚未在真实拼屏环境完成终验。
- 本轮 mock 能耗区域数量是为了验证滚动效果而扩充，进入真实数据接入后仍需基于真实区域数量重新验收展示密度。

### 下一个最优先任务

- 如果继续收口 `M4`，优先在真实左屏全屏场景下确认能耗区滚动节奏、单条高度和总能耗摘要位置是否合适；否则继续等待外部系统资料到位，按计划推进 `M5` 前置准备。

## 64. 本轮更新记录

- 本轮继续严格停留在 `M4` 左屏展示层微调范围内，不进入真实数据接入。
- frontend：
  - `frontend/src/ScreenDisplay.jsx`
  - 左屏“区域能耗概览”将“总能耗”从第二行摘要上移到标题行右侧，与“区域能耗概览”同一行显示。
  - 原先标题行中的“区域数量 / 自动滚动中”状态下放到下一行摘要。
- 本轮验证结果：
  - `npm run build` 通过。
  - `GET http://127.0.0.1:3000/screen/left` 返回 200。

## 65. 本轮收尾状态

### 当前阶段

- 当前仍处于 `M4` 左屏展示层收口阶段。
- 本轮只调整左屏能耗区标题与摘要的排布，不改变数据结构和项目边界。

### 本轮已完成

- 左屏“总能耗”现在与“区域能耗概览”位于同一行。
- 左屏“区域数量 / 自动滚动中”状态移动到下一行摘要。
- 已完成前端构建与左屏路由可访问性验证。

### 本轮未完成

- 未在真实拼屏硬件上完成本轮标题行排布的现场终验。
- 未接入真实外部系统。

### 当前已知问题

- 本轮只验证了本地构建和路由返回 200，尚未在真实大屏观看距离下确认标题行与摘要的最终视觉平衡。

### 下一个最优先任务

- 如果继续收口 `M4`，优先根据现场观感确认能耗区标题行、摘要和滚动列表之间的视觉层级是否还需微调；否则继续等待外部系统资料到位，按计划推进 `M5` 前置准备。

## 66. 本轮更新记录

- 本轮继续严格停留在 `M4` 右屏展示层重组范围内，不进入真实数据接入。
- frontend：
  - `frontend/src/ScreenDisplay.jsx`
  - 右屏“延期风险说明”不再作为独立模块渲染。
  - 右屏“未完工订单排产展示”模块顶部新增一行 4 状态订单数量汇总，状态为：正常、风险、延期、暂停。
  - 右屏 section 解析新增嵌入映射 `delayLegend -> schedule`，保持旧 `pageKeys/moduleSettings` 配置兼容，不会因为旧配置导致重复渲染或空白页。
  - 右屏“3D 仿真占位区”从原先独占整行改为右侧独立模块，和左侧排产模块组成左右两栏布局。
- frontend：
  - `frontend/src/styles.css`
  - 新增右屏排产模块的 4 状态横向汇总样式 `risk-summary-row` / `risk-summary-tile`。
  - 新增右屏排产模块与 3D 仿真模块的布局辅助样式 `schedule-panel` / `simulation-panel`。
  - 新增右屏风险汇总在平板和窄屏下的响应式栅格规则。
- 本轮验证结果：
  - `npm run build` 通过。
  - `GET http://127.0.0.1:3000/screen/right` 返回 200。
  - `GET http://127.0.0.1:8000/api/screens/right` 返回 200。

## 67. 本轮收尾状态

### 当前阶段

- 当前仍处于 `M4` 右屏展示层收口阶段。
- 本轮只重组右屏模块布局与风险汇总展示方式，不改变后端接口边界和真实数据接入计划。

### 本轮已完成

- 右屏由原先“三模块”改为“左排产、右仿真”两模块布局。
- “延期风险说明”独立模块已取消。
- 四个状态的订单数量汇总已并入排产模块顶部，并在同一行展示。
- 3D 仿真占位区已改为右侧独立模块，保留原有占位语义。
- 已完成前端构建和右屏路由/API 可访问性验证。

### 本轮未完成

- 未在真实拼屏硬件上完成本轮右屏新布局的现场终验。
- 未接入真实排产系统。
- 未推进 `M5` 真实数据接入。

### 当前已知问题

- 本轮验证覆盖了构建成功与本地访问返回 200，但还没有在真实拼屏场景下确认右侧 3D 占位区宽度、左侧汇总条密度和甘特图区可读性是否最优。

### 下一个最优先任务

- 如果继续收口 `M4`，优先在真实右屏全屏场景下确认：
  - 左侧 4 状态汇总条的一行密度是否合适
  - 右侧 3D 占位区宽度是否满足预期
  - 甘特图区剩余高度和可读性是否还需微调
- 否则继续等待外部系统资料到位，按计划推进 `M5` 前置准备。

## 68. 本轮更新记录

- 本轮继续严格停留在 `M4` 右屏展示层 bug 修复范围内，不进入真实数据接入。
- frontend：
  - `frontend/src/styles.css`
  - 右屏 `schedule-panel` 新增 `align-self: start`，避免左侧排产模块在两列布局下被同一行高度强制拉伸，导致底部出现大块空白。
- 本轮验证结果：
  - `npm run build` 通过。
  - `GET http://127.0.0.1:3000/screen/right` 返回 200。

## 69. 本轮收尾状态

### 当前阶段

- 当前仍处于 `M4` 右屏展示层收口阶段。
- 本轮只修复右屏排产模块底部空白问题，不改变数据结构和项目边界。

### 本轮已完成

- 右屏左侧排产模块不再被右侧占位区高度强制拉伸。
- 右屏排产模块底部的大块空白已按内容高度收口。
- 已完成前端构建与右屏路由可访问性验证。

### 本轮未完成

- 未在真实拼屏硬件上完成本轮空白修复后的现场终验。
- 未接入真实排产系统。

### 当前已知问题

- 本轮只验证了本地构建和页面返回 200，尚未在真实拼屏环境下确认左侧收口后与右侧占位区的最终视觉平衡。

### 下一个最优先任务

- 如果继续收口 `M4`，优先根据现场观感确认右屏左侧排产模块收口后的高度、右侧占位区比例和顶部四状态汇总条是否还需微调；否则继续等待外部系统资料到位，按计划推进 `M5` 前置准备。

## 70. 本轮更新记录

- 本轮继续严格停留在 `M4` 右屏展示层 bug 修复范围内，不进入真实数据接入。
- frontend：
  - `frontend/src/styles.css`
  - 回退上一轮错误的 `schedule-panel` 收口思路，不再通过缩短左侧排产模块本身来消除空白。
  - `screen-grid-right` 增加 `height: 100%`，确保右屏两列共同吃满内容区高度。
  - `schedule-panel` 和 `simulation-panel` 统一改为 `height: 100%`，保持左右两模块都到底。
  - `gantt-shell`、`gantt-board`、`gantt-rows` 改为逐层 `flex` 填满剩余高度，移除 `gantt-rows` 固定 `max-height: 460px` 的限制。
  - 右屏左侧现在是“顶部标题 + 状态汇总固定，甘特区自适应填满剩余空间并滚动”，而不是“模块整体缩短”。
- 本轮验证结果：
  - `npm run build` 通过。
  - `GET http://127.0.0.1:3000/screen/right` 返回 200。
  - `GET http://127.0.0.1:8000/api/screens/right` 返回 200。

## 71. 本轮收尾状态

### 当前阶段

- 当前仍处于 `M4` 右屏展示层收口阶段。
- 本轮修正了上一轮错误修法，改为保持右屏左侧排产模块全高，并让甘特区填满剩余空间。

### 本轮已完成

- 右屏左侧排产模块重新恢复为撑满整列高度。
- 右屏甘特图区不再受固定 `460px` 高度限制，而是填满模块剩余空间。
- 右屏左侧底部不再依赖“缩短模块本身”来消除空白。
- 已完成前端构建与右屏路由/API 可访问性验证。

### 本轮未完成

- 未在真实拼屏硬件上完成本轮正确修法后的现场终验。
- 未接入真实排产系统。

### 当前已知问题

- 本轮验证覆盖了构建成功与本地访问返回 200，但还没有在真实拼屏环境下确认甘特区填满剩余空间后的最终视觉比例是否最优。

### 下一个最优先任务

- 如果继续收口 `M4`，优先在真实右屏全屏场景下确认：
  - 甘特图区填满后的可读性是否合适
  - 右侧 3D 占位区比例是否还需微调
  - 顶部四状态汇总条与甘特图区之间的间距是否需要继续收口
- 否则继续等待外部系统资料到位，按计划推进 `M5` 前置准备。

## 72. 本轮更新记录

- 本轮严格控制为文档同步轮次：读取 `README.md` 后，按其中“开发前先读”要求对齐核心文档，不进入新功能开发。
- docs：
  - `docs/HANDOFF.md`
  - 修正“下次开发前必须先阅读的文件”中的 PRD 路径为 `docs/PRD/PRD_和泰智屏系统.md`。
  - 必读清单补齐 `docs/AGENTS.md`、`docs/DECISIONS.md`，并与 README 核心文档顺序保持一致。
  - 将过时描述“尚未把数据源健康状态接到后台前端控制台”更新为“后台前端控制台已可查看数据源健康状态”。
- docs：
  - `docs/STATUS.md`
  - 新增本轮文档同步记录与收尾状态，明确本轮未改动后端/前端实现，仅做文档一致性修正。

## 73. 本轮收尾状态

### 当前阶段

- 当前阶段仍为 `M4` 已完成、`M5` 未开始。
- 本轮仅同步文档，不改变既有里程碑边界与实现策略。

### 本轮已完成

- 已完成 `README.md` 与 `docs/HANDOFF.md` 必读清单的一致性对齐。
- 已修正 `docs/HANDOFF.md` 中过时的“数据源健康状态未接入后台”描述。
- 已在 `docs/STATUS.md`、`docs/HANDOFF.md` 补齐本轮文档同步记录，保持交接连续性。

### 本轮未完成

- 未接入真实外部系统。
- 未修改后端、前端、collector 业务代码。
- 未推进现场拼屏终验。

### 当前已知问题

- 历史文档记录跨度较长，早期阶段内容保留原时间语境；当前仅修正与 README 直接冲突的硬性不一致项。

### 下一个最优先任务

- 回到既定路线继续推进：若继续 `M4` 则做展示层现场收口；若进入下一阶段则开展 `M5` 前置准备，且继续保持前后端边界不变。

## 74. 本轮更新记录

- 本轮继续严格停留在一期前段后台配置能力范围内，只完成一个最小可交付目标：调整 OPC UA 数据源配置中的节点配置方式；不进入真实外部系统接入，不扩展到报修、3D 仿真或内部 Web 报表。
- backend：
  - `backoffice/models.py`
  - `DataSourceConfig` 新增 `node` 字段（JSON），用于存储节点 ID 列表。
- backend：
  - `backoffice/serializers.py`
  - OPC UA 的 `connection_config` 允许键中移除 `nodeId`，保留 `endpointUrl/username/password`。
  - `DataSourceConfigSerializer` 新增 `node` 字段输出与接收。
  - 对 `opcua` 类型新增校验：`node` 必须为非空字符串数组（允许空列表）。
- backend：
  - `backoffice/migrations/0014_datasourceconfig_node.py`
  - 新增迁移为 `DataSourceConfig` 增加 `node` 字段，并将历史 `connection_config.nodeId` 自动迁移到 `node` 列表首项。
- backend：
  - `backoffice/opcua_history_services.py`
  - OPC UA 历史样本优先读取 `DataSourceConfig.node[0]` 作为采样节点，兼容旧数据时仍可回退 `connection_config.nodeId`。
- backend test：
  - `backoffice/tests.py`
  - 更新数据源配置清洗测试：校验 `connection_config` 不再保存 `nodeId`，并新增 `node` 数组入库断言。
- frontend：
  - `frontend/src/adminResources.js`
  - OPC UA 配置项“节点 ID”输入框改为“节点ID列表”长文本 JSON 字段（`node`），用于录入节点数组。
- 本轮验证结果：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 执行通过。
  - `npm run build` 执行通过。

## 75. 本轮收尾状态

### 当前阶段

- 当前阶段仍为 `M4` 已完成、`M5` 未开始。
- 本轮只完成 OPC UA 数据源配置字段调整，不改变一期前段范围边界。

### 本轮已完成

- OPC UA 配置页面已将“节点ID”改为“节点ID列表”长文本录入。
- 后端数据模型已新增 `DataSourceConfig.node` JSON 字段。
- 历史 `connection_config.nodeId` 已有迁移兜底到新字段。
- 后端清洗逻辑与自动化测试已同步更新。

### 本轮未完成

- 未接入真实 OPC UA 外部系统。
- 未推进 M5 真实数据接入。
- 未改动双屏展示链路与现场拼屏验收。

### 当前已知问题

- 当前后台“节点ID列表”使用 JSON 文本录入（例如数组），录入格式不合法会在提交时触发 JSON 解析错误提示。

### 下一个最优先任务

- 若继续做后台配置收口，可补充“节点ID列表”输入模板提示与示例校验文案；否则继续按既定计划推进 M5 前置准备，并保持前端不直连外部系统。

## 76. 本轮更新记录

- 本轮继续停留在一期前段后台数据源配置能力范围内，只完成一个最小可交付目标：OPC UA“测试连接”按节点ID列表顺序读取并逐条输出结果。
- backend：
  - `backoffice/connection_test_services.py`
  - `test_opcua_connection` 新增 `node` 列表入参支持。
  - 节点读取逻辑改为按列表顺序从上到下依次读取。
  - 返回消息新增“节点读取结果（按配置顺序）”多行明细。
  - 当某个节点读取失败时，会在结果中明确标识该节点“获取失败”并附错误原因。
- backend：
  - `backoffice/views.py`
  - `POST /api/admin/data-source-configs/test-connection` 已透传请求体中的 `node` 列表到 OPC UA 测试服务。
- backend：
  - `backoffice/display_services.py`
  - 数据源连通性探测调用 OPC UA 测试逻辑时同步传入 `source.node`，保持行为一致。
- test：
  - `backoffice/tests.py`
  - 新增接口测试，验证 test-connection 会把节点列表透传给 OPC UA 测试服务，并返回顺序读取结果文案。
- 本轮验证结果：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 执行通过。
  - `npm run build` 执行通过。

## 77. 本轮收尾状态

### 当前阶段

- 当前阶段仍为 `M4` 已完成、`M5` 未开始。
- 本轮只增强 OPC UA 测试连接返回信息，不改变一期前段边界。

### 本轮已完成

- 测试连接已支持按“节点ID列表”顺序逐个读取。
- 返回信息已包含每个节点的读取结果。
- 获取失败的节点会明确显示是哪一个失败。

### 本轮未完成

- 未接入真实 OPC UA 外部系统进行现场联调。
- 未推进 M5 真实数据源接入。
- 未改动双屏展示功能。

### 当前已知问题

- 若运行环境未安装 `asyncua`，当前仍只能完成连通性与握手前置探测，无法读取节点值；此时不会产出逐节点值明细。

### 下一个最优先任务

- 若继续收口后台可用性，可在前端“测试连接”结果弹层中增强多行结果展示（当前为 toast 显示）；否则按既定计划推进 M5 前置准备。

## 78. 本轮更新记录

- 本轮继续停留在一期前段后台数据源配置范围内，只完成一个最小可交付目标：节点列表支持注释，并在 OPC UA 测试连接输出中按注释显示结果。
- backend：
  - `backoffice/serializers.py`
  - OPC UA `node` 列表新增对象格式校验，支持：
    - 字符串项（兼容旧数据）
    - 对象项 `{ nodeId, comment }`（新推荐格式）
  - 对象项要求 `nodeId/comment` 均为非空字符串。
- backend：
  - `backoffice/connection_test_services.py`
  - 节点归一化逻辑新增注释字段处理。
  - 测试连接逐节点结果改为按注释输出，不再在用户返回消息中展示详细节点路径。
  - 节点读取失败时，明确显示失败的“注释名”和错误原因。
- frontend：
  - `frontend/src/adminResources.js`
  - “节点ID列表”示例占位更新为对象数组格式（含 `nodeId` 与 `comment`）。
- test：
  - `backoffice/tests.py`
  - 更新 test-connection 透传测试，改为对象节点格式断言。
- 本轮验证结果：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 执行通过。
  - `npm run build` 执行通过。

## 79. 本轮收尾状态

### 当前阶段

- 当前阶段仍为 `M4` 已完成、`M5` 未开始。
- 本轮只增强 OPC UA 测试连接输出语义，不改变一期前段范围边界。

### 本轮已完成

- 节点列表可携带注释。
- 测试连接结果按注释顺序输出节点值。
- 获取失败时按注释名提示失败项，不回显节点详细路径。

### 本轮未完成

- 未接入真实 OPC UA 外部系统现场联调。
- 未推进 M5 真实数据接入。
- 未改动双屏展示功能。

### 当前已知问题

- 旧字符串节点格式仍兼容，但建议逐步迁移为 `{nodeId, comment}` 格式，避免输出“未命名节点”。

### 下一个最优先任务

- 若继续收口后台可用性，可补充“节点ID列表”模板自动填充与前端字段级校验提示；否则按既定计划推进 M5 前置准备。

## 80. 本轮更新记录

- 本轮继续严格停留在一期前段双屏展示范围内，只完成一个最小可交付目标：新增左屏子页面“设备实时监控”，由后端读取 OPC UA 并向前端输出监控参数。
- 范围控制：
  - 未进入内部 Web 报表。
  - 未进入报修真实接入。
  - 未进入 3D 仿真真实开发。
  - 前端仍不直连外部系统。
- backend：
  - `backoffice/connection_test_services.py`
  - 新增 `read_opcua_nodes`，支持按节点列表顺序读取实时值，输出在线/离线状态与逐项参数结果。
  - 连接超时或连接失败时返回 `offline=True`，用于前端离线展示。
- backend：
  - `backoffice/display_services.py`
  - 左屏 payload 新增 `content.deviceRealtimeMonitor`。
  - 新增 OPC UA 实时监控卡片数据拼装（按区域过滤绑定设备、按数据源读取参数）。
  - 新增 `pollIntervalSeconds`，取启用 OPC UA 数据源的最小刷新周期，默认 30 秒。
  - 新增 TK 节点语义映射，节点无注释时按 TK 路径回填“值代表什么”中文含义。
  - 左屏默认模块开关新增 `deviceRealtimeMonitor`。
- frontend：
  - `frontend/src/ScreenDisplay.jsx`
  - 新增左屏子页面 `realtime`（标签“设备实时监控”）。
  - 新增实时监控卡片渲染：设备在线/离线、更新时间、参数注释和值、失败项提示。
  - 页面轮询间隔改为可动态使用后端返回的 `pollIntervalSeconds`（下限 5 秒）。
- frontend：
  - `frontend/src/adminResources.js`
  - 左屏 page key 选项新增 `realtime`。
- frontend：
  - `frontend/src/styles.css`
  - 新增实时监控页面样式，包含卡片化布局、状态色、参数行和滚动优化。
- test：
  - `backoffice/tests.py`
  - 左屏接口测试补充断言，验证 `deviceRealtimeMonitor` 结构存在（含 `pollIntervalSeconds/cards`）。
- 本轮验证结果：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 执行通过。
  - `npm run build` 执行通过。

## 81. 本轮收尾状态

### 当前阶段

- 当前阶段仍为 `M4` 已完成、`M5` 未开始。
- 本轮在既有 M4 双屏链路内新增了左屏“设备实时监控”子页面能力。

### 本轮已完成

- 新增左屏子页面“设备实时监控”。
- 后端已可按 OPC UA 节点顺序读取参数并返回前端展示数据。
- 连接超时/连接失败的设备会标记离线并输出离线原因。
- 节点语义可由注释或 TK 路径映射给出“参数含义”。
- 前端轮询周期已按后端 OPC UA 常规刷新周期驱动。

### 本轮未完成

- 未接入新的真实外部系统类型（仅使用当前 OPC UA 数据源配置）。
- 未推进 M5 真实数据源接入全链路。
- 未做现场拼屏终验。

### 当前已知问题

- 运行环境若未安装 `asyncua`，实时值读取会降级为不可读状态，监控卡片会显示离线/失败信息。

### 下一个最优先任务

- 若继续收口 M4，优先在真实展示环境验证监控页参数密度、刷新节奏和离线提示可读性；否则按既定计划推进 M5 前置准备。

## 82. 本轮更新记录

- 本轮继续停留在 M4 展示层优化范围内，只收口“设备实时监控”卡顿与视觉表达问题，不进入真实数据接入里程碑。
- backend：
  - `backoffice/display_services.py`
  - 设备实时监控从串行读取改为并发读取（线程池），每个 OPC UA 设备/数据源异步发起请求，避免左屏等待所有设备串行完成。
  - 并发读取结果回收后按 `sourceCode` 排序，保持前端展示稳定。
- frontend：
  - `frontend/src/ScreenDisplay.jsx`
  - 实时参数展示从“纯文字列表”改为图例风格参数卡片（带状态点、标题、值）。
- frontend：
  - `frontend/src/styles.css`
  - 新增实时参数图例样式：成功/失败差异边框、状态点颜色、双列参数卡片布局，提升大屏观感。
- 本轮验证结果：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 执行通过。
  - `npm run build` 执行通过。

## 83. 本轮收尾状态

### 当前阶段

- 当前仍为 `M4` 展示层收口阶段。
- 本轮只优化实时监控页面性能与视觉呈现。

### 本轮已完成

- 设备监控读取改为并发，降低左屏等待时间。
- 参数展示改为图例化卡片，不再是简单文字列表。
- 离线/失败项继续保留醒目提示。

### 本轮未完成

- 未进入 M5 真实数据源接入。
- 未在真实拼屏环境完成终验。

### 当前已知问题

- 若单个设备节点过多，卡片信息密度仍可能偏高；后续可按分组折叠优化。

### 下一个最优先任务

- 若继续收口 M4，可将实时参数按“运行/程序/速度/报警”分组展示并加入折叠，进一步提升远距离可读性。

## 84. 本轮更新记录

- 本轮继续停留在 M4 展示层收口范围内，只处理“设备监控页面重叠、区域高度受限、视觉不够可视化”问题。
- frontend：
  - `frontend/src/ScreenDisplay.jsx`
  - 左屏实时监控页新增“实时KPI概览”可视化区（总设备/在线/离线）。
  - 当当前页仅包含 `deviceRealtimeMonitor` 时，页面进入独立实时监控布局模式，不再复用三卡片同高限制。
  - 实时监控面板增加 `panel-unbounded` 标记，避免被通用卡片高度规则挤压。
- frontend：
  - `frontend/src/styles.css`
  - 新增实时监控独立布局样式：`screen-grid-left-realtime`，去除行高限制并允许页面自然扩展滚动。
  - 实时监控卡片布局从固定三列改为自适应列 `auto-fill + minmax`，避免不同分辨率重叠。
  - 新增可视化 KPI 卡片样式与在线/离线状态色，整体风格更接近驾驶舱。
  - 实时设备卡片最小高度提升，减少信息拥挤。
- 本轮验证结果：
  - `npm run build` 执行通过。
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 执行通过。

## 85. 本轮收尾状态

### 当前阶段

- 当前仍为 M4 展示层优化阶段。
- 本轮只修复实时监控页布局与视觉，不改后端接口边界。

### 本轮已完成

- 实时监控页解除原区域高度限制，避免内容叠在一起。
- 实时监控页改为独立可视化布局，新增 KPI 概览区。
- 实时设备卡片改为响应式网格，跨分辨率更稳定。

### 本轮未完成

- 未推进 M5 真实数据接入。
- 未做真实拼屏环境最终验收。

### 当前已知问题

- 参数项非常多时，单卡片仍可能显得偏密集；后续可继续做参数分组折叠。

### 下一个最优先任务

- 若继续收口 M4，优先把参数按业务域分组展示（运行/程序/速度/报警）并增加分组卡片标题，进一步提高“高大上”可视化效果。

## 86. 本轮更新记录

- 本轮继续停留在 M4 展示层优化范围内，只处理设备监控页“分组显示 + 基础信息不轮询不展示 + 视觉升级”。
- backend：
  - `backoffice/display_services.py`
  - 新增节点分组映射，实时参数按“运行状态/程序信息/加工计时/速度与倍率/坐标信息/报警信息”分组返回。
  - 新增基础信息节点集合：基础信息节点不进入实时轮询，也不在监控页展示。
  - 保留节点注释优先策略，注释缺失时按 TK 路径自动映射中文语义。
- frontend：
  - `frontend/src/ScreenDisplay.jsx`
  - 实时设备卡片改为按分组块渲染参数，不再混合为单层列表。
  - 当节点全是基础信息时，显示“仅基础信息节点，不参与实时轮询展示”提示。
- frontend：
  - `frontend/src/styles.css`
  - 新增分组块视觉样式与分组标题，参数卡改为自适应列布局，观感与层级进一步优化。
- 本轮验证结果：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings` 通过。
  - `npm run build` 通过。

## 87. 本轮收尾状态

### 当前阶段

- 当前仍为 M4 展示层收口阶段。
- 本轮只收口设备监控页展示语义和轮询策略，不扩展项目边界。

### 本轮已完成

- 实时监控参数已分组展示。
- 基础信息参数已排除出实时轮询与展示。
- 监控页视觉层级提升，不再是混排文字列表。

### 本轮未完成

- 未推进 M5 真实数据源接入。
- 未做真实拼屏环境终验。

### 当前已知问题

- 极端参数量场景下分组卡片仍可能较多，后续可加“分组折叠”继续减压。

### 下一个最优先任务

- 若继续收口 M4，可补充分组图标与分组折叠交互，进一步提升大屏可读性。

## 88. 本轮更新记录（文档：数据真实性）

- 新增 `docs/DATA_REALITY.md`，集中说明各模块真实接入、mock 快照与占位边界。
- 更新本文档第 0 节、`README.md`、`DOCS_OVERVIEW.md`，与当前代码行为对齐（右屏 MySQL 甘特、OPC UA 监控、能耗看板 API、嵌入能耗与产量趋势快照等）。

## 89. 本轮更新记录（文档：左屏产量概览真实数据）

- 左屏「产量执行概览」在排产 MySQL 配置成功时与右屏甘特同源取数；`docs/DATA_REALITY.md`、本文档第 0 节与 `README.md` 已同步为「产量可真实、近 8 小时趋势仍为快照」的表述。

## 90. 后台 antd 重构与 Schema 维护（M-B / M-C）

### 架构现状（M-B0～M-B4，已完成）

- 路由：扁平 URL `/admin/{slug}`（react-router-dom），19 个菜单页 lazy 加载。
- 壳层：`AdminLayout` + antd Layout / Menu / Header / Sider。
- 业务：薄 `*Page.jsx` → `createResourcePage` → `ResourceCrudPage` + `useResourceCrud`。
- 构建：`vite.config.js` 拆分 `antd` / `react-vendor` chunk；详见 `docs/HANDOFF.md` §64。

### Schema 维护（M-C）

| 子项 | 状态 | 说明 |
|------|------|------|
| M-C1 Schema 拆分 | ✅ | `frontend/src/admin/schemas/`；`adminResources.js` 仅为 re-export |
| M-C2 JSDoc + 校验 | ✅ | `schemaTypes.js`、`validateResourceDefinitions.js`；`npm run validate:schemas` |
| M-C3 Tier + SOP | ✅ | 决策流程与新增页步骤见 **`docs/PLAN.md` §12**；字段字典见 **`docs/ADMIN_SCHEMA.md`** |
| M-C4 引擎扩展点 | ⏸ 未做 | Tier B 需求出现前可跳过 |
| M-C5 TS / 单测 / 注册合一 | ⏸ 未做 | 可选；当前靠 validate 脚本 |

### 新增后台页时（团队约定）

1. 按 **`docs/PLAN.md` §12.3** 选定 Tier（默认 A）。
2. 按 **§12.4** 十步 SOP 改 schema、菜单、`ADMIN_RESOURCE_KEYS`、`PAGE_LOADERS`、Page 文件。
3. 必须通过 `npm run validate:schemas` 与 `npm run build`。
4. 复杂页勿硬塞进 schema；升 Tier B/C 并在 `HANDOFF.md` 记录原因。

### 验证命令

```bash
cd frontend && npm run validate:schemas
cd frontend && npm run build
```
