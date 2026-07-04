# 和泰智造数屏系统 HANDOFF

## 1. 当前项目背景

本项目是和泰智造数屏系统，当前一期前段目标是建设面向外部客户参观的数字化工厂展示大屏。

大屏采用左右双屏展示：

- 左屏：综合运行展示。
- 右屏：生产动态展示。

一期前段只聚焦外部参观大屏，不包含内部 Web 报表。内部 Web 报表作为二期另行规划。

报修系统取数存在困难，因此报修接入作为一期后段项目。3D 仿真作为一期后段低优先级项目，优先级低于报修系统接入。

## 2. 已确认决策

### 2.1 范围决策

- 一期前段验收以设备、产量、排产、能耗稳定展示为核心。
- 报修不作为一期前段验收阻塞项。
- 3D 仿真不作为一期前段验收阻塞项。
- 内部 Web 报表不进入一期前段。

### 2.2 展示决策

- 左右屏分别使用独立 URL。
- 左右屏分别配置内容和轮播策略。
- 默认轮播时间为 60 秒，可后台配置。
- 报修未接入前显示占位。
- 3D 仿真未实施前显示预留区或占位。

### 2.3 数据决策

- 设备、产量、排产、能耗必须真实接入。
- 后端定时拉取并缓存外部系统数据。
- 前端不直接访问外部系统。
- 默认刷新频率 5 分钟，可后台配置。
- 当前外部点表和表结构未提供，允许先做标准模型、mock 数据和适配器接口。
- 数据库历史数据永久保留。

### 2.4 编码决策

- 本系统自建主数据编码。
- 其他系统编码映射到本系统主编码。
- 至少支持设备、产线、订单、物料、区域映射。

### 2.5 权限决策

- 后台需要登录。
- 一期不做复杂角色拆分。
- 默认管理员拥有全部后台配置权限。

### 2.6 异常决策

- 大屏显示最近一次成功数据。
- 大屏不提示数据过期。
- 后台显示数据源健康状态、最近成功更新时间和过期状态。

### 2.7 部署决策

- Ubuntu。
- Docker。
- MySQL 独立部署。
- 容器拆分为 backend、frontend/nginx、collector。
- 外部数据源连接信息只能在后台配置，不能写死在代码里。

## 3. 未完成事项

需求层面：

- 确认一个订单是否绝对不会同时分配到多条产线。
- 确认 WMS 是否进入一期真实接入。
- 确认拼接屏实际分辨率和浏览器环境。
- 确认后台连接信息加密方案。

外部系统资料：

- OPCUA / Modbus 点表。
- SAP RFC 字段和连接方式。
- 排产系统数据库表结构。
- 能耗数据库表结构。
- 报修系统接入方式。

实现层面：

- 已初始化 Django + DRF 后端工程骨架。
- 已初始化 React 前端工程骨架。
- 已初始化 collector 独立服务目录。
- 已新增 Docker Compose 基础部署结构。
- 已新增 `.env.example` 环境变量模板。
- 已新增 backend 基础健康检查接口 `/api/health`。
- 已新增后台管理员认证接口 `/api/admin/auth/login`、`/api/admin/auth/me`。
- 已将前端 `/admin/login` 从占位页升级为最小可用登录页。
- 已新增 M2 最小后台数据模型与管理 API。
- 已新增 M3 标准化缓存快照、mock 数据装载命令、左右屏展示 API 与左右屏前端展示页。
- 尚未接入外部系统。
- 尚未进入真实数据源驱动的大屏页面联调。
- 后台前端控制台已可查看数据源健康状态。

## 4. 下次开发前必须先阅读的文件

按顺序阅读：

1. `docs/PRD/PRD_和泰智屏系统.md`
2. `docs/SPEC.md`
3. `docs/PLAN.md`
4. `docs/STATUS.md`
5. `docs/HANDOFF.md`
6. `docs/AGENTS.md`
7. `docs/DECISIONS.md`
8. `docs/API_CONTRACT.md`
9. `docs/DB_MODEL_DRAFT.md`
10. `docs/IMPLEMENTATION_PLAN.md`
11. `README.md`

## 5. 建议下一轮优先任务

下一轮建议在保持 M4 稳定的前提下，准备进入 M5，但仍不要让前端直接接外部系统。

建议顺序：

1. 保持现有 `/api/screens/left`、`/api/screens/right`、屏幕配置和双屏 UI 稳定，不做无必要重构。
2. 在外部系统资料到位后进入 M5，由后端/collector 负责真实数据源接入、标准化和缓存。
3. 前端继续只依赖后端标准化 API，不接触外部原始结构。
4. 报修、3D 仿真和内部 Web 报表仍继续排除在当前优先级之外。

## 6. 特别注意

- 不要把报修和 3D 仿真做成一期前段阻塞项。
- 不要把内部 Web 报表纳入一期前段。
- 不要让前端直连外部系统。
- 不要把外部系统连接信息写死在代码中。
- 不要在大屏端显示“数据过期”提示。
- 在外部点表和表结构未提供前，先做标准模型、mock 数据和适配器接口。
- 数据库历史数据要求永久保留，后续设计归档和清理策略时不得默认删除历史数据。

## 7. 本轮交接记录

- 本轮新增 `docs/IMPLEMENTATION_PLAN.md`，用于记录一期前段开发实施 WBS。
- 文档按 M0、M1、M2、M3、M4、M6、M5、UAT 拆分，并将 M7 报修、M8 3D 仿真、M9 内部 Web 报表列为后续阶段。
- 后续开发建议先按 `docs/IMPLEMENTATION_PLAN.md` 的推荐顺序推进，优先完成 M0 到 M1，不直接接外部系统。

## 8. 本轮交接记录

- 本轮新增 `docs/API_CONTRACT.md` 与 `docs/DB_MODEL_DRAFT.md`。
- API 契约草案覆盖后台登录、台账维护、编码映射、左右屏配置、数据源配置、数据源健康状态、左屏展示数据、右屏展示数据。
- 数据模型草案覆盖主数据、编码映射、标准缓存模型、数据源配置、左右屏配置、页面模块开关、操作日志。
- 后续进入工程实现前，应先基于这两份草案确认歧义问题，尤其是订单与产线关系、近 8 小时产量统计口径、延期预测阈值、能耗统计口径和连接信息加密方案。

## 9. 本轮交接记录

- 本轮完成 M1 工程骨架与基础部署，不包含任何真实业务功能或真实外部系统接入。
- 新增 backend、frontend、collector、Docker Compose、`.env.example` 和 README。
- backend 使用 Django + DRF，并通过环境变量配置 MySQL；未写死任何外部系统连接信息。
- frontend 使用 React，并提供 `/screen/left`、`/screen/right`、`/admin/login` 三个占位路由。
- collector 目前仅为独立服务占位和心跳输出，不连接 OPCUA、Modbus、SAP、排产库、能耗库或报修系统。
- frontend 的 Vite 仅作为 React 构建工具使用，不代表引入新的业务技术栈。
- 本地验证已通过 Python 语法编译、Docker Compose 配置解析和 `package.json` JSON 校验。
- 当前 Docker Desktop/Linux engine 未运行，容器启动、MySQL 实际连接和 `/api/health` 运行时访问尚未完成。
- 当前 npm 依赖安装多次超时，未生成 `node_modules` 或 `package-lock.json`；后续在网络或 registry 可用时需重新执行前端依赖安装与构建验证。

## 10. 本轮交接记录

- 本轮进入 M2，并完成“管理员登录最小可交付目标”。
- backend 新增 `accounts` 应用，提供 `/api/admin/auth/login` 与 `/api/admin/auth/me`。
- 认证策略为最小实现：校验 Django 用户名密码，仅允许 `is_staff` 用户登录，返回带签名的短期令牌。
- 本轮未引入复杂权限体系，未实现后台业务配置页，符合一期不做复杂角色拆分的约束。
- frontend 的 `/admin/login` 已支持账号密码提交、会话令牌存储、当前管理员信息读取与清除会话。
- 新增 `frontend/vite.config.js`，开发环境下 `/api` 代理到 backend，便于本地联调。
- 本轮验证已通过后端编译、4 条认证测试、前端 `npm install`、前端生产构建，以及基于 `hota_mds.test_settings` 的本地登录链路实测。
- `hota_mds.test_settings` 仅用于本地测试与验证；项目正式约束仍然是 Django + DRF + MySQL，不应误用为生产配置。

## 11. 本轮交接记录

- 本轮范围严格限制在 M2 最小后台能力，不进入大屏展示、不接真实数据源、不做报修、不做 3D 仿真、不做内部报表。
- backend 新增 `backoffice` 应用，落地了区域、产线、设备、编码映射、左右屏配置、数据源配置、操作日志等模型与 API。
- 后台接口统一走管理员 Bearer Token 鉴权，保持与 `/api/admin/auth/login`、`/api/admin/auth/me` 一致的管理域风格。
- 数据源配置支持两类敏感信息保护结构：
  - `env_ref`：通过环境变量名引用敏感值
  - `encrypted`：预留密文和密钥版本字段
- 数据源配置接口不会在返回结果和操作日志中暴露敏感密文或敏感键值内容。
- 操作日志已覆盖管理员登录、创建、更新、删除四类基础动作，便于后续后台审计。
- 本轮新增统一异常处理器，后台管理接口在常见错误场景下也返回一致的 `success/code/message/data` 结构。
- 本轮自动化验证已通过：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings`
  - 9 个测试全部通过
- 本轮运行态冒烟验证已通过：
- 管理员登录接口返回 200
- 区域创建接口返回 201
- 操作日志列表可正常返回
- 下一轮更适合继续留在 M2，补后台页面入口、参数配置、模块开关等，使这批 API 真正可维护；不要直接跳到 M3/M4。

## 12. 本轮交接记录

- 本轮继续停留在 M2，补齐了后台参数配置能力，没有进入大屏展示，也没有接真实数据源。
- backend 新增两个配置模型：
  - `DisplayContentConfig`：欢迎语、Logo、宣传图片等展示内容
  - `RuntimeParameterConfig`：单日有效工作时间、标准产能、延期预警缓冲、甘特窗口、自动滚动阈值、产量窗口等运行参数
- backend 新增两个管理接口：
  - `/api/admin/display-content-configs`
  - `/api/admin/runtime-parameter-configs`
- 现有 `ScreenConfig` 继续负责左右屏自身配置；本轮新增配置更偏全局参数与欢迎展示内容。
- `ScreenConfigSerializer` 已补结构校验，要求 `pageKeys` 为数组、`moduleSettings`/`themeSettings` 为对象。
- 本轮新增迁移文件 `backoffice/migrations/0002_displaycontentconfig_runtimeparameterconfig.py`。
- 本轮自动化验证已通过：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings`
  - 11 个测试全部通过
- 本轮运行态冒烟验证已通过：
- 管理员登录接口返回 200
- 展示内容配置创建接口返回 201
- 运行参数配置创建接口返回 201
- 下一轮最适合继续留在 M2，把这批后台 API 接到最小管理界面上，或者补 Django Admin 运维入口；之后再进入 M3。

## 13. 本轮交接记录

- 本轮继续按 M2 边界工作，没有进入大屏展示，也没有接真实数据源。
- frontend 新增最小后台前端界面：
  - `/admin/login`：管理员登录页
  - `/admin/console`：后台控制台
- 控制台已接入以下资源的最小维护能力：
- 区域台账
- 产线台账
- 设备台账
- 员工台账
- 编码映射
  - 左右屏配置
  - 欢迎展示配置
  - 运行参数配置
  - 数据源配置
  - 操作日志查看
- 前端继续通过本系统后端 API 工作，没有直连 SAP、排产库、能耗库、OPCUA、Modbus 或其他外部系统。
- 本轮本地验证已通过：
- `npm run build`
- `/admin/console` 路由可访问
- backend 健康检查接口可访问
- `python manage.py test accounts backoffice --settings=hota_mds.test_settings`
- 到当前为止，M2 的“最小后台能力 + 最小后台界面”已基本具备，下一轮更适合进入 M3，开始标准展示数据模型、缓存层与 mock 展示 API。

## 15. 本轮交接记录

- 本轮根据数据库结构审阅意见补充了员工台账。
- backend 新增员工模型 `Employee`，当前字段范围严格收敛为：
  - `employee_no`
  - `name`
  - `role`
  - `is_active`
  - `notes`
- 员工号当前仅允许英文和数字，不允许连字符、空格或其他特殊字符。
- 员工角色当前固定为三类：
  - `employee`
  - `team_leader`
  - `supervisor`
- frontend 后台控制台已新增“员工台账”入口，可直接管理该表。
- docs 已同步补录到：
  - `docs/DECISIONS.md`
  - `docs/DB_MODEL_DRAFT.md`
  - `docs/API_CONTRACT.md`

## 14. 本轮交接记录

- 已新增 `docs/DECISIONS.md`，专门记录开发过程中“为什么这样实现”的技术决策。
- 这份文档用于补充 `STATUS.md` 和 `HANDOFF.md` 不便展开说明的实现背景，后续有新的架构、认证、缓存、配置、安全、前后端协作等决策时都应继续追加。
## 16. 本轮收尾交接

### 本轮目标

- 根据数据库结构审阅结果，补充缺失的员工表和员工台账。
- 员工号支持英文及数字。
- 增加员工角色字段，范围限定为员工、班组长、主管。
- 完成后同步更新状态、交接和决策文档。

### 本轮实际完成

