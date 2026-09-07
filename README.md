# 公司内部内容自动发布平台前端

面向公司内部的内容提交、审核、自动发布与检索平台。前端只负责用户交互和 REST API 调用，不读取服务器目录、不处理文件转换，也不自行拼接发布 URL。

配套 FastAPI + PostgreSQL 后端位于 `backend/`。本地一键启动、联调和验收见 [`docs/LOCAL_DEVELOPMENT.md`](docs/LOCAL_DEVELOPMENT.md)；无 root 权限的服务器部署见 [`docs/SERVER_DEPLOYMENT_NON_ROOT_README.md`](docs/SERVER_DEPLOYMENT_NON_ROOT_README.md)，有 root 权限的部署见 [`docs/SERVER_DEPLOYMENT_README.md`](docs/SERVER_DEPLOYMENT_README.md)；验收结果见 [`docs/LOCAL_INTEGRATION_TEST_REPORT.md`](docs/LOCAL_INTEGRATION_TEST_REPORT.md)。

## 技术栈

- Vue 3 + TypeScript + Vite
- Vue Router、Pinia、Axios
- Element Plus
- Composition API 与 `<script setup lang="ts">`

## 运行环境

推荐 Node.js 22 LTS（最低建议 Node.js 20.19+），npm 10+。

## 安装与启动

首先启动数据库服务：

```powershell
.\local-data\postgres\pgsql\bin\pg_ctl.exe start `
  -D ".\local-data\postgres-data" `
  -l ".\local-data\postgres\pgsql\postgres.log"
```

完整本地环境可从项目根目录一键启动：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

脚本会执行数据库迁移和 Seed，并启动前端与 FastAPI；首次数据库配置见 [`docs/LOCAL_DEVELOPMENT.md`](docs/LOCAL_DEVELOPMENT.md)。仅启动前端时使用：

```bash
npm install
npm run dev
```

开发服务器默认地址为 `http://localhost:5173`。

生产构建：

```bash
npm run build
npm run preview
```

代码检查：

```bash
npm run lint
```

## 环境变量

复制 `.env.example` 为 `.env.local`，按需配置：

```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_USE_MOCK=false
```

- `VITE_API_BASE_URL`：真实后端 API 基础地址。页面内没有写死后端地址。
- `VITE_USE_MOCK=true`：使用浏览器本地 Mock 数据，可演示完整业务流程。
- `VITE_USE_MOCK=false`：通过 Axios 调用真实后端 REST API。

## Mock 模式

Mock 数据保存在浏览器 `localStorage`，切换账号后员工提交的内容、审核结果、发布日志仍然保留，适合演示完整闭环。

| 角色 | 用户名 | 密码 |
|---|---|---|
| 管理员 | `admin` | `admin123` |
| 普通员工 | `employee` | `employee123` |

Mock 模式账号保存在浏览器本地；真实 API 模式由后端 Seed 创建同名本地开发账号。部署到共享或生产环境前必须替换默认密码。

## 真实 API 模式

设置 `VITE_USE_MOCK=false`，并将 `VITE_API_BASE_URL` 指向后端统一 `/api` 地址。所有页面只依赖 `src/api/` 中的接口模块；如果后端响应字段存在差异，只需在该层适配。

Axios 会统一添加 `Authorization: Bearer {token}`，并处理网络错误、401 登录失效与 403 权限不足。

## 多文件与多发布目标

- 新建或编辑内容时可选择多个文件，也可选择文件夹并保留相对目录结构；新选择会整体替换已有文件。
- 多文件/文件夹的内容预览只展示可下载的文件清单。单个 PPT 也按普通文件展示文件名，不再生成与原文不一致的文字预览。
- 管理员可配置公司服务器目录（Local）、SFTP、GitHub Repository、GitHub Pages、Microsoft OneDrive 和 Dropbox，并在发布配置页执行“测试连接”。
- 普通员工只会看到目标名称、类型和适用内容类型，不会收到物理目录、仓库、服务器或凭证配置。
- Token、密码、Client Secret 与私钥只由后端通过 `credential_ref` 对应的环境变量读取。具体字段、变量命名及扩展 Adapter 方法见 [`backend/README.md`](backend/README.md)。

## 页面路由

| 路由 | 页面 | 权限 |
|---|---|---|
| `/login` | 登录 | 公开 |
| `/` | 工作台 | 已登录 |
| `/contents` | 内容管理 / 我的内容 | 已登录 |
| `/contents/new` | 新建内容 | 已登录 |
| `/contents/:id` | 内容详情与预览 | 已登录，受数据权限约束 |
| `/contents/:id/edit` | 编辑内容 | 已登录，受内容状态与归属约束 |
| `/search` | 已发布内容检索 | 已登录 |
| `/reviews` | 审核队列 | 管理员 |
| `/reviews/:contentId` | 审核详情 | 管理员 |
| `/users` | 用户管理 | 管理员 |
| `/settings/publish-targets` | 发布配置 | 管理员 |
| `/logs` | 操作与发布日志 | 管理员 |
| `/403` | 无权限 | 公开 |

## 权限说明

- 路由守卫会拦截未登录访问，并将普通员工访问管理员页面重定向到 `/403`。
- 普通员工只能看到、编辑和删除自己的可编辑内容，待审核或已发布内容不可编辑。
- 普通员工只能提交发布申请，不能直接正式发布。
- 管理员审核通过或直接发布时，前端只调用后端 API。
- 普通员工使用的发布目标数据不包含服务器物理目录；物理目录仅管理员的发布配置和审核核对页面可见。
- 最终访问地址始终使用 API 返回的 `view_url`，前端不拼接 URL。

## 项目目录

```text
src/
├─ api/          # Axios 实例与按业务拆分的 API
├─ components/   # 状态、表单、上传、预览、流程轨迹等公共组件
├─ constants/    # 状态、类型、分类与文件格式常量
├─ layouts/      # 管理后台整体布局与角色菜单
├─ mock/         # 可持久化的完整 Mock 业务层
├─ pages/        # 11 类业务页面及 403 / 404
├─ router/       # 路由定义与认证、角色守卫
├─ stores/       # Pinia 认证与界面状态
├─ styles/       # 全局设计系统
├─ types/        # 领域模型与分页类型
└─ utils/        # 日期、文件大小等格式化方法
```

## 已覆盖的演示流程

1. 管理员新增、编辑、启用或禁用用户。
2. 员工创建内容、上传文件、按类型选择发布目标并保存草稿。
3. 员工提交审核后内容锁定。
4. 管理员在审核详情中核对预览、物理目录、URL 根地址与历史记录。
5. 管理员驳回，员工查看原因、修改并重新提交。
6. 管理员审核通过并触发后端自动发布，获得 `view_url`。
7. 对预置发布失败内容执行重新发布，无需重复审核。
8. 员工仅能检索并打开已发布内容。
9. 管理员查看操作日志和发布日志。



