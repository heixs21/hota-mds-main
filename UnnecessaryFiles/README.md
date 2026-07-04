# UnnecessaryFiles 说明

本目录用于存放**已从原路径移出、不再参与项目构建与运行**的文件。移入此处是为了与活跃代码/文档分离，便于后续确认后彻底删除或归档，而**不是**立即从 Git 历史中抹除。

整理时间：2026-07-04  
项目阶段：M4 已完成，M5 进行中（参考 `docs/STATUS.md`）

---

## 1. 本目录现有文件及移出原因

| 当前文件名 | 原路径 | 类型 | 为何不再需要 |
|---|---|---|---|
| `linear.md` | `frontend/linear.md` | AI 设计风格参考 | 开发 M4 大屏时的 Linear 风格灵感文档；样式已落地到 `frontend/src/styles.css`，代码与构建无任何引用 |
| `airtable.md` | `frontend/airtable.md` | AI 设计风格参考 | 同上，Airtable 风格参考，仓库内零引用 |
| `preview_svgs.html` | `docs/PRD/preview_svgs.html` | 概念图本地预览 | 仅用于浏览器打开 SVG 效果图，不参与前端构建、后端 API 或部署 |
| `screen-left-concept.svg` | `docs/PRD/screen-left-concept.svg` | PRD 概念 SVG | 仅被 `preview_svgs.html` 引用；正式 PRD 使用的是 PNG（见下「需保留」） |
| `screen-right-concept.svg` | `docs/PRD/screen-right-concept.svg` | PRD 概念 SVG | 同上 |
| `hota-logo.png` | `docs/PRD/hota-logo.png` | 概念图素材 | 仅嵌入上述两个 SVG，无业务代码引用 |
| `screen-left-concept.png` | `docs/PRD/screen-left-concept.png` | 概念 PNG（重复） | 与 `docs/PRD/assets/screen-left-concept.png` 重复；PRD 正文引用的是 `assets/` 下版本 |
| `screen-right-concept.png` | `docs/PRD/screen-right-concept.png` | 概念 PNG（重复） | 与 `docs/PRD/assets/screen-right-concept.png` 重复 |

**移出后的影响：** 无。`npm run build`、`python manage.py test`、`docker compose` 及大屏/后台功能均不依赖上述文件。

**需继续保留的相关文件（未移入本目录）：**

- `docs/PRD/assets/screen-left-concept.png`
- `docs/PRD/assets/screen-right-concept.png`  
  → `docs/PRD/PRD_和泰智屏系统.md` 第 11 节概念效果图仍引用这两张图。

---

## 2. 后期可考虑移入或删除的文件（Git 已跟踪）

以下文件**当前仍在仓库活跃路径**，删除/移出前请团队确认。按风险从低到高排列。

### 2.1 中置信度 — 可删，主要损失设计/运维文档

| 文件路径 | 类型 | 说明 |
|---|---|---|
| `frontend/framer.md` | M4 风格参考 | Framer 风格说明；大屏视觉已实现，`DOCS_OVERVIEW.md` 等文档仍有提及，移出后需同步改一句文档 |
| `frontend/sentry.md` | M4 布局参考 | Sentry 风格说明；同上 |
| `docs/电视页面白屏问题说明.md` | 故障排查 | 小米电视 WebView 白屏/布局问题记录；不参与构建，现场排障时仍有参考价值 |
| `后台管理控制台操作说明.md` | 操作草稿 | 根目录中文说明，部分字段标注「暂时没法显示」，未列入 README 必读 |

### 2.2 低置信度 — 开发/部署辅助，按需保留

| 文件路径 | 类型 | 说明 |
|---|---|---|
| `backend/backoffice/management/commands/seed_device_samples.py` | 一次性 seed 命令 | 生成 100 条示例设备；测试与文档未引用，本地造数时可能有用 |
| `ecosystem.config.cjs` | PM2 配置 | 非 Docker 场景下用 Gunicorn 托管 Django；主部署路径为 `docker-compose.yml`，且已在 `.gitignore` 中但仍被 Git 跟踪 |

---

## 3. 本地产物 — 可随时清理，通常不应提交 Git

这些文件**不在 Git 跟踪范围内**（或已在 `.gitignore`），清理后不影响仓库；需要时可重新生成。

| 路径 | 说明 |
|---|---|
| `backend/test.sqlite3` | 本地 `hota_mds.test_settings` SQLite 库，易失；迁移不一致时应删除后 `migrate` 重建 |
| `.codex-logs/` | 本地前后端运行日志（若存在） |
| `frontend/node_modules/` | npm 依赖，`npm install` 恢复 |
| `frontend/dist/` | 前端构建产物，`npm run build` 恢复 |
| `**/__pycache__/` | Python 字节码缓存 |

---

## 4. 明确不应删除的内容

| 类别 | 原因 |
|---|---|
| **`backend/backoffice/migrations/*.py`** | Django 数据库版本链；含表结构变更与 `RunPython` 数据迁移。删除会导致 `migrate` 失败、新环境无法建库、与已部署库 `django_migrations` 不一致 |
| **`docs/TK.MD`** | 后端 OPC UA 节点语义映射（`display_services.py` 运行期依赖） |
| **`SCREEN_API.md`** | 大屏接口说明，`docs/DATA_REALITY.md` 引用 |
| **核心文档**（`docs/SPEC.md`、`PLAN.md`、`STATUS.md`、`HANDOFF.md` 等） | 项目事实源与交接依据（见 `docs/AGENTS.md`） |
| **`seed_*` 管理命令及 `*_seed.py`** | 销轴/套筒滚子等区域真实接入与测试在用 |
| **`frontend/src/PlaceholderScreen.jsx`** | 根路由 `/` 仍在使用 |
| **`frontend/src/AdminConsole.jsx`** | 重导出 `admin/AdminConsole.jsx`，后台路由依赖 |

若需「整理迁移文件」，应使用 Django 官方的 **`squashmigrations`** 流程在专项分支上操作，**不要**直接删除单个迁移文件。

---

## 5. 使用建议

1. **确认无引用后再彻底删除：** 移入本目录后观察 1～2 个迭代，无回归即可 `git rm UnnecessaryFiles/...` 整目录清理。
2. **新增移入文件时：** 在本 README「第 1 节」表格追加一行，写明原路径与移出原因。
3. **文档类文件移出时：** 同步检查 `README.md`、`DOCS_OVERVIEW.md`、`docs/STATUS.md` 是否仍引用旧路径。

---

## 6. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-07-04 | 初版：移入 8 个设计参考/概念图文件；补充后期可删清单与迁移文件保留说明 |