- 后端新增 `Employee` 模型与迁移文件。
- 员工号字段 `employee_no` 已限制为仅允许英文和数字。
- 角色字段 `role` 已固定为 `employee`、`team_leader`、`supervisor`。
- 新增员工台账接口 `/api/admin/employees`，纳入管理员鉴权和基础操作日志。
- 前端后台控制台新增“员工台账”资源入口。
- 已更新 `STATUS.md`、`HANDOFF.md`、`DECISIONS.md`、`API_CONTRACT.md`、`DB_MODEL_DRAFT.md`。
- 已完成编译、测试、迁移和接口冒烟验证。

### 本轮未完成

- 未扩展员工与部门、班组、管理员账号的关联关系。
- 未增加员工导入导出、批量维护能力。
- 未进入 M3 的缓存模型、mock 展示数据和左右屏展示 API。
- 未接入真实数据源。

### 修改文件清单

- `backend/backoffice/models.py`
- `backend/backoffice/serializers.py`
- `backend/backoffice/views.py`
- `backend/backoffice/urls.py`
- `backend/backoffice/tests.py`
- `backend/backoffice/migrations/0003_employee.py`
- `frontend/src/adminResources.js`
- `docs/API_CONTRACT.md`
- `docs/DB_MODEL_DRAFT.md`
- `docs/DECISIONS.md`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 本轮未发现员工模型或接口设计上的阻塞性问题。
- 在本地 shell 冒烟验证时，`APIClient` 默认 host 会触发 400，请显式传入 `HTTP_HOST=localhost` 后再执行接口链路验证。
- 当前联调仍以 `hota_mds.test_settings` 为主，尚未在正式 MySQL 环境完成实际验证。

### 建议下一轮优先任务

- 按既定计划进入 M3，先做标准化缓存模型、mock 数据装载和左右屏展示 API。
- 第一优先级是把“最近一次成功数据兜底”机制做进缓存和展示接口，继续保持不接真实外部系统。

## 17. 本轮交接记录

- 本轮已正式从 M2 收尾推进到 M3 的第一个最小可交付目标。
- 后端新增 5 类标准化缓存快照模型：
  - `DeviceStatusSnapshot`
  - `ProductionSnapshot`
  - `ScheduleSnapshot`
  - `EnergySnapshot`
  - `DataSourceHealthSnapshot`
- 后端新增 `backoffice/display_services.py`，统一处理 mock 数据生成、快照装载、默认配置兜底和左右屏展示数据拼装。
- 后端新增公开展示接口：
  - `/api/screens/left`
  - `/api/screens/right`
- 后端新增后台只读健康状态接口：
  - `/api/admin/data-source-healths`
- 后端新增管理命令：
  - `python manage.py load_mock_screen_data`
  - `python manage.py load_mock_screen_data --simulate-failure`
- 当前兜底策略已经落地：
  - mock 刷新成功时更新快照和数据源健康状态
  - mock 刷新失败时仅更新健康状态为失败，不覆盖原快照
  - 左右屏展示接口继续返回最近一次成功快照，并通过 `meta.usingFallback` 表示当前处于兜底
- 本轮没有接任何真实外部系统，没有实现报修真实数据，没有实现 3D 仿真，没有进入内部 Web 报表。
- 本轮验证已通过：
  - `python -m compileall backoffice hota_mds`
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings`
  - `npm run build`
  - `python manage.py migrate --settings=hota_mds.test_settings`
  - `python manage.py load_mock_screen_data --settings=hota_mds.test_settings`
  - 本地读取 `/api/screens/left`、`/api/screens/right` 均成功
  - 执行 `python manage.py load_mock_screen_data --simulate-failure --settings=hota_mds.test_settings` 后，右屏接口仍成功返回，且 `meta.usingFallback=True`
- 本轮修改文件清单：
  - `backend/backoffice/models.py`
  - `backend/backoffice/serializers.py`
  - `backend/backoffice/views.py`
  - `backend/backoffice/urls.py`
  - `backend/backoffice/display_services.py`
  - `backend/backoffice/tests.py`
  - `backend/backoffice/management/commands/load_mock_screen_data.py`
  - `backend/backoffice/migrations/0004_datasourcehealthsnapshot_devicestatussnapshot_and_more.py`
  - `backend/hota_mds/urls.py`
  - `docs/STATUS.md`
  - `docs/HANDOFF.md`

## 18. 本轮交接记录

- 本轮继续停留在 M3，并完成了第二个最小可交付目标：左右屏前端展示页正式接入标准展示 API，不再停留在占位页。
- frontend 新增 `src/ScreenDisplay.jsx`，按 `screenKey` 区分左屏和右屏展示：
  - 左屏展示欢迎信息、设备运行概览、产量执行概览、近 8 小时产量趋势、区域能耗概览和报修占位区
  - 右屏展示未完工订单排产、延期风险概览和 3D 仿真预留区
- frontend `src/App.jsx` 已切换为在 `/screen/left`、`/screen/right` 直接渲染真实屏幕组件。
- frontend `src/styles.css` 已新增大屏样式，当前以全屏深色展示布局为主，适配桌面与窄屏场景。
- 前端当前也实现了最小白屏保护：
  - 首次加载成功后，如果后续接口请求失败，页面继续保留上一次成功内容
  - 页面顶部会显示当前是否处于兜底数据展示中
- 本轮没有改动后台管理 API 的行为，没有接真实外部系统，没有做报修真实接入，没有做 3D 仿真真实开发。
- 本轮验证已通过：
  - `npm run build`
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings`
  - `http://127.0.0.1:8000/api/screens/left` 返回 200
  - `http://127.0.0.1:3000/screen/left` 返回 200
  - `http://127.0.0.1:3000/screen/right` 返回 200
- 本轮本地运行地址：
  - 前端：`http://127.0.0.1:3000/screen/left`
  - 前端：`http://127.0.0.1:3000/screen/right`
  - 后端展示 API：`http://127.0.0.1:8000/api/screens/left`
  - 后端展示 API：`http://127.0.0.1:8000/api/screens/right`
- 本轮修改文件清单：
  - `frontend/src/App.jsx`
  - `frontend/src/ScreenDisplay.jsx`
  - `frontend/src/styles.css`
  - `docs/STATUS.md`
  - `docs/HANDOFF.md`

## 19. 本轮交接记录

- 本轮修复了左右屏在 IAB/浏览器内打开时白屏的问题。
- 问题根因：
  - 前端当前没有接入 `@vitejs/plugin-react`
  - Vite/esbuild 仍按经典 JSX 运行时输出 `React.createElement(...)`
  - 但项目中的 `.jsx` 文件并没有统一把 `React` 注入到运行时作用域
  - 页面打开后直接报错 `React is not defined`，导致只剩网页标题，`#root` 里没有内容
- 修复措施：
  - 在 `frontend/vite.config.js` 中增加 `esbuild.jsxInject = 'import React from "react"'`
  - 在 `frontend/src/main.jsx` 中将根节点包裹改为 `StrictMode`
  - 重启前端 dev 服务和 preview 服务，使新配置生效
- 验证结果：
  - 通过无头浏览器抓到旧报错：`React is not defined`
  - 修复并重启后，再次使用无头浏览器验证：
    - `http://127.0.0.1:3000/screen/left` 已能渲染正文
    - `http://127.0.0.1:4173/screen/left` 已能渲染正文
  - 当前仍可见一条 404 资源日志，但不影响页面主内容渲染，属于非阻塞问题
- 本轮修改文件清单：
  - `frontend/src/main.jsx`
  - `frontend/vite.config.js`
  - `docs/STATUS.md`
  - `docs/HANDOFF.md`

## 20. 本轮交接记录

- 本轮继续停留在 M3，目标是把“数据源健康状态”接到现有后台控制台，不涉及真实数据接入。
- backend 调整：
  - `GET /api/admin/data-source-healths` 现在在健康快照还不存在时会自动调用 mock 快照装载逻辑
  - 这样后台第一次进入健康状态页时，不需要先手工执行 `load_mock_screen_data`
- backend 测试补充：
  - 新增健康状态接口自动补装 mock 快照的测试
- frontend 调整：
  - `frontend/src/adminResources.js` 新增只读资源 `dataSourceHealths`
  - `frontend/src/AdminConsole.jsx` 已重写为干净版本，去掉历史乱码字符串，并支持按资源显示对应详情标题
  - 后台控制台现在可直接查看数据源健康状态列表和详情
- 本轮验证已通过：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings`
  - `npm run build`
  - 本地实测 `GET /api/admin/data-source-healths` 返回 200 且 `total=4`
  - `http://127.0.0.1:3000/admin/console` 返回 200
- 本轮修改文件清单：
  - `backend/backoffice/views.py`
  - `backend/backoffice/tests.py`
  - `frontend/src/adminResources.js`
  - `frontend/src/AdminConsole.jsx`
  - `docs/STATUS.md`
  - `docs/HANDOFF.md`

## 21. 本轮交接记录

- 本轮继续停留在 M3，只做后台“数据源健康”页面的可读性优化，不扩展到真实数据源接入。
- frontend 调整：
  - 重写 `frontend/src/adminResources.js`，清理历史乱码资源定义
  - 为“数据源健康”资源补充表格格式化和详情格式化
  - `frontend/src/AdminConsole.jsx` 现已支持按资源定制表格单元格显示和只读详情显示
- 当前“数据源健康”页的展示效果：
  - 状态字段显示为“正常/失败”
  - 布尔字段显示为“是/否”
  - 时间字段显示为 `YYYY-MM-DD HH:mm:ss`
  - 详情面板按名称、来源键、状态、最近成功、最近尝试、是否过期、是否使用兜底、错误信息、附加信息分项展示
- 本轮验证已通过：
  - `npm run build`
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings`
  - 使用无头浏览器登录后台后进入“数据源健康”，列表和详情均按新的友好格式展示
- 本轮修改文件清单：
  - `frontend/src/adminResources.js`
  - `frontend/src/AdminConsole.jsx`
  - `docs/STATUS.md`
  - `docs/HANDOFF.md`

## 22. 本轮交接记录

- 本轮目标：清理一期双屏展示与后台入口中仍残留的历史乱码，并修复左屏欢迎语/公司名显示为 `?` 的问题。
- 范围控制：
  - 没有接入真实外部系统
  - 没有进入报修真实接入
  - 没有做 3D 仿真开发
  - 没有进入内部 Web 报表
- frontend 调整：
  - 重写 `frontend/src/AdminApp.jsx`，清理登录页与状态提示文案中的历史乱码
  - 重写 `frontend/src/App.jsx`，清理根路由占位页标题与副标题文案
  - 重写 `frontend/src/PlaceholderScreen.jsx`，清理快速入口区域的无障碍标签文案
- backend 调整：
  - `backend/backoffice/display_services.py` 新增展示文案兜底逻辑
  - 当激活中的 `DisplayContentConfig.company_name` 或 `welcome_message` 只包含问号时，左/右屏接口自动回退到默认文案，而不是继续把坏值直接返回给前端
- 测试补充：
  - `backend/backoffice/tests.py` 新增用例，验证左屏接口在展示配置为 `????` / `????????` 时仍返回默认欢迎语和公司名
- 本地环境处理：
  - 已将当前 `hota_mds.test_settings` 测试库中 `DisplayContentConfig(config_key='default')` 的坏值修正为正常中文，当前运行中的 `127.0.0.1:8000` 服务已恢复正常输出
- 本轮验证已通过：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings`
  - `npm run build`
  - `GET http://127.0.0.1:8000/api/screens/left`
  - 无头浏览器验证 `http://127.0.0.1:3000/admin/login`
  - 无头浏览器验证 `http://127.0.0.1:3000/screen/left`
- 当前可直接访问：
  - 前端左屏：`http://127.0.0.1:3000/screen/left`
  - 前端右屏：`http://127.0.0.1:3000/screen/right`
  - 后台登录：`http://127.0.0.1:3000/admin/login`
  - 后端左屏 API：`http://127.0.0.1:8000/api/screens/left`
- 下一步建议：
  - 继续留在 M3，优先把双屏剩余展示文案与状态枚举做一轮统一整理，确保外部参观双屏所有可见字段都来自稳定、可控的后端标准化输出
- 本轮修改文件清单：
  - `backend/backoffice/display_services.py`
  - `backend/backoffice/tests.py`
  - `frontend/src/AdminApp.jsx`
  - `frontend/src/App.jsx`
  - `frontend/src/PlaceholderScreen.jsx`
  - `docs/STATUS.md`
  - `docs/HANDOFF.md`

## 23. 本轮交接记录

- 本轮目标：把一期双屏中仍暴露给参观者的原始状态枚举收敛为后端标准化展示字段，让前端只负责渲染。
- 范围控制：
  - 没有接入真实外部系统
  - 没有进入报修真实接入
  - 没有做 3D 仿真开发
  - 没有进入内部 Web 报表
- backend 调整：
  - `backend/backoffice/display_services.py` 新增设备状态展示映射 `DEVICE_STATUS_DISPLAY`
  - 左屏 `deviceOverview` 新增 `statusItems`，标准输出“运行/停机/报警/离线”及对应数量与视觉强调色
  - 右屏 `schedule.riskSummary` 新增 `items`，标准输出“正常/风险/延期/暂停”及对应数量、颜色、视觉强调色
  - 为一期后段占位模块补充说明文案：
    - `repairPlaceholder.description`
    - `simulationPlaceholder.description`
- frontend 调整：
  - 重写 `frontend/src/ScreenDisplay.jsx`
  - 左屏设备状态区不再遍历原始 `statusBreakdown` 键，而是直接渲染后端给出的 `statusItems`
  - 右屏风险概览不再在前端硬编码风险标签，而是直接渲染后端给出的 `riskSummary.items`
  - 报修占位和 3D 预留区改为直接显示接口返回的说明文案
- 测试补充：
  - `backend/backoffice/tests.py` 补充断言，验证：
    - 左屏接口会返回标准化 `statusItems`
    - 左屏接口会返回 `repairPlaceholder.description`
    - 右屏接口会返回标准化 `riskSummary.items`
    - 右屏接口会返回 `simulationPlaceholder.description`
