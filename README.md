# 和泰智造数屏系统

一期前段目标是建设面向外部参观的左右双屏大屏。当前代码状态已完成 `M4`，也就是基于 mock/cache API 的双屏展示链路已经跑通；`M5` 真实数据源接入尚未开始。

## 开发前先读

以下文档是当前项目的唯一事实来源，继续开发前必须先读：

1. `docs/PRD/PRD_和泰智屏系统.md`
2. `docs/SPEC.md`
3. `docs/PLAN.md`
4. `docs/STATUS.md`
5. `docs/HANDOFF.md`
6. `docs/AGENTS.md`
7. `docs/DECISIONS.md`

补充参考文档：

- `docs/API_CONTRACT.md`
- `docs/DB_MODEL_DRAFT.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `DOCS_OVERVIEW.md`

## 当前阶段

当前已完成：

- `M1` 工程骨架与基础部署
- `M2` 后台基础能力与主数据维护
- `M3` 标准数据模型、缓存层与 mock 数据
- `M4` 一期前段双屏大屏页面
- 左右屏独立 URL：`/screen/left`、`/screen/right`
- 左右屏自动轮播、全屏按钮与双击全屏
- 左右屏按各自配置读取标题、页面顺序、模块开关和轮播秒数
- 左屏综合运行展示、右屏排产甘特图展示
- 报修占位区与 3D 占位区
- 数据异常时保留最近一次成功数据，不白屏
- 后台最小管理界面：`/admin/login`、`/admin/console`

当前未完成：

- `M5` 真实外部系统接入
- 报修真实接入
- 3D 仿真真实开发
- 二期内部 Web 报表
- 真实拼屏/kiosk 现场联调与终验

## 当前明确边界

- 一期前段只做外部参观双屏大屏，不做内部 Web 报表。
- 报修与 3D 仿真不是一期前段阻塞项。
- 前端不得直连外部系统。
- 后端负责定时拉取、标准化、缓存并对前端提供 API。
- 数据源异常时，大屏必须显示最近一次成功数据，不允许白屏。
- 大屏不显示“数据过期”提示，数据源健康状态放在后台查看。
- 一期后台只做管理员权限，不做复杂 RBAC。
- 外部系统连接信息不得写死在代码中。

## 技术栈


| 模块             | 技术                             |
| -------------- | ------------------------------ |
| backend        | Django + Django REST Framework |
| frontend       | React + Vite                   |
| collector      | Python 独立采集服务目录                |
| database       | MySQL                          |
| deploy         | Docker Compose                 |
| target runtime | Ubuntu                         |


## 主要路由

| 路由 | 说明 |
| --- | --- |
| `http://localhost:8000/api/health` | 后端健康检查 |
| `http://localhost:8000/api/screens/left` | 左屏展示 API（M4） |
| `http://localhost:8000/api/screens/right` | 右屏展示 API（M4） |
| `http://localhost:8000/api/admin/auth/login` | 后台管理员登录 API（M2） |
| `http://localhost:8000/api/admin/auth/me` | 当前管理员信息 API（M2） |
| `http://localhost:8000/api/admin/data-source-healths` | 数据源健康状态 API（M3/M4 运维查看） |
| `http://localhost:3000/screen/left` | 左屏展示页（M4） |
| `http://localhost:3000/screen/right` | 右屏展示页（M4） |
| `http://localhost:3000/admin/login` | 后台登录页 |
| `http://localhost:3000/admin/console` | 后台控制台 |


## 本地启动

1. 准备环境变量

```bash
cp .env.example .env
```

1. 使用 Docker Compose 启动

```bash
docker compose up --build
```

1. 打开路由验证服务

- 后端健康检查：`http://localhost:8000/api/health`
- 左屏页面：`http://localhost:3000/screen/left`
- 右屏页面：`http://localhost:3000/screen/right`
- 后台登录页：`http://localhost:3000/admin/login`

## 本地开发

### 后端

```bash
cd backend
python manage.py migrate
python manage.py load_mock_screen_data
python manage.py runserver
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

说明：

- 前端开发环境通过 Vite 代理访问本地 backend 的 `/api`。
- 当前双屏开发与验证默认基于 mock/cache API。
- 项目正式约束仍是 MySQL；`hota_mds.test_settings` 仅用于本地测试与验证。

## 验证命令

### Docker 基础验证

```bash
docker compose config
docker compose up --build
```

### 后端验证

```bash
cd backend
python -m compileall .
python manage.py test accounts backoffice --settings=hota_mds.test_settings
python manage.py migrate --settings=hota_mds.test_settings
python manage.py load_mock_screen_data --settings=hota_mds.test_settings
```

### 前端验证

```bash
cd frontend
npm run build
```

## 当前后台能力

当前后台接口前缀为 `/api/admin/`，已覆盖以下资源：

- `auth/login`
- `auth/logout`
- `auth/me`
- `areas`
- `production-lines`
- `devices`
- `employees`
- `materials`
- `orders`
- `code-mappings`
- `screen-configs`
- `display-content-configs`
- `runtime-parameter-configs`
- `page-module-switches`
- `data-source-configs`
- `data-source-healths`
- `operation-logs`

## 下一步方向

在不扩大范围的前提下，下一阶段应进入 `M5` 前置准备或真实数据源接入；但仍必须保持以下边界：

- 前端只读本系统标准 API
- 真实数据接入由 backend/collector 负责
- 报修、3D 仿真、内部 Web 报表继续排除在当前优先级之外