- 本轮验证已通过：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings`
  - `npm run build`
  - `GET http://127.0.0.1:8000/api/screens/left`
  - `GET http://127.0.0.1:8000/api/screens/right`
  - 无头浏览器验证 `http://127.0.0.1:3000/screen/left`
  - 无头浏览器验证 `http://127.0.0.1:3000/screen/right`
- 当前验证结果：
  - 左屏设备状态已经显示为“运行/停机/报警/离线”，不再出现 `running/stopped/alarm/offline`
  - 右屏风险汇总已经显示为“正常/风险/延期/暂停”
  - 右屏 3D 预留区说明文案显示正常
- 下一步建议：
  - 继续留在 M3，优先把双屏剩余动态字段的展示命名也统一收口到后端标准化输出，进一步降低前端拼装和解释业务含义的比例
- 本轮修改文件清单：
  - `backend/backoffice/display_services.py`
  - `backend/backoffice/tests.py`
  - `frontend/src/ScreenDisplay.jsx`
  - `docs/STATUS.md`
  - `docs/HANDOFF.md`

## 24. 暂停前交接摘要

### 本轮目标

- 在不扩展一期范围的前提下，把双屏中仍直接暴露给参观者的原始状态枚举收敛为后端标准化展示字段。

### 本轮实际完成

- 后端新增左屏设备状态展示映射，接口返回 `statusItems`。
- 后端新增右屏风险汇总展示映射，接口返回 `riskSummary.items`。
- 后端为报修占位和 3D 预留区补充说明文案字段。
- 前端重写 `frontend/src/ScreenDisplay.jsx`，改为直接消费后端标准化字段。
- 已完成 `python manage.py test accounts backoffice --settings=hota_mds.test_settings`、`npm run build`、左右屏接口读取和浏览器冒烟验证。

### 本轮未完成

- 未接入真实外部系统。
- 未进入内部 Web 报表。
- 未做报修真实接入。
- 未做 3D 仿真真实开发。
- 未完成双屏其余动态字段的全部标准化收口。

### 修改文件清单

- `backend/backoffice/display_services.py`
- `backend/backoffice/tests.py`
- `frontend/src/ScreenDisplay.jsx`
- `docs/STATUS.md`
- `docs/HANDOFF.md`
- `docs/DECISIONS.md`

### 遇到的问题

- 双屏展示链路中仍有部分字段历史上由前端自行解释状态含义，不符合“后端负责标准化、前端负责展示”的项目规则。
- 文档早期历史内容存在编码乱码，阅读体验较差，但不影响本轮新增记录和继续交接。
- 当前验证环境仍以本地 mock + `hota_mds.test_settings` 为主，尚未具备真实外部系统联调依据。

### 建议下一轮优先任务

- 继续留在 M3，优先把双屏剩余动态字段的展示名称、状态枚举和提示语继续统一收敛到后端标准化输出。

## 25. 本轮交接记录

- 本轮目标：继续留在 M3，把右屏排产卡片里仍由前端自行解释的动态展示字段收口到后端标准化输出。
- 范围控制：
  - 没有接入真实外部系统
  - 没有进入报修真实接入
  - 没有做 3D 仿真开发
  - 没有进入内部 Web 报表
- backend 调整：
  - `backend/backoffice/display_services.py` 为右屏排产订单新增 `display` 字段
  - 每个订单当前会直接返回：
    - `riskLabel`
    - `riskAccent`
    - `timeRangeLabel`
    - `completionRateLabel`
  - 原始 `riskStatus`、`displayStartAt`、`displayEndAt`、`completionRate` 仍保留在快照中，作为兼容字段存在，但右屏展示不再依赖它们拼装文案
- frontend 调整：
  - `frontend/src/ScreenDisplay.jsx` 改为渲染 `order.display`
  - 右屏排产卡片顶部现在直接显示后端给出的风险标签
  - 时间区间与完成率文案改为直接显示后端给出的格式化文本
  - `frontend/src/styles.css` 将卡片视觉强调从 `risk-*` 切换为 `accent-*`，与后端标准化语义保持一致
- 测试补充：
  - `backend/backoffice/tests.py` 新增断言，验证右屏接口会返回订单级 `display` 字段，并且其内容与原始快照字段一致
- 本轮验证已通过：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings`
  - `npm run build`
  - 基于 `hota_mds.test_settings` 的接口冒烟校验 `GET /api/screens/right`
- 当前验证结果：
  - 右屏首个订单已返回 `display.riskLabel='正常'`
  - 右屏首个订单已返回 `display.riskAccent='green'`
  - 右屏首个订单已返回格式化后的 `display.timeRangeLabel` 与 `display.completionRateLabel`
  - 说明右屏排产卡片的展示语义已进一步从前端收口到后端
- 本轮修改文件清单：
  - `backend/backoffice/display_services.py`
  - `backend/backoffice/tests.py`
  - `frontend/src/ScreenDisplay.jsx`
  - `frontend/src/styles.css`
  - `docs/STATUS.md`
  - `docs/HANDOFF.md`
- 下一步建议：
  - 继续留在 M3，优先检查左屏产量概览、右屏排产列表和图例里是否还有前端自行拼接的展示字段，继续按同样方式收口到后端标准化输出

## 26. 本轮交接记录

- 本轮目标：继续留在 M3，把左屏“产量执行概览”里仍由前端自行拼接的展示语义收口到后端标准化输出。
- 范围控制：
  - 没有接入真实外部系统
  - 没有进入报修真实接入
  - 没有做 3D 仿真开发
  - 没有进入内部 Web 报表
- backend 调整：
  - `backend/backoffice/display_services.py` 为左屏产量概览新增 `productionOverview.display`
  - 同时为 `productionOverview.lineSummaries` 中的每条产线新增 `display` 字段
  - 当前标准化展示字段包括：
    - `overallCompletionRateLabel`
    - `totalTargetQuantityLabel`
    - `totalProducedQuantityLabel`
    - `currentOrderLabel`
    - `targetQuantityLabel`
    - `producedQuantityLabel`
    - `completionRateLabel`
  - 原始 `totalTargetQuantity`、`totalProducedQuantity`、`overallCompletionRate`、`currentOrderCode`、`targetQuantity`、`producedQuantity`、`completionRate` 仍保留，作为兼容字段存在
- frontend 调整：
  - `frontend/src/ScreenDisplay.jsx` 改为优先渲染后端给出的产量概览标准化字段
  - 左屏产量概览标题处的完成率文案改为使用 `productionOverview.display.overallCompletionRateLabel`
  - 左屏两张总量指标卡改为优先使用 `totalTargetQuantityLabel` / `totalProducedQuantityLabel`
  - 左屏产线摘要列表改为优先渲染 `lineSummaries[].display`，不再在前端拼接“当前订单 / 目标 / 已产 / %”
- 测试补充：
  - `backend/backoffice/tests.py` 新增断言，验证左屏接口会返回 `productionOverview.display`
  - 同时验证首条产线会返回 `lineSummaries[0].display`
- 本轮验证已通过：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings`
  - `npm run build`
  - 基于 `hota_mds.test_settings` 的接口冒烟校验 `GET /api/screens/left`
- 当前验证结果：
  - 左屏产量概览已返回 `overallCompletionRateLabel='85.58%'`
  - 左屏产量概览已返回 `totalTargetQuantityLabel='3120'`
  - 左屏产量概览已返回 `totalProducedQuantityLabel='2670'`
  - 首条产线已返回 `display.currentOrderLabel='当前订单 MO-001'`
  - 首条产线已返回 `display.targetQuantityLabel='目标 920'`
  - 首条产线已返回 `display.producedQuantityLabel='已产 785'`
  - 首条产线已返回 `display.completionRateLabel='85.33%'`
  - 说明左屏产量概览展示语义已进一步从前端收口到后端
- 本轮修改文件清单：
  - `backend/backoffice/display_services.py`
  - `backend/backoffice/tests.py`
  - `frontend/src/ScreenDisplay.jsx`
  - `docs/STATUS.md`
  - `docs/HANDOFF.md`
- 下一步建议：
  - 继续留在 M3，优先检查左屏趋势区、区域能耗区、右屏图例与排产明细里是否还有前端自行拼接的展示字段，继续按“后端标准化、前端渲染”的方式逐步收口

## 27. 本轮交接记录

- 本轮目标：继续留在 M3，把左屏“区域能耗概览”里仍由前端自行做数值格式化和单位拼接的展示语义收口到后端标准化输出。
- 范围控制：
  - 没有接入真实外部系统
  - 没有进入报修真实接入
  - 没有做 3D 仿真开发
  - 没有进入内部 Web 报表
- backend 调整：
  - `backend/backoffice/display_services.py` 为左屏能耗概览新增 `energyOverview.display`
  - 同时为 `energyOverview.areaSummaries` 中的每个区域新增 `display` 字段
  - 当前标准化展示字段包括：
    - `totalConsumptionLabel`
    - `consumptionLabel`
  - 原始 `totalConsumption`、`unit`、`consumption` 字段仍保留，作为兼容字段存在
- frontend 调整：
  - `frontend/src/ScreenDisplay.jsx` 改为优先渲染后端给出的能耗概览标准化字段
  - 左屏区域能耗标题处的总能耗文案改为优先使用 `energyOverview.display.totalConsumptionLabel`
  - 左屏分区能耗列表改为优先渲染 `areaSummaries[].display.consumptionLabel`
- 测试补充：
  - `backend/backoffice/tests.py` 新增断言，验证左屏接口会返回 `energyOverview.display`
  - 同时验证首个区域会返回 `areaSummaries[0].display`
- 本轮验证已通过：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings`
  - `npm run build`
  - 基于 `hota_mds.test_settings` 的接口冒烟校验 `GET /api/screens/left`
- 当前验证结果：
  - 当前本地测试数据下，左屏能耗概览已返回 `totalConsumptionLabel='545.00 kWh'`
  - 当前本地测试数据下，首个区域已返回 `consumptionLabel='545.00 kWh'`
  - 自动化测试中的全新测试库也已验证默认 mock 结构会返回 `energyOverview.display` 与区域级 `display`
  - 说明左屏能耗概览展示语义已进一步从前端收口到后端
- 本轮修改文件清单：
  - `backend/backoffice/display_services.py`
  - `backend/backoffice/tests.py`
  - `frontend/src/ScreenDisplay.jsx`
  - `docs/STATUS.md`
  - `docs/HANDOFF.md`
- 下一步建议：
  - 继续留在 M3，优先检查左屏趋势区和右屏图例中是否还有前端自行拼接的展示字段，继续按“后端标准化、前端渲染”的方式逐步收口

## 29. 本轮交接记录

- 本轮目标：完成 M3 收尾，把双屏剩余可见动态字段全部收口到后端标准化输出，并确认 M3 验收条件已经满足。
- 范围控制：
  - 没有接入真实外部系统
  - 没有进入报修真实接入
  - 没有做 3D 仿真开发
  - 没有进入内部 Web 报表
- backend 调整：
  - `backend/backoffice/display_services.py` 新增 `meta.display.lastSuccessfulAtLabel`
  - 左屏 `deviceOverview.statusItems[]` 新增 `countLabel`
  - 左屏 `productionTrend[]` 新增 `display.timeLabel` 与 `display.producedQuantityLabel`
  - 右屏 `schedule.display` 新增 `windowDaysLabel`
  - 右屏 `schedule.riskSummary.items[]` 新增 `countLabel`
  - 原始 `lastSuccessfulAt`、`count`、`hourLabel`、`producedQuantity`、`windowDays` 等字段仍保留，作为兼容字段存在
- frontend 调整：
  - `frontend/src/ScreenDisplay.jsx` 改为优先渲染后端给出的剩余标准化展示字段
  - 左右屏状态栏不再自行格式化最近成功时间
  - 左屏状态分解和趋势图不再自行格式化数量文案
  - 右屏排产窗口与风险概览计数不再自行格式化
- 测试补充：
  - `backend/backoffice/tests.py` 新增断言，验证左屏 `meta.display`、状态项 `countLabel`、趋势点 `display`
  - 同时验证右屏 `schedule.display.windowDaysLabel` 和风险汇总项 `countLabel`
- 本轮验证已通过：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings`
  - `npm run build`
  - 基于 `hota_mds.test_settings` 的接口冒烟校验 `GET /api/screens/left`
  - 基于 `hota_mds.test_settings` 的接口冒烟校验 `GET /api/screens/right`
- 当前验证结果：
  - 左屏已返回 `meta.display.lastSuccessfulAtLabel='2026-04-21 14:57:20'`
  - 左屏首个状态项已返回 `countLabel='4'`
  - 左屏首个趋势点已返回 `display={'timeLabel': '07:00', 'producedQuantityLabel': '80'}`
  - 右屏已返回 `schedule.display.windowDaysLabel='30 天'`
  - 右屏首个风险项已返回 `countLabel='1'`
  - 说明双屏剩余可见动态字段也已进一步从前端收口到后端
- M3 完成结论：
  - 标准数据模型、缓存层和 mock 数据链路已完成
  - 后端可返回设备、产量、排产、能耗 mock API
  - 前端已可基于 mock/cache API 运行左右屏展示
  - 后端已具备最近一次成功数据兜底
  - 后台已可查看 mock 数据源健康状态
- 本轮修改文件清单：
  - `backend/backoffice/display_services.py`
  - `backend/backoffice/tests.py`
  - `frontend/src/ScreenDisplay.jsx`
  - `docs/STATUS.md`
  - `docs/HANDOFF.md`
- 下一步建议：
  - 正式进入 M4，优先补齐左右屏轮播、全屏适配和独立配置读取能力，但仍继续基于现有 mock/cache API 推进

## 30. 本轮交接摘要

### 本轮目标

- 完成 M3 收尾，把双屏剩余可见动态字段全部收口到后端标准化输出。
- 用验证结果确认 M3 验收条件已经满足，并把项目状态切换为可进入 M4。

### 本轮实际完成

- 后端补齐了 `meta.display.lastSuccessfulAtLabel`、`deviceOverview.statusItems[].countLabel`、`productionTrend[].display.*`、`schedule.display.windowDaysLabel`、`schedule.riskSummary.items[].countLabel`。
- 前端改为优先渲染上述标准化字段，进一步减少前端自行格式化和解释业务字段的职责。
- 补充并通过了后端测试、前端构建以及左右屏接口冒烟验证。
- 已更新 `docs/STATUS.md`、`docs/HANDOFF.md`，并确认当前可从 M3 进入 M4。

### 本轮未完成

- 未进入 M4 的轮播、全屏适配和左右屏独立配置读取实现。
- 未接入任何真实外部系统。
- 未进入报修真实接入、3D 仿真真实开发和内部 Web 报表。

### 修改文件清单

- `backend/backoffice/display_services.py`
- `backend/backoffice/tests.py`
- `frontend/src/ScreenDisplay.jsx`
- `docs/STATUS.md`
- `docs/HANDOFF.md`
- `docs/DECISIONS.md`

### 遇到的问题

- 新增 `meta.display.lastSuccessfulAtLabel` 时，`meta.lastSuccessfulAt` 现有结构是 ISO 字符串而非 datetime，首次测试触发了 `timezone.localtime` 类型错误。
- 已通过在后端标准化 helper 中兼容 ISO 字符串解析修复，不影响最终交付。
- 当前本地工作区仍存在既有改动 `README.md`、`frontend/src/styles.css` 和 `.codex-logs/`，本轮未处理。

### 建议下一轮优先任务

- 正式进入 M4，优先做左右屏轮播、全屏适配和独立配置读取。
- 继续严格使用现有 mock/cache API 推进，不要提前进入真实外部系统接入。
- 继续保持报修、3D 仿真和内部 Web 报表不进入当前优先级。

## 28. 本轮交接记录

- 本轮目标：继续留在 M3，把左屏“设备运行概览”里仍由前端自行格式化的时间与数量展示语义收口到后端标准化输出。
- 范围控制：
  - 没有接入真实外部系统
  - 没有进入报修真实接入
  - 没有做 3D 仿真开发
  - 没有进入内部 Web 报表
- backend 调整：
  - `backend/backoffice/display_services.py` 为左屏设备概览新增 `deviceOverview.display`
  - 当前标准化展示字段包括：
    - `sourceUpdatedAtLabel`
    - `totalCountLabel`
    - `runningCountLabel`
    - `abnormalCountLabel`
  - 原始 `sourceUpdatedAt`、`totalCount`、`runningCount`、`abnormalCount` 字段仍保留，作为兼容字段存在
- frontend 调整：
  - `frontend/src/ScreenDisplay.jsx` 改为优先渲染后端给出的设备概览标准化字段
  - 左屏“数据更新时间”文案改为优先使用 `deviceOverview.display.sourceUpdatedAtLabel`
  - 左屏三项设备指标改为优先渲染 `deviceOverview.display.totalCountLabel`、`runningCountLabel`、`abnormalCountLabel`
- 测试补充：
  - `backend/backoffice/tests.py` 新增断言，验证左屏接口会返回 `deviceOverview.display`
  - 同时验证 `sourceUpdatedAtLabel`、`totalCountLabel`、`runningCountLabel`、`abnormalCountLabel` 的内容符合当前 mock 结构
- 本轮验证已通过：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings`
  - `npm run build`
  - 基于 `hota_mds.test_settings` 的接口冒烟校验 `GET /api/screens/left`
- 当前验证结果：
  - 当前本地测试数据下，左屏设备概览已返回 `sourceUpdatedAtLabel='2026-04-21 14:46:53'`
  - 当前本地测试数据下，左屏设备概览已返回 `totalCountLabel='6'`、`runningCountLabel='4'`、`abnormalCountLabel='2'`
  - 自动化测试中的全新测试库也已验证默认 mock 结构会返回 `deviceOverview.display`
  - 说明左屏设备运行概览展示语义已进一步从前端收口到后端
- 本轮修改文件清单：
  - `backend/backoffice/display_services.py`
  - `backend/backoffice/tests.py`
  - `frontend/src/ScreenDisplay.jsx`
  - `docs/STATUS.md`
  - `docs/HANDOFF.md`
- 下一步建议：
  - 继续留在 M3，优先检查左屏趋势区和右屏图例中是否还有前端自行拼接的展示字段，继续按“后端标准化、前端渲染”的方式逐步收口

## 31. 本轮交接记录

- 本轮目标：完成 M4，一期前段大屏页面开发，只基于 mock 或缓存 API，不接真实外部系统。
- 范围控制：
  - 只做外部参观双屏大屏。
  - 不进入内部 Web 报表。
  - 报修与 3D 仅做占位，不做真实能力。
  - 前端不直连外部系统。
- frontend 实现：
  - `frontend/src/ScreenDisplay.jsx`
  - 新增左右屏页面预设与模块编排，支持 `/screen/left`、`/screen/right` 独立打开。
  - 左屏完成欢迎头部、设备运行概览、产量执行概览、近 8 小时产量趋势、区域能耗概览、报修占位区。
  - 右屏完成未完工订单排产展示、延期风险说明、3D 仿真占位区。
  - 左右屏分别读取自身 `screen` 配置中的标题、`pageKeys`、轮播间隔等参数。
  - 支持按钮和双击触发全屏。
  - 支持自动轮播与甘特区自动纵向滚动。
  - 接口异常时继续渲染最近一次成功数据，避免白屏。
- 样式实现：
  - `frontend/src/styles.css`
  - 按 `frontend/framer.md` 主风格和 `frontend/sentry.md` 数据布局重做大屏视觉。
  - 风格为深色冷色调、高端访客驾驶舱、极简大数字 KPI、柔和动效、玻璃质感面板。
- 文档决策补充：
  - `docs/DECISIONS.md`
  - 明确自动轮播采用“前端页面预设 + 后端配置驱动”的实现方式。
  - 明确全屏为用户触发式，不在加载后自动进入。
- 本轮验证已通过：
  - `npm run build`
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings`
  - 基于 `hota_mds.test_settings` 的左右屏 API 冒烟校验：
    - 左屏 200，返回 `pageKeys=['overview', 'operations']`、`rotationIntervalSeconds=45`
    - 右屏 200，返回 `pageKeys=['schedule', 'risk']`、`rotationIntervalSeconds=50`、`schedule.windowDays=30`

## 32. 本轮交接摘要

### 当前状态

- 当前 M4 已完成，双屏大屏页面可基于 mock/cache API 独立运行。
- 当前仍未接真实外部系统，仍符合“一期前段不直连外部系统”的约束。
- 当前文档顶部状态与本轮交接记录已同步更新。

### 本轮修改文件

- `frontend/src/ScreenDisplay.jsx`
- `frontend/src/styles.css`
- `docs/STATUS.md`
- `docs/HANDOFF.md`
- `docs/DECISIONS.md`

### 下一轮接手重点

- 不要回退当前双屏页面结构与配置驱动方式。
- 若进入 M5，优先推进后端真实数据接入与缓存链路，不要让前端绕过后端直接连外部系统。
- 继续保持报修与 3D 为非阻塞项，除非项目范围再次明确变更。

### 已知缺口

- 还没有在真实拼屏硬件与浏览器 kiosk 场景做现场验收。
- 全屏只能用户触发，无法在首屏自动进入。
- 轮播页仍基于当前预设页集合，后续若增加页面类型需要补预设映射。

## 33. 本轮交接记录

- 本轮目标：继续优化右屏甘特图，并补足 mock 数据规模，用于验证自动纵向滚动是否真实生效。
- 范围控制：
  - 继续留在 M4。
  - 不接真实外部系统。
  - 不进入报修真实接入。
  - 不进入 3D 仿真真实开发。
  - 不进入内部 Web 报表。
- backend 调整：
  - `backend/backoffice/display_services.py`
  - 右屏排产 mock 改为多产线、多订单结构。
  - 当前运行态 mock 返回 16 条产线、32 个订单。
  - 风险状态覆盖正常 / 风险 / 延期 / 暂停。
  - 默认自动滚动阈值为 12，当前 mock 规模已稳定超过阈值，可直接用于验证自动滚动。
- frontend 调整：
  - `frontend/src/ScreenDisplay.jsx`
  - 甘特图区新增产线总数、订单总数、滚动状态信息。
  - 行头新增区域名、可见订单数和延期数量提示。
  - 甘特条补充完整 / 紧凑 / 极窄三档展示密度。
  - 甘特条补充时间范围展示，并在跨窗口裁剪时增加左右方向提示。
  - `frontend/src/styles.css`
  - 日期头改为 sticky，滚动时继续可见。
  - 调整甘特条的行高、文本省略、裁剪提示和信息层级，改善“部分文字显示不完全”的问题。
- test 调整：
  - `backend/backoffice/tests.py`
  - 右屏接口测试改为校验：
    - 产线数大于自动滚动阈值
    - 自动滚动开关为启用
    - 风险汇总总数与订单总数一致
    - 暂停与延期风险至少各有一项
- 本轮验证已通过：
  - `python manage.py test accounts backoffice --settings=hota_mds.test_settings`
  - `npm run build`
  - 运行态 `GET /api/screens/right` 返回：
    - `lineCount=16`
    - `totalOrders=32`
    - `threshold=12`
    - `shouldAutoScroll=true`
  - 运行态 `GET /screen/right` 返回 200

## 34. 本轮交接摘要

### 当前状态

- 右屏甘特图已完成第二轮可读性优化。
- 自动滚动现在不只是逻辑存在，mock 数据规模也已足以稳定触发验证。
- 当前仍满足一期前段范围约束，没有越界进入真实系统接入。

### 本轮修改文件

- `backend/backoffice/display_services.py`
- `backend/backoffice/tests.py`
- `frontend/src/ScreenDisplay.jsx`
- `frontend/src/styles.css`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 下一轮接手重点

- 优先用真实拼屏或大屏浏览距离验收右屏甘特图的行高、字重和滚动节奏。
- 如果继续优化前端，只做展示层微调，不要破坏当前 mock 自动滚动验证条件。
- 如果进入 M5，仍需保持“后端接真实系统、前端只读缓存 API”的边界。

### 已知缺口

- 自动滚动目前已在本地环境具备验证条件，但还没有现场硬件级验收结果。
- mock 数据已为验证放大，后续接真实系统后需要重新校验甘特图密度分布。

## 35. 本轮交接记录

- 本轮目标：继续优化右屏甘特图短周期任务条，让更短的任务块尽量完整显示订单号。
- 范围控制：
  - 继续停留在 M4。
  - 只调展示层样式，不改真实系统边界。
  - 不新增真实业务接入。
- frontend 调整：
  - `frontend/src/styles.css`
  - `compact` 短条进一步减小字号与内边距。
  - `tiny` 极短条进一步减小字号、字距和内边距。
  - 短条订单号由“优先省略显示”调整为“优先完整显示”。
  - 本轮保持前一轮修复后的纵向不截断方案不变。
- 本轮验证已通过：
  - `npm run build`
  - `GET /screen/right` 返回 200

## 36. 本轮交接摘要

### 当前状态

- 右屏甘特图短周期任务条的订单号可读性已继续增强。
- 当前仍在 M4 展示层收口范围内，没有越界进入真实系统接入。

### 本轮修改文件

- `frontend/src/styles.css`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 下一轮接手重点

- 优先在真实屏幕观看距离下确认当前短条字号是否已经足够。
- 若仍有个别极短任务看不清，再考虑对极窄条做更激进的单独字号策略。

## 37. 本轮交接记录

- 本轮目标：隐藏右屏甘特图区右侧难看的纵向滚动条，但保留滚动和自动滚动能力。
- 范围控制：
  - 继续停留在 M4。
  - 只做展示层样式收口。
  - 不改动真实系统接入边界。
- frontend 调整：
  - `frontend/src/styles.css`
  - 为 `.gantt-rows` 增加跨浏览器隐藏滚动条样式：
    - `scrollbar-width: none`
    - `-ms-overflow-style: none`
    - `::-webkit-scrollbar { display: none; width: 0; height: 0; }`
  - 当前仍保留纵向滚动和自动滚动逻辑，只隐藏滚动条可视 UI。
- 本轮验证已通过：
  - `npm run build`
  - `GET /screen/right` 返回 200

## 38. 本轮交接摘要

### 当前状态

- 右屏甘特图区显式纵向滚动条已隐藏。
- 当前仍处于 M4 展示层收口范围内，没有越界到真实系统接入。

### 本轮修改文件

- `frontend/src/styles.css`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 下一轮接手重点

- 继续在真实观看距离下验收右屏甘特图的整体观感。
- 若还需要更强的沉浸感，可继续收口时间轴、行头和卡片阴影，但不要破坏当前滚动能力。

## 39. 本轮交接记录

### 本轮目标

- 继续收口右屏甘特图的展示问题，重点处理：
  - 部分任务块底部被截断
  - 任务条上风险文字过多
  - 短周期任务订单号显示不完整
  - 右侧显式滚动条观感差

### 本轮实际完成

- `frontend/src/ScreenDisplay.jsx`
  - 调整任务条纵向槽位与底部安全区，修复部分任务块底部被截断问题。
  - 去除任务条上的风险/延期文字，仅保留颜色作为状态区分。
  - 保留订单号、物料、完成率、时间范围等核心信息。
- `frontend/src/styles.css`
  - 针对 `compact` 和 `tiny` 短条继续缩小字号、字距与内边距。
  - 隐藏 `.gantt-rows` 的显式纵向滚动条，同时保留自动滚动和手动滚动。
- `docs/STATUS.md`
  - 按本轮口径补齐“当前阶段 / 本轮已完成 / 未完成 / 当前已知问题 / 下一个最优先任务”。
- `docs/HANDOFF.md`
  - 按本轮口径补齐“本轮目标 / 本轮实际完成 / 本轮未完成 / 修改文件清单 / 遇到的问题 / 建议下一轮优先任务”。
- `docs/DECISIONS.md`
  - 补充本轮右屏甘特图相关决策、理由与影响。
- 本轮验证已通过：
  - `npm run build`
  - `GET /screen/right` 返回 200

### 本轮未完成

- 尚未在真实拼屏硬件与远距离观看场景下确认当前短条字号是否已达到最终最佳状态。
- 尚未接入真实排产系统数据。
- 尚未完成现场演示环境下右屏甘特图的最终视觉微调。

### 修改文件清单

- `frontend/src/ScreenDisplay.jsx`
- `frontend/src/styles.css`
- `docs/STATUS.md`
- `docs/HANDOFF.md`
- `docs/DECISIONS.md`

### 遇到的问题

- 右屏甘特图使用绝对定位叠加任务条时，任务条真实高度与估算槽位高度之间存在偏差，导致部分条块底部被截断。
- 短周期任务在有限宽度内既要显示订单号，又要避免条内信息过载，需要持续平衡字号、字距和内边距。
- 显式浏览器滚动条在大屏观感中较突兀，需要在不影响滚动能力的前提下做纯展示层隐藏。

### 建议下一轮优先任务

- 优先在真实拼屏或 kiosk 场景做右屏甘特图现场验收，确认短条订单号可读性、任务条密度和自动滚动节奏是否还需要最后一轮微调。

## 40. 本轮交接记录

### 本轮目标

- 先更新根目录 `README.md`，把仓库入口文档与当前项目事实源对齐。
- 本轮只做文档，不进入真实数据接入、不改代码实现。

### 本轮实际完成

- 已更新 `README.md`，使其与以下核心文档保持一致：
  - `docs/PRD/PRD_和泰智屏系统.md`
  - `docs/SPEC.md`
  - `docs/PLAN.md`
  - `docs/STATUS.md`
  - `docs/HANDOFF.md`
  - `docs/AGENTS.md`
  - `docs/DECISIONS.md`
- 已将 README 中过时的项目状态从 M2/M1 阶段描述修正为当前 `M4 已完成、M5 未开始`。
- 已修正 README 中错误或过时的信息：
  - PRD 实际路径
  - 左右屏页面不再是占位页，而是当前可运行展示页
  - 当前后台资源清单已补齐 `materials`、`orders`、`page-module-switches`、`data-source-healths`
  - 本地开发增加 `load_mock_screen_data` 命令说明
- 已同步更新 `docs/STATUS.md` 与 `docs/HANDOFF.md`，记录本轮仅做 README 同步这一事实。

### 本轮未完成

- 未修改任何后端、前端、collector 或数据库实现。
- 未进入 `M5` 真实外部系统接入。
- 未继续推进右屏甘特图现场验收。

### 修改文件清单

- `README.md`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- `README.md` 在本轮开始前已经处于脏工作区，但差异很小；本轮在保留现有改动基础上增量同步到当前文档口径，没有做回退。
- README 原内容明显落后于当前状态，仍停留在 M2 口径，并包含错误的 PRD 路径与“占位页”描述，已在本轮修正。

### 建议下一轮优先任务

- 按既定计划回到 M5 前置准备或真实数据源接入准备，但仍保持“前端不直连外部系统、后端负责标准化与缓存”的边界。

## 41. 本轮交接记录

### 本轮目标

- 启动当前项目，供本地直接查看前端效果。
- 本轮只做运行与验证，不进入新功能开发。

### 本轮实际完成

- 已确认本机 Docker 可执行文件存在，但 Docker Engine 未启动，因此没有采用 `docker compose up`。
- 已改用本地开发启动方案：
  - 后端：`python manage.py runserver 0.0.0.0:8000 --settings=hota_mds.test_settings`
  - 前端：`npm run dev -- --host 0.0.0.0 --port 3000`
- 启动前已处理本地测试库问题：
  - `backend/test.sqlite3` 不是仓库受管文件，而是本地产物。
  - 因旧库迁移状态与当前代码不一致，已删除后重建。
  - 已重新执行迁移并串行执行 `python manage.py load_mock_screen_data --settings=hota_mds.test_settings`。
- 已完成运行态验证：
  - `http://127.0.0.1:8000/api/health` 返回 200
  - `http://127.0.0.1:8000/api/screens/left` 返回 200
  - `http://127.0.0.1:3000/screen/left` 返回 200
  - `http://127.0.0.1:3000/screen/right` 返回 200
- 当前本地可直接访问：
  - 左屏：`http://127.0.0.1:3000/screen/left`
  - 右屏：`http://127.0.0.1:3000/screen/right`

### 本轮未完成

- 未启动 Docker Compose 运行方式。
- 未接入真实外部系统。
- 未进行任何业务代码变更。

### 修改文件清单

- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- `docker compose ps` 报错，根因是 Docker Desktop Linux Engine 未启动，而不是 Compose 文件本身有误。
- 首次尝试把 `migrate` 与 `load_mock_screen_data` 并行执行，导致 mock 装载早于迁移完成，触发“表不存在”错误；已改为串行执行并解决。
- 原有 `backend/test.sqlite3` 与当前迁移历史不一致，已删除后重建。

### 建议下一轮优先任务

- 如果只是继续查看页面效果，直接复用当前本地运行的前后端即可。
- 如果进入开发轮次，仍应保持当前边界，优先推进 M5 前置准备或真实数据接入准备，不让前端直连外部系统。

## 42. 本轮交接记录

### 本轮目标

- 优化左屏 `http://127.0.0.1:3000/screen/left` 中“产量执行概览”模块。
- 解决“只有百分比、没有进度条”的展示问题。
- 扩充 mock 数据，验证该模块在多产线场景下是否会滚动切换显示。

### 本轮实际完成

- `frontend/src/ScreenDisplay.jsx`
  - 为左屏产量概览的每条产线摘要新增进度条。
  - 当产线摘要数量大于 6 条时，自动启用纵向滚动。
  - 模块头部新增产线数量和滚动状态文案。
- `frontend/src/styles.css`
  - 新增进度条和滚动容器样式。
  - 隐藏该模块的显式滚动条，同时保留滚动能力。
  - 调整摘要卡片布局，兼容进度条、订单信息与数量信息同屏显示。
- `backend/backoffice/display_services.py`
  - 将左屏 mock 产线摘要扩充到最少 8 条，便于直接验证滚动。
  - 保留首条产线的既有 mock 文案与数值口径，避免无必要破坏既有展示语义。
- `backend/backoffice/tests.py`
  - 更新左屏 mock 总量断言。
  - 新增左屏产线摘要数量为 8 的断言。

### 本轮未完成

- 未接入真实产量系统。
- 未在真实拼屏硬件上做左屏模块终验。
- 未扩展到报修、3D 仿真或内部 Web 报表。

### 修改文件清单

- `frontend/src/ScreenDisplay.jsx`
- `frontend/src/styles.css`
- `backend/backoffice/display_services.py`
- `backend/backoffice/tests.py`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 本地后端进程在自动 reload 场景下不稳定，改为 `--noreload` 后稳定提供服务。
- 本轮中途发现当前运行中的后端还是旧代码进程，导致 API 一度返回旧的 3 条产线摘要；重启 Django 服务后恢复正常。
- 左屏 mock 数据扩容后，原有测试中的总目标数、总已产数和完成率断言需要同步更新。

### 建议下一轮优先任务

- 如果继续做 M4 展示层收口，优先在真实大屏观看距离下确认左屏进度条的远距离可读性和自动滚动节奏。
- 如果进入下一阶段，仍保持“前端只读标准 API、真实接入由后端/collector 负责”的边界，推进 M5 前置准备。

## 43. 本轮交接记录

### 本轮目标

- 继续优化左屏“产量执行概览”模块。
- 让进度条更粗、更易读。
- 把完成率百分比移到进度条右侧。
- 增加起始时间-结束时间与预计完成时间。
- 当预计无法按期完成时，把进度条变为红色。

### 本轮实际完成

- `backend/backoffice/display_services.py`
  - 为左屏产线摘要新增原始字段：
    - `plannedStartAt`
    - `plannedEndAt`
    - `estimatedCompletionAt`
    - `isDelayed`
  - 为左屏产线摘要 `display` 新增：
    - `plannedRangeLabel`
    - `estimatedCompletionLabel`
    - `progressAccent`
  - 当前 mock 中已稳定生成延期样本，延期样本会返回 `progressAccent='red'`。
- `frontend/src/ScreenDisplay.jsx`
  - 左屏进度条变粗。
  - 完成率百分比移到进度条右侧。
  - 每条产线新增计划起止时间显示。
  - 每条产线新增预计完成时间显示。
  - 延期样本自动渲染为红色进度条。
- `frontend/src/styles.css`
  - 新增蓝色/红色两种进度条视觉状态。
  - 调整左屏产量摘要布局，兼容更粗进度条、右侧百分比和两行时间文案。
- `backend/backoffice/tests.py`
  - 同步补充时间标签、`progressAccent` 与红色延期样本断言。

### 本轮未完成

- 未接入真实产量/订单系统。
- 未在真实拼屏硬件上做左屏时间信息的终验。
- 未扩展到报修、3D 仿真或内部 Web 报表。

### 修改文件清单

- `backend/backoffice/display_services.py`
- `backend/backoffice/tests.py`
- `frontend/src/ScreenDisplay.jsx`
- `frontend/src/styles.css`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 为了让“延期红条”真实可见，原先 mock 中的延迟量不够，需要进一步放大预计完成偏移，才能稳定出现延期样本。
- 本地 Django 开发服务在某些后台隐藏启动方式下不稳定，最终采用更保守的常驻方式启动，确保本地页面验证可持续。

### 建议下一轮优先任务

- 如果继续做 M4 收口，优先在真实大屏观看距离下确认：
  - 进度条厚度是否足够
  - 时间信息是否过密
  - 红色延期条是否足够醒目
- 如果进入下一阶段，继续保持现有边界，推进 M5 前置准备或真实数据接入准备。

## 44. 本轮交接记录

### 本轮目标

- 拉长左屏任务进度条。
- 保持百分比数字在进度条右方。

### 本轮实际完成

- `frontend/src/styles.css`
  - 为左屏任务卡片主信息区补充 `flex: 1 1 auto`，使其吃满剩余横向空间。
  - 将右侧数量信息列收敛为固定窄列，减少对进度条的横向挤压。
  - 将进度条行宽度调整为约 `88%`，落在要求的 `85%-90%` 区间内。
  - 保持进度条右侧百分比布局不变。

### 本轮未完成

- 未在真实拼屏硬件上确认 88% 是否为最终最佳值。
- 未推进真实数据接入。

### 修改文件清单

- `frontend/src/styles.css`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 当前问题的根因不是数据不足，而是任务卡片主信息区没有明确占满剩余宽度，导致进度条行天然偏短。

### 建议下一轮优先任务

- 如果继续收口左屏，优先在真实大屏观看距离下确认当前 88% 的进度条长度是否已经足够，必要时再微调到更接近 90%。

## 45. 本轮交接记录

### 本轮目标

- 在不改数据结构的前提下，把左屏进度条继续拉长一截。

### 本轮实际完成

- `frontend/src/styles.css`
  - 将右侧数量信息列进一步压窄。
  - 将进度条行宽度推到主信息区满宽。
  - 缩小百分比占位宽度和进度条/百分比之间的间距。
  - 略微缩小时间信息字号，给进度条释放更多横向空间。
- 本轮保持：
  - 百分比仍在进度条右方
  - 时间信息、预计完成时间和红色延期条逻辑不变

### 本轮未完成

- 未在真实拼屏硬件上确认这次拉长后的最终观感。
- 未推进真实数据接入。

### 修改文件清单

- `frontend/src/styles.css`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 当前已经基本把纯样式层能释放的横向空间都释放出来了；如果用户仍觉得不够长，下一轮应改为更大幅度调整卡片信息布局，而不是继续只压缩间距。

### 建议下一轮优先任务

- 如果你看完仍觉得太短，下一轮直接改卡片整体布局，把右侧数量信息进一步下沉或重排，给进度条让出更多真正可用的横向空间。

## 46. 本轮交接记录

### 本轮目标

- 解决左屏任务卡片内部纵向隔断限制进度条长度的问题。

### 本轮实际完成

- `frontend/src/ScreenDisplay.jsx`
  - 左屏任务卡片改为三行结构：
    - 第一行：任务主信息 + 右侧目标/已产
    - 第二行：跨整卡的进度条 + 百分比
    - 第三行：跨整卡的时间信息
- `frontend/src/styles.css`
  - 左屏任务卡片从原来的横向块布局调整为 CSS Grid。
  - 进度条行设置为跨列整行，已越过原先右侧纵向分栏。
  - 时间信息行也改为跨列整行。
  - 百分比仍在进度条右方，但现在位于任务块最右侧。

### 本轮未完成

- 未在真实拼屏硬件上终验当前跨列布局。
- 未推进真实数据接入。

### 修改文件清单

- `frontend/src/ScreenDisplay.jsx`
- `frontend/src/styles.css`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 当前问题的根因不是进度条宽度数值不够，而是进度条始终被放在左主信息列内部；只有把进度条改成跨列整行，才能真正突破那条纵向隔断。

### 建议下一轮优先任务

- 如果继续收口左屏，优先在你实际刷新后的观感基础上判断：
  - 是否还需要继续缩小左右内边距
  - 百分比占位是否还要再压窄
  - 时间信息是否需要再减字号

## 47. 本轮交接记录

### 本轮目标

- 修复自动滚动到最后一条后不回到第一条的问题。

### 本轮实际完成

- `frontend/src/ScreenDisplay.jsx`
  - 修正通用自动纵向滚动 hook。
  - 原逻辑要求 `scrollTop >= maxScrollTop` 才会回卷，容易因为滚动值停在“接近底部但未精确命中”的状态而卡住。
  - 新逻辑改为先计算 `nextScrollTop`，当 `nextScrollTop >= maxScrollTop - 1` 时直接回到顶部。
  - 该修复同时作用于：
    - 左屏产量摘要自动滚动
    - 右屏甘特图区自动滚动

### 本轮未完成

- 未在真实拼屏硬件上做长时间循环滚动终验。
- 未推进真实数据接入。

### 修改文件清单

- `frontend/src/ScreenDisplay.jsx`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 问题根因不是“滚动没开”，而是回卷条件过于严格，导致滚动值靠近底部时可能永远不会触发顶部重置。

### 建议下一轮优先任务

- 如果继续收口 M4，优先在真实展示环境下连续观察一段时间，确认左屏和右屏都能稳定从底部回卷到顶部。

## 48. 本轮交接记录

### 本轮目标

- 在不进入真实数据接入的前提下，调整左屏 `http://127.0.0.1:3000/screen/left` 的模块组织方式。
- 去掉设备概览中的运行、停机、报警、离线四块状态明细。
- 将报修模块整合进设备概览模块。
- 将区域能耗概览整合进 8 小时产量趋势模块。

### 本轮实际完成

- `frontend/src/ScreenDisplay.jsx`
  - 左屏“设备运行概览”卡片保留设备总数、运行设备、异常设备 3 个核心指标。
  - 左屏“设备运行概览”卡片移除原先的运行/停机/报警/离线状态明细列表。
  - 左屏“报修占位区”改为内嵌到“设备运行概览”卡片下半区，不再独立渲染。
  - 左屏“区域能耗概览”改为内嵌到“近 8 小时产量趋势”卡片下半区，不再独立渲染。
  - 新增左屏 section 嵌入映射，保证旧 `pageKeys`/`moduleSettings` 配置下仍能正确落到宿主卡片，不会重复显示。
- `frontend/src/styles.css`
  - 新增内嵌子模块样式：分隔线、子标题、内嵌报修块、内嵌能耗列表。
  - 调整内嵌报修区最小高度，避免沿用独立占位卡片的大块留白。
  - 调整内嵌能耗项布局，使其适配趋势卡片下半区。
- `docs/STATUS.md`
  - 已同步记录本轮展示层调整、验证结果、未完成项和下一步建议。
- `docs/HANDOFF.md`
  - 已同步记录本轮目标、实际完成、修改文件和验证结果。

### 本轮未完成

- 未接入真实外部系统。
- 未改动后端展示数据结构。
- 未在真实拼屏硬件上完成本轮左屏重组后的现场终验。

### 修改文件清单

- `frontend/src/ScreenDisplay.jsx`
- `frontend/src/styles.css`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 左屏原有页面配置中 `repairPlaceholder` 与 `energyOverview` 仍作为独立 section key 存在，如果直接删除会导致旧配置下可能出现空白页或重复渲染。
- 本轮通过“嵌入 section 映射到宿主卡片”的方式处理，既完成视觉整合，又保持旧配置兼容，没有额外扩大改动范围。

### 建议下一轮优先任务

- 如果继续收口 `M4`，优先在真实左屏观看距离下确认：
  - 设备概览并入报修后卡片高度是否合适
  - 趋势卡片并入能耗后上下区块密度是否合适
  - 是否还需要继续做纯展示层微调
- 如果不继续做展示层微调，则继续等待外部系统资料，按既定计划推进 `M5` 前置准备。

## 49. 本轮交接记录

### 本轮目标

- 修复左屏 `http://127.0.0.1:3000/screen/left` 中“产量执行概览”模块底部数据显示不全的问题。
- 保持本轮只做展示层 bug 修复，不进入真实数据接入。

### 本轮实际完成

- `frontend/src/ScreenDisplay.jsx`
  - 为左屏“产量执行概览”卡片增加 `production-overview-panel` 布局类。
  - 为产线摘要列表增加 `production-overview-list` 容器类，使列表明确成为卡片内的剩余高度区。
- `frontend/src/styles.css`
  - 将“产量执行概览”卡片改为 `flex` 纵向布局。
  - 产线摘要列表改为 `flex: 1 1 auto` + `min-height: 0` 的自适应滚动区域。
  - 移除原先固定的 `max-height: 372px` 限制，避免卡片高度变化后继续把底部内容顶出卡片。
  - 保留滚动条隐藏和既有自动滚动能力。
- `docs/STATUS.md`
  - 已同步记录本轮 bug 修复、验证结果和后续建议。
- `docs/HANDOFF.md`
  - 已同步记录本轮目标、修复内容、修改文件和验证结果。

### 本轮未完成

- 未在真实拼屏硬件上完成本轮修复后的现场终验。
- 未接入真实外部系统。
- 未推进 `M5` 真实数据接入。

### 修改文件清单

- `frontend/src/ScreenDisplay.jsx`
- `frontend/src/styles.css`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 根因不是接口数据缺失，而是“产量执行概览”卡片与同一行其他卡片共享栅格高度时，内部列表仍按固定高度向下撑开，最终被卡片的 `overflow: hidden` 裁切。
- 本轮通过把卡片改为“固定头部 + 自适应滚动列表”的结构处理，避免继续依赖固定像素高度。

### 建议下一轮优先任务

- 如果继续收口 `M4`，优先在真实左屏观看距离下确认：
  - 底部条目是否已经完整显示
  - 列表滚动节奏是否仍然合适
  - 是否还需要继续压缩卡片留白来提升单屏可见条目数
- 如果不继续做展示层微调，则继续等待外部系统资料，按既定计划推进 `M5` 前置准备。

## 50. 本轮交接记录

### 本轮目标

- 修复上一轮引入的新问题：左屏“产量执行概览”卡片内容过多时，把整行三张卡片一起撑高，导致全屏后无法完整看到三个模块整体。
- 保持本轮只做展示层布局修复，不进入真实数据接入。

### 本轮实际完成

- `frontend/src/styles.css`
  - `screen-shell` 改为纵向 `flex` 布局，使头部之外的页面区域严格使用剩余可视高度。
  - `screen-page` 改为 `flex: 1 1 auto` 且 `min-height: 0`，允许内容区在全屏时被限制在可见范围内。
  - 左屏 `screen-grid-left` 增加 `height: 100%`、`align-items: stretch`、`grid-auto-rows: minmax(0, 1fr)`，确保左屏当前这一行三张卡片共享同一受限高度。
  - 左屏卡片统一增加 `height: 100%` 和 `min-height: 0`，避免“产量执行概览”单卡内容继续把整行高度一起撑大。
- 保留上一轮修复结果：
  - “产量执行概览”内部列表仍在卡片内部滚动。
  - 不再改成一次性显示全部条目。
- `docs/STATUS.md`
  - 已同步记录本轮布局约束修复、验证结果和后续建议。
- `docs/HANDOFF.md`
  - 已同步记录本轮目标、修复内容、修改文件和验证结果。

### 本轮未完成

- 未在真实拼屏硬件上完成本轮高度约束修复后的现场终验。
- 未接入真实外部系统。
- 未推进 `M5` 真实数据接入。

### 修改文件清单

- `frontend/src/styles.css`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 上一轮虽然把“产量执行概览”内部列表改成了可滚动，但没有同时约束左屏整页和这一行 grid 的总高度，导致 production 卡片所在整行仍会被内容一起撑高。
- 本轮通过“左屏整页剩余高度受限 + 左屏当前行三卡同高 + 只有卡片内部列表滚动”的方式修复，避免再次回到“内容全展开”的错误方向。

### 建议下一轮优先任务

- 如果继续收口 `M4`，优先在真实左屏全屏场景下确认：
  - 三张卡片整体是否都完整可见
  - 产量卡片内部滚动是否自然
  - 是否还需要继续微调卡片内部留白和单条摘要高度
- 如果不继续做展示层微调，则继续等待外部系统资料，按既定计划推进 `M5` 前置准备。

## 51. 本轮交接记录

### 本轮目标

- 检查左屏“区域能耗概览”是否具备和“产量执行概览”同类的内部滚动能力。
- 增加更多 mock 能耗区域，使左屏能直接观察到能耗区滚动效果。
- 保持本轮只做展示层与 mock 数据增强，不进入真实数据接入。

### 本轮实际完成

- `frontend/src/ScreenDisplay.jsx`
  - 左屏“区域能耗概览”新增独立滚动容器引用 `energySummaryScrollRef`。
  - 左屏“区域能耗概览”新增自动滚动判断 `shouldAutoScrollEnergySummaries`，当前阈值为区域数大于 4。
  - 左屏“近 8 小时产量趋势”卡片增加 `production-trend-panel` 布局类，兼容上半区柱状图和下半区能耗滚动区。
  - 左屏“区域能耗概览”标题区新增“区域 N 个 / 自动滚动中”状态文案。
  - 左屏“区域能耗概览”新增总能耗摘要行。
- `frontend/src/styles.css`
  - 新增 `production-trend-panel`，使趋势卡片本身采用纵向布局。
  - 新增 `embedded-panel-block-fill`，让内嵌能耗区占用趋势卡片剩余高度。
  - 新增 `embedded-panel-summary`，展示总能耗摘要。
  - `energy-list-embedded` 改为内部滚动容器，并保留滚动条隐藏能力。
  - 新增 `energy-list-scrollable`，用于能耗区自动滚动场景。
- `backend/backoffice/display_services.py`
  - mock 能耗区域扩充到最少 8 条。
  - 前 3 条区域数据口径保持不变，后续新增 `MOCK-Axx` 区域用于验证滚动。
  - 当前 mock 总能耗更新为 `6180.00 kWh`。
- `backend/backoffice/tests.py`
  - 总能耗断言更新为 `6180.00 kWh`。
  - 新增左屏能耗区域数量为 8 的断言。

### 本轮未完成

- 未在真实拼屏硬件上完成能耗区滚动终验。
- 未接入真实能耗数据库。
- 未推进 `M5` 真实数据接入。

### 修改文件清单

- `frontend/src/ScreenDisplay.jsx`
- `frontend/src/styles.css`
- `backend/backoffice/display_services.py`
- `backend/backoffice/tests.py`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 左屏能耗区此前只是并入趋势卡片，但没有独立滚动容器，因此即使数据增多，也不会像产量概览那样在卡片内部自动滚动。
- 本轮通过“趋势卡片自身纵向布局 + 能耗区占剩余高度 + 能耗列表内部滚动”的方式补齐这一能力。
- 扩充 mock 区域时需要保持前三条既有数据口径不变，否则会破坏原有展示基准和测试断言。

### 建议下一轮优先任务

- 如果继续收口 `M4`，优先在真实左屏全屏场景下确认：
  - 能耗区自动滚动节奏是否合适
  - 总能耗摘要位置是否清晰
  - 单条区域卡片高度和字体是否还需微调
- 如果不继续做展示层微调，则继续等待外部系统资料，按既定计划推进 `M5` 前置准备。

## 52. 本轮交接记录

### 本轮目标

- 调整左屏“区域能耗概览”的标题行排布。
- 让“总能耗”与“区域能耗概览”位于同一行显示。

### 本轮实际完成

- `frontend/src/ScreenDisplay.jsx`
  - 左屏能耗区将“总能耗”上移到标题行右侧。
  - 原先标题行中的“区域 N 个 / 自动滚动中”状态下移到下一行摘要。
- `docs/STATUS.md`
  - 已同步记录本轮微调与验证结果。
- `docs/HANDOFF.md`
  - 已同步记录本轮目标、实际完成和验证结果。

### 本轮未完成

- 未在真实拼屏硬件上完成本轮标题行排布的现场终验。
- 未接入真实外部系统。

### 修改文件清单

- `frontend/src/ScreenDisplay.jsx`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 无阻塞性问题。本轮只是展示层文案位置调整，不涉及数据结构和滚动逻辑变更。

### 建议下一轮优先任务

- 如果继续收口 `M4`，优先根据现场观感确认能耗区标题行、摘要和滚动列表的视觉层级是否还需要微调；否则继续等待外部系统资料，按既定计划推进 `M5` 前置准备。

## 53. 本轮交接记录

### 本轮目标

- 将右屏从当前“三模块”改为“两模块”布局。
- 保持左侧“未完工订单排产展示”横向宽度不变。
- 将“延期风险说明”取消为独立模块，只保留四个状态订单数量汇总并入排产模块。
- 将剩余右侧空间作为“3D 仿真占位区”。

### 本轮实际完成

- `frontend/src/ScreenDisplay.jsx`
  - 右屏 section 解析新增嵌入映射 `delayLegend -> schedule`，保持旧配置兼容。
  - 右屏“未完工订单排产展示”模块顶部新增 4 状态订单数量汇总，状态为正常、风险、延期、暂停。
  - 右屏“延期风险说明”独立模块已移除，不再单独渲染。
  - 右屏“3D 仿真占位区”从整行模块改为右侧独立模块。
- `frontend/src/styles.css`
  - 新增右屏汇总条样式 `risk-summary-row` / `risk-summary-tile`，保证 4 个状态同一行显示。
  - 新增右屏布局样式 `schedule-panel` / `simulation-panel`。
  - 新增右屏汇总条的响应式规则，避免窄屏时四项挤坏布局。
- `docs/STATUS.md`
  - 已同步记录本轮右屏展示层重组与验证结果。
- `docs/HANDOFF.md`
  - 已同步记录本轮目标、完成情况和后续建议。

### 本轮未完成

- 未在真实拼屏硬件上完成本轮右屏新布局的现场终验。
- 未接入真实排产系统。
- 未推进 `M5` 真实数据接入。

### 修改文件清单

- `frontend/src/ScreenDisplay.jsx`
- `frontend/src/styles.css`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 右屏当前数据结构仍保留 `delayLegend` 和 `schedule.riskSummary.items`，如果直接删掉旧 key，容易破坏既有配置兼容性。
- 本轮通过“保留数据结构与旧配置 key，但在前端渲染层把 `delayLegend` 折叠进 `schedule`”的方式处理，避免无必要重构。

### 建议下一轮优先任务

- 如果继续收口 `M4`，优先在真实右屏全屏场景下确认：
  - 4 状态汇总条是否太高或太宽
  - 右侧 3D 占位区比例是否合适
  - 甘特图区剩余空间是否足够
- 否则继续等待外部系统资料到位，按既定计划推进 `M5` 前置准备。

## 54. 本轮交接记录

### 本轮目标

- 修复右屏“未完工订单排产展示”模块底部空白问题。
- 保持本轮只做展示层 bug 修复，不进入真实数据接入。

### 本轮实际完成

- `frontend/src/styles.css`
  - 右屏 `schedule-panel` 新增 `align-self: start`。
  - 这样左侧排产模块不再被右侧 3D 占位区所在同一行高度强制拉伸，底部空白改为按排产内容高度自然收口。
- `docs/STATUS.md`
  - 已同步记录本轮 bug 修复与验证结果。
- `docs/HANDOFF.md`
  - 已同步记录本轮目标、修复内容和后续建议。

### 本轮未完成

- 未在真实拼屏硬件上完成本轮空白修复的现场终验。
- 未接入真实排产系统。

### 修改文件清单

- `frontend/src/styles.css`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 根因不是甘特图数据缺失，而是右屏改为两列布局后，左侧排产模块作为 grid item 默认被拉伸到整行高度，导致内容不足部分在底部留下明显空白。
- 本轮通过让左侧排产模块按内容高度收口处理，没有扩大改动到数据结构或甘特图绘制逻辑。

### 建议下一轮优先任务

- 如果继续收口 `M4`，优先根据现场观感确认：
  - 左侧排产模块收口后是否还需要补充底部分隔或留白
  - 右侧 3D 占位区比例是否合适
  - 顶部四状态汇总条是否还需继续压缩高度
- 否则继续等待外部系统资料到位，按既定计划推进 `M5` 前置准备。

## 55. 本轮交接记录

### 本轮目标

- 修正上一轮错误修法：不能通过缩短右屏左侧排产模块本身来消除底部空白。
- 改为保持左侧排产模块全高，并让甘特图区本身填满剩余高度。

### 本轮实际完成

- `frontend/src/styles.css`
  - 回退 `schedule-panel align-self: start` 的错误方向。
  - `screen-grid-right` 增加 `height: 100%`，让右屏两列共同吃满内容区高度。
  - `schedule-panel` 和 `simulation-panel` 增加 `height: 100%`，保持左右两模块都到底。
  - `gantt-shell` 改为纵向 `flex` 容器，并占用排产模块剩余空间。
  - `gantt-board` 改为纵向 `flex` 容器，并继续占用剩余空间。
  - `gantt-rows` 改为 `flex: 1` + `min-height: 0`，并移除固定 `max-height: 460px` 限制。
- 修复结果：
  - 左侧排产模块仍然显示到模块最下方。
  - 顶部标题和 4 状态汇总固定。
  - 甘特图区吃满剩余高度并在内部滚动。
- `docs/STATUS.md`
  - 已同步记录本轮更正修法与验证结果。
- `docs/HANDOFF.md`
  - 已同步记录本轮目标、修复内容和后续建议。

### 本轮未完成

- 未在真实拼屏硬件上完成本轮正确修法后的现场终验。
- 未接入真实排产系统。

### 修改文件清单

- `frontend/src/styles.css`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 上一轮问题判断只覆盖了“模块底部空白”，但忽略了用户真正要求的是“左侧模块本身仍应显示到底”，因此缩短 `schedule-panel` 是错误修法。
- 本轮改为保持左侧模块全高，并把自适应逻辑下沉到甘特区内部容器，这是更符合需求边界的处理方式。

### 建议下一轮优先任务

- 如果继续收口 `M4`，优先根据现场观感确认：
  - 甘特图区填满剩余高度后的阅读密度是否合适
  - 顶部 4 状态汇总与甘特图区的垂直间距是否要继续收口
  - 右侧 3D 占位区比例是否还需微调
- 否则继续等待外部系统资料到位，按既定计划推进 `M5` 前置准备。

## 56. 本轮交接记录

### 本轮目标

- 读取 `README.md` 并按当前事实源对齐核心交接文档。
- 修正文档中的过时路径与过时状态描述，避免后续接手误读。

### 本轮实际完成

- `docs/HANDOFF.md`
  - 修正“下次开发前必须先阅读的文件”中 PRD 路径为 `docs/PRD/PRD_和泰智屏系统.md`。
  - 将必读清单补齐为与 README 一致的核心文档集合，新增：
    - `docs/AGENTS.md`
    - `docs/DECISIONS.md`
  - 保留 `docs/API_CONTRACT.md`、`docs/DB_MODEL_DRAFT.md`、`docs/IMPLEMENTATION_PLAN.md` 作为补充阅读顺序。
  - 修正过时状态描述：将“尚未把数据源健康状态接到后台前端控制台”更新为“后台前端控制台已可查看数据源健康状态”。
- `docs/STATUS.md`
  - 新增本轮“文档对齐”更新与收尾状态记录，明确本轮仅做文档同步，不改动业务实现。

### 本轮未完成

- 未进入 `M5` 真实数据源接入。
- 未修改后端、前端、collector 业务代码。
- 未推进现场拼屏终验。

### 修改文件清单

- `docs/HANDOFF.md`
- `docs/STATUS.md`

### 遇到的问题

- 文档历史记录较长，部分早期段落保留了阶段性语义；本轮只修正 README 明确要求相关的硬性不一致项，不回溯改写历史交接内容。

### 建议下一轮优先任务

- 继续按当前里程碑边界推进：`M4` 展示层收口或 `M5` 前置准备；保持“前端不直连外部系统、后端负责标准化与缓存”。

## 57. 本轮交接记录

### 本轮目标

- 调整 OPC UA 数据源配置项：
  - 删除原“节点ID”单行输入框。
  - 改为“节点ID列表”长文本输入。
  - 后端新增 `NODE`（`node`）JSON 字段存储节点列表。

### 本轮实际完成

- `backend/backoffice/models.py`
  - `DataSourceConfig` 新增 `node = JSONField(default=dict, blank=True)`。
- `backend/backoffice/serializers.py`
  - `DataSourceConfigSerializer` 新增 `node` 字段。
  - OPC UA `connection_config` 允许键移除 `nodeId`，仅保留 `endpointUrl/username/password`。
  - 新增 OPC UA 校验：`node` 需为字符串数组（允许空数组）。
- `backend/backoffice/migrations/0014_datasourceconfig_node.py`
  - 新增数据库迁移，新增 `node` 字段。
  - 兼容迁移历史数据：将 `connection_config.nodeId` 迁移到 `node` 列表。
- `backend/backoffice/opcua_history_services.py`
  - 历史样本节点读取优先级改为 `node[0]` -> `connection_config.nodeId` -> 默认节点，兼容旧数据。
- `backend/backoffice/tests.py`
  - 更新 OPC UA 数据源配置清洗测试，确保 `connection_config` 不再保留 `nodeId`。
  - 增加 `node` 列表保存断言。
- `frontend/src/adminResources.js`
  - OPC UA 表单字段由 `nodeId` 改为 `node`。
  - 标签改为“节点ID列表”。
  - 输入组件改为 JSON 长文本（textarea）并提供数组示例占位。

### 本轮未完成

- 未接入真实 OPC UA 服务端进行联调。
- 未推进 M5 真实数据源接入。
- 未扩展到报修、3D 仿真或内部 Web 报表。

### 修改文件清单

- `backend/backoffice/models.py`
- `backend/backoffice/serializers.py`
- `backend/backoffice/opcua_history_services.py`
- `backend/backoffice/tests.py`
- `backend/backoffice/migrations/0014_datasourceconfig_node.py`
- `frontend/src/adminResources.js`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 旧版本 OPC UA 配置将节点放在 `connection_config.nodeId`，本轮新增 `node` 后需要保证历史数据不丢失；已通过迁移脚本兼容处理。
- 后台改为 JSON 长文本后，节点列表录入必须是合法 JSON 数组；非法格式会在前端提交阶段被拦截。

### 建议下一轮优先任务

- 若继续收口后台可用性，优先补充“节点ID列表”示例模板与错误提示文案。
- 若进入下一阶段，继续按计划推进 M5 前置准备，保持前端不直连外部系统、后端负责标准化与缓存。

## 58. 本轮交接记录

### 本轮目标

- 在 OPC UA 测试连接中，按“节点ID列表”从上到下顺序读取节点值并返回。
- 对读取失败节点明确指出“哪个节点获取不到”。

### 本轮实际完成

- `backend/backoffice/connection_test_services.py`
  - `test_opcua_connection` 新增参数 `node`，支持节点列表输入。
  - 增加节点列表归一化逻辑，兼容旧 `connection_config.nodeId` 回退。
  - 节点读取改为顺序循环读取，输出格式为逐行编号结果。
  - 某节点读取失败时，不中断后续节点读取；最终结果中会标明失败节点及异常信息。
  - 若存在失败节点，测试接口返回失败态并携带完整顺序结果明细。
- `backend/backoffice/views.py`
  - `POST /api/admin/data-source-configs/test-connection` 现在会把请求体中的 `node` 列表透传给 OPC UA 测试服务。
- `backend/backoffice/display_services.py`
  - 数据源健康探测在 OPC UA 场景下同步传入 `source.node`。
- `backend/backoffice/tests.py`
  - 新增 `test_opcua_test_connection_forwards_node_list`，验证节点列表透传与返回文案。

### 本轮未完成

- 未进行真实 OPC UA 服务现场联调。
- 未推进 M5 真实数据接入。
- 未改动双屏页面展示层。

### 修改文件清单

- `backend/backoffice/connection_test_services.py`
- `backend/backoffice/views.py`
- `backend/backoffice/display_services.py`
- `backend/backoffice/tests.py`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 需要兼容旧配置中仍使用 `connection_config.nodeId` 的场景，避免测试连接回归；本轮通过“优先 node 列表，回退 nodeId”的方式兼容。

### 建议下一轮优先任务

- 若继续优化后台体验，建议把“测试连接”结果改为可滚动详情面板展示，避免多节点结果在 toast 中过长难读。
- 若进入下一阶段，继续按既定计划推进 M5 前置准备，保持前端不直连外部系统。

## 59. 本轮交接记录

### 本轮目标

- 给节点列表中的每个节点增加注释说明。
- OPC UA 测试连接结果只输出注释，不输出详细节点路径。

### 本轮实际完成

- `backend/backoffice/serializers.py`
  - OPC UA `node` 列表支持对象结构 `{ nodeId, comment }`。
  - 新增校验：对象项必须包含非空 `nodeId` 与非空 `comment`。
  - 同时保留字符串节点项兼容能力（历史数据不报错）。
- `backend/backoffice/connection_test_services.py`
  - 节点归一化支持对象节点与字符串节点混用。
  - 测试连接逐节点输出从“节点路径”改为“节点注释”。
  - 某节点获取失败时，按注释名输出失败条目并附错误原因。
- `frontend/src/adminResources.js`
  - “节点ID列表”占位示例改为对象数组格式：
    - `nodeId`
    - `comment`
- `backend/backoffice/tests.py`
  - 更新 test-connection 节点透传测试，断言对象列表可正确透传。

### 本轮未完成

- 未做真实 OPC UA 现场联调。
- 未推进 M5 真实数据接入。
- 未改动双屏展示能力。

### 修改文件清单

- `backend/backoffice/serializers.py`
- `backend/backoffice/connection_test_services.py`
- `frontend/src/adminResources.js`
- `backend/backoffice/tests.py`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 需要兼容旧的字符串节点列表，否则会影响已有配置；本轮采用“对象格式优先 + 字符串兼容”的方式平滑过渡。

### 建议下一轮优先任务

- 若继续优化后台体验，建议在“节点ID列表”增加可视化行编辑（nodeId/comment 分栏）以减少 JSON 手工输入错误。
- 若进入下一阶段，继续按既定计划推进 M5 前置准备，保持前端不直连外部系统。

## 60. 本轮交接记录

### 本轮目标

- 新增左屏子页面“设备实时监控”。
- 基于当前 OPC UA 数据源输出设备实时参数。
- 轮询时间按 OPC UA 常规监控刷新周期。
- 连接超时视为设备离线。
- 参数含义依据 `TK.MD` 注释/映射展示。

### 本轮实际完成

- `backend/backoffice/connection_test_services.py`
  - 新增 `read_opcua_nodes(connection_config, node)`，支持：
    - 顺序读取节点值
    - 连接超时/连接失败离线判定
    - 每节点成功/失败结果结构化输出
  - 现有 `test_opcua_connection` 复用该读取能力。
- `backend/backoffice/display_services.py`
  - 左屏 payload 新增 `content.deviceRealtimeMonitor`。
  - 新增 `_build_device_realtime_monitor(area)`：
    - 仅读取绑定到当前区域设备的启用 OPC UA 数据源
    - 返回 `pollIntervalSeconds`（取启用源最小刷新周期）
    - 返回设备卡片（在线/离线、更新时间、参数列表）
  - 新增 TK 节点路径到中文语义映射，用于节点无注释时回填参数含义。
  - 左屏默认模块新增 `deviceRealtimeMonitor` 开关。
- `frontend/src/ScreenDisplay.jsx`
  - 左屏新增 page key：`realtime`（设备实时监控）。
  - 新增实时监控模块渲染：设备卡片、状态徽标、参数值、离线原因。
  - 屏幕轮询间隔支持使用后端返回 `pollIntervalSeconds`（最小 5 秒）。
- `frontend/src/adminResources.js`
  - 左屏可配置页面键新增 `realtime`。
- `frontend/src/styles.css`
  - 新增实时监控页面样式（卡片化、状态色、参数列表、滚动优化）。
- `backend/backoffice/tests.py`
  - 左屏接口测试补充 `deviceRealtimeMonitor` 结构断言。

### 本轮未完成

- 未做真实拼屏环境下的实时监控页面终验。
- 未推进 M5 真实数据接入里程碑。
- 未扩展到报修/3D/内部报表。

### 修改文件清单

- `backend/backoffice/connection_test_services.py`
- `backend/backoffice/display_services.py`
- `backend/backoffice/tests.py`
- `frontend/src/ScreenDisplay.jsx`
- `frontend/src/adminResources.js`
- `frontend/src/styles.css`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 需严格保持“前端不直连外部系统”，因此实时监控读取逻辑全部放在后端服务层完成。
- 节点注释不全时仍需保证可读性，本轮通过 `TK.MD` 路径映射做了后备语义补全。

### 建议下一轮优先任务

- 若继续收口 M4，优先做监控页现场可读性验收（字体密度、刷新频率、离线提示强度）。
- 若进入下一阶段，按计划推进 M5 前置准备，继续保持前后端边界不变。

## 61. 本轮交接记录

### 本轮目标

- 解决左屏“设备实时监控”等待时间长的问题。
- 调整实时参数展示样式，避免纯文字列表观感差。

### 本轮实际完成

- `backend/backoffice/display_services.py`
  - `deviceRealtimeMonitor` 数据构建由串行读取改为线程池并发读取。
  - 每个 OPC UA 数据源异步发起读取请求，降低整体等待时间。
  - 读取结果收集后按 `sourceCode` 排序，保证卡片顺序稳定。
- `frontend/src/ScreenDisplay.jsx`
  - 实时参数 UI 从列表行改为“图例卡片”样式：
    - 左侧状态点 + 参数名
    - 右侧参数值/失败状态
- `frontend/src/styles.css`
  - 新增图例样式与状态色：
    - 成功项绿色体系
    - 失败项红色体系
    - 双列卡片布局，减少密集文字堆叠

### 本轮未完成

- 未进入 M5 真实数据源接入阶段。
- 未在真实拼屏环境做最终视觉验收。

### 修改文件清单

- `backend/backoffice/display_services.py`
- `frontend/src/ScreenDisplay.jsx`
- `frontend/src/styles.css`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 串行读取模式下，任一慢设备都会拖慢整页返回；本轮通过并发读取降低整体阻塞。
- 纯文字列表在大屏观感上信息层级差，本轮通过图例化卡片提高可读性。

### 建议下一轮优先任务

- 若继续收口 M4，建议把实时参数按业务域分组（运行/程序/速度/报警）并支持折叠，进一步减少单屏信息拥挤。

## 62. 本轮交接记录

### 本轮目标

- 去掉设备监控页面区域高度限制，解决重叠问题。
- 将实时监控视觉从文字列表升级为更可视化的驾驶舱风格。

### 本轮实际完成

- `frontend/src/ScreenDisplay.jsx`
  - 新增实时监控 KPI 概览区（设备总数/在线设备/离线设备）。
  - 当页面仅展示 `deviceRealtimeMonitor` 时，启用独立实时页布局类 `screen-grid-left-realtime`。
  - 实时监控面板新增 `panel-unbounded` 标记，避免继承通用卡片高度约束导致内容叠压。
- `frontend/src/styles.css`
  - 新增 `screen-grid-left-realtime` 与 `panel-unbounded` 样式，解除原三卡同高限制。
  - 实时设备卡片网格改为自适应列（`repeat(auto-fill, minmax(320px, 1fr))`），避免固定列在不同屏幕下重叠。
  - 新增 KPI 可视化卡片样式（在线/离线状态色），增强“高大上”观感。
  - 提升实时设备卡片最小高度，缓解内容拥挤。

### 本轮未完成

- 未扩展后端数据结构。
- 未推进 M5 真实数据接入。
- 未进行真实拼屏环境终验。

### 修改文件清单

- `frontend/src/ScreenDisplay.jsx`
- `frontend/src/styles.css`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 原实时页复用了左屏通用网格高度约束，导致在实时监控场景下容易挤压与重叠；本轮通过“实时页独立布局模式”解耦处理。

### 建议下一轮优先任务

- 若继续收口实时监控可视化，建议把参数按“运行/程序/速度/报警”做分组卡片并增加图标，进一步提升可读性和视觉层次。

## 63. 本轮交接记录

### 本轮目标

- 设备监控参数分组显示。
- 基础信息不参与实时轮询且不在监控页展示。
- 监控页视觉再升级，避免混在一起难看。

### 本轮实际完成

- `backend/backoffice/display_services.py`
  - 新增 TK 节点分组映射并返回 `groupedParameters`。
  - 新增基础信息节点集合：轮询时过滤掉基础信息节点。
  - 节点注释仍优先使用配置注释，缺失时按 TK 路径映射自动补语义。
- `frontend/src/ScreenDisplay.jsx`
  - 实时参数展示改为“按分组块”渲染。
  - 新增基础信息已过滤的空态提示。
- `frontend/src/styles.css`
  - 新增分组块、分组标题和分组内参数自适应布局样式，整体视觉更规整。

### 本轮未完成

- 未推进 M5 真实数据接入。
- 未做真实拼屏终验。

### 修改文件清单

- `backend/backoffice/display_services.py`
- `frontend/src/ScreenDisplay.jsx`
- `frontend/src/styles.css`
- `docs/STATUS.md`
- `docs/HANDOFF.md`

### 遇到的问题

- 既要兼容旧节点配置格式，又要在新页面上分组显示；本轮通过后端分组构建并保留兼容字段解决。

### 建议下一轮优先任务

- 若继续收口 M4，建议增加分组折叠与分组图标，进一步提升大屏驾驶舱观感。

## 64. 后台 antd 重构交接（M-B0 ~ M-B4）

### 架构结果

- 路由：`react-router-dom`，扁平路径 `/admin/{slug}`（如 `/admin/devices`）。
- 壳层：`AdminLayout` + antd `Menu` / `Header` / `Sider`。
- 业务页：19 个 `pages/*Page.jsx`，经 `createResourcePage` 复用 `ResourceCrudPage`。
- 表单/对话框：`ResourceField`（antd）、`AdminDialogs`（antd Modal + Table）。
- 代码分割：`App.jsx` lazy 加载 `AdminApp`；`adminRouteRegistry.js` 按页 lazy；`vite.config.js` 拆分 `antd` / `react-vendor` chunk。

### 已删除的旧实现

- `ResourceEditor.jsx`、`ResourceModalForm.jsx`、`ResourceQueryBar.jsx`
- `ledger/ResourceTable.jsx`、`sidebar/ResourceSidebar.jsx`
- `admin.css` 中旧 table/modal/field/transfer 样式（现约 490 行）

### 验证命令

```bash
cd frontend && npm run build
```

构建产物应包含独立 `antd-*.js`、`AdminApp-*.js`、各 `*Page-*.js` 与共享 `createResourcePage-*.js`。

### 建议冒烟

- P0：`/admin/login` → 默认页；深链刷新；侧栏高亮
- P1：devices CRUD；screen-configs 穿梭框；OPC UA 历史 Modal
- P2：`/screen/*` 不受 antd 影响；暗/亮主题切换

## 65. Schema 拆分交接（M-C1）

### 本轮目标

- 将原 ~1170 行 `adminResources.js` 按职责拆分为 `frontend/src/admin/schemas/` 多文件。
- 编写 `docs/ADMIN_SCHEMA.md` 初稿，说明 ResourceDefinition 与扩展 Tier。

### 本轮实际完成

- **目录拆分**
  - `shared.js` — `OMIT_VALUE`、`RESERVED_FIELDS`
  - `options.js` — 下拉选项与页面键常量
  - `menu.js` — `ADMIN_MENU_GROUPS`、`DEFAULT_ADMIN_RESOURCE`
  - `formUtils.js` — 表单/列工具函数
  - `ledger.js` / `screen.js` / `system.js` — 分组 resource 定义
  - `dataSources.js` — `buildDataSourceResources()` 动态 6 类数据源
  - `index.js` — 合并 `resourceDefinitions` + `assertResourceDefinitions()`
- **兼容入口**：`frontend/src/adminResources.js` 仅 `export * from "./admin/schemas/index.js"`，现有 `import '../../adminResources.js'` 无需改动。
- **文档**：`docs/ADMIN_SCHEMA.md`（字段表、Field 类型、列格式、bulkApplyToolbar、Tier A/B/C、devices / screenConfigs 示例）。
- **构建**：`cd frontend && npm run build` 通过；启动时校验侧栏 19 个叶子 key 均有 schema。

### 修复项（拆分脚本遗留）

- `screen.js`：`displayContentConfigs` 缺少闭合 `},`
- `dataSources.js`：`buildDataSourceResources` 改为 `export function`

### 未完成 / 下一轮

- M-C3：新增页面 SOP 与 Tier 决策流程写入 STATUS/PLAN

### 建议冒烟

- `/admin/devices` — 标准 Tier A CRUD
- `/admin/screen-configs` — 宽 Modal + 穿梭框 + 批量轮播
- `/admin/operation-logs` — 只读列表 + `cstDateTime` 列
- `/admin/opcua-data-source`（或对应 slug）— 测试连接 / 历史 / 复制新增

### 修改文件清单

- `frontend/src/adminResources.js`
- `frontend/src/admin/schemas/**`
- `frontend/scripts/split-admin-resources.py`（可选保留）
- `docs/ADMIN_SCHEMA.md`
- `docs/HANDOFF.md`

## 66. Schema 校验交接（M-C2）

### 本轮目标

- JSDoc typedef 描述 ResourceDefinition 结构。
- 轻量运行时校验：字段类型、列格式、关联引用、批量工具条形态。
- 可独立执行的 `npm run validate:schemas`（含菜单 ↔ 路由注册表对齐）。

### 本轮实际完成

- **`schemaTypes.js`** — `@typedef ResourceDefinition` / `FieldDefinition` / `ColumnDefinition` / `BulkApplyToolbar` 等。
- **`schemaRegistry.js`** — `FORM_FIELD_TYPES`、`QUERY_FIELD_TYPES`、`CELL_FORMATS`、`BULK_*` 白名单。
- **`validateResourceDefinitions.js`** — `collectResourceDefinitionErrors()` + `validateResourceDefinitions()`；`index.js` 构建时调用后者。
- **`scripts/validate-admin-schemas.mjs`** + **`package.json`** → `"validate:schemas"`.
- **`docs/ADMIN_SCHEMA.md`** §10 更新为 M-C2 校验说明。

### 验证

```bash
cd frontend && npm run validate:schemas   # 20 definitions, 19 routes
cd frontend && npm run build              # 构建时同样校验 schema
```

### 未完成 / 下一轮

- M-C4：注册表驱动 `ResourceField` / `formatCellValue`，减少引擎 if 链

### 修改文件清单

- `frontend/src/admin/schemas/schemaTypes.js`（新）
- `frontend/src/admin/schemas/schemaRegistry.js`（新）
- `frontend/src/admin/schemas/validateResourceDefinitions.js`（新）
- `frontend/src/admin/schemas/index.js`
- `frontend/scripts/validate-admin-schemas.mjs`（新）
- `frontend/package.json`
- `docs/ADMIN_SCHEMA.md`
- `docs/HANDOFF.md`

## 67. Tier 分级与 SOP 交接（M-C3）

### 本轮目标

- 将 Tier A/B/C 决策流程与新增后台页 SOP 写入 **`docs/PLAN.md` §12**。
- 在 **`docs/STATUS.md` §90** 记录 M-B/M-C 完成状态与团队约定。
- 更新 **`docs/ADMIN_SCHEMA.md`**：Tier 速查、文件级清单、文档索引。

### 本轮实际完成

- **`PLAN.md` §12** — Tier 表、决策流程、Tier A 十步 SOP、修改现有页 SOP、验收标准、与 M-C4/M-C5 关系。
- **`STATUS.md` §90** — M-B0～B4、M-C1～C3 状态表；新增页约定；验证命令。
- **`ADMIN_SCHEMA.md`** — §7 Tier A+、§9 文件级清单、§11 维护文档索引。

### 不做 M-C4/M-C5 时的约定（已写入 PLAN §12.7）

- Tier B 需求：优先 Tier C 独立页，或临时接受引擎 `resourceKey` 分支。
- 三处注册（menu / `ADMIN_RESOURCE_KEYS` / `PAGE_LOADERS`）继续人工同步；`validate:schemas` 覆盖 menu ↔ 路由键。

### 修改文件清单

- `docs/PLAN.md`
- `docs/STATUS.md`
- `docs/ADMIN_SCHEMA.md`
- `docs/HANDOFF.md`
