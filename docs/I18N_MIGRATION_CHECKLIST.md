# 多语言迁移检查清单

本清单记录在现有中文系统上增量加入 `zh-CN`、`ja-JP`、`en-US` 的扫描范围、改造结果和回归项。业务数据、数据库状态值、角色值、API 路径和发布目标类型均不参与翻译。

## 现状扫描与改造结果

- [x] 页面：登录、工作台、内容列表/表单/详情/预览、审核列表/详情、检索、用户、部门、分类、发布配置、日志、403、404。
- [x] 公共区域：主布局、侧栏、Header、面包屑、页面标题、状态标签、发布流程、上传器、预览器、弹窗和消息。
- [x] 硬编码 UI：页面标题、卡片标题、按钮、Tab、表格列、筛选条件、Label、Placeholder、空状态、校验提示、确认提示和操作结果提示。
- [x] 映射项：角色、用户状态、可见范围、审核状态、发布状态、发布记录状态、内容类型、发布目标类型和操作日志 action。
- [x] 路由元数据由静态标题改为 `meta.i18nKey`，`document.title` 随语言响应式更新。
- [x] 日期和文件大小数字统一通过 `Intl.DateTimeFormat` / `Intl.NumberFormat` 输出。
- [x] 后端高频业务异常增加稳定 `error_code`，原 `message` 保留；未知 code 继续显示后端 message。
- [x] Axios 随每次请求发送当前 `Accept-Language`。

## 语言基础设施

- [x] 使用 Vue 3 Composition API 版 `vue-i18n`。
- [x] 默认语言和 fallback 均为 `zh-CN`，不读取浏览器语言。
- [x] 只接受 `zh-CN`、`ja-JP`、`en-US`；缺失或非法 `localStorage.app_locale` 回退中文。
- [x] 登录页右上角和登录后 Header 右上角均提供语言切换。
- [x] 切换即时生效，仅更新 locale 和 localStorage，不跳转、不登出、不重建当前页面。
- [x] Element Plus 的中文、日语、英语 locale 与应用语言联动。
- [x] 三种语言由同一 catalog 生成，键集合天然一致；自动脚本同时检查文本非空和插值参数一致。

## 明确不翻译的内容

- [x] 内容标题、内容描述、分类名、部门名、文件名、审核备注、驳回原因和上传文件正文。
- [x] 数据库中的 `admin` / `employee`、审核/发布状态、PublishRecord 状态和 PublishTarget `target_type`。
- [x] `credential_ref`、仓库、目录、远程路径、第三方配置和 API path。
- [x] 后端内部日志正文；`operation_logs.action` 保持稳定内部值，只在前端映射显示。
- [x] 未新增用户语言字段、语言表或 Alembic migration。

## 自动检查与回归

在项目根目录执行：

```bash
npm run check:i18n
npm run lint
npm run build
cd backend
pytest
```

- [x] 翻译键完整性检查纳入 `npm run check:i18n`。
- [x] 前端类型检查和生产构建纳入 `npm run build`。
- [x] 后端异常响应保持 `success`、`data`、`message` 兼容字段。
- [x] 权限守卫仍按内部角色判断，不依赖当前语言。
- [x] 发布 Adapter 不读取 UI locale，发布配置和业务路径保持原值。

最近一次本地执行结果（2026-09-17）：`check:i18n` 通过（564 keys / 3 locales）、ESLint 通过、生产构建通过、Pytest 90 项全部通过。

## 人工验收建议

- [ ] 清除 `app_locale` 后首次打开显示中文。
- [ ] 分别切换日语、英语并刷新，语言选择保持。
- [ ] 将 `app_locale` 手工改为 `xx-XX`，刷新后回退中文。
- [ ] 在填写中的内容表单切换语言，确认输入内容和已选文件不丢失。
- [ ] 使用管理员与普通员工账号验证菜单和路由权限不受语言影响。
- [ ] 走通创建草稿、提交、驳回、修改、重新提交、通过、发布失败和重新发布流程。
- [ ] 在实际凭证环境分别回归 Local、SFTP、GitHub、GitHub Pages、OneDrive、Dropbox 发布和已发布内容打开。

最后两组需要连接部署环境及第三方真实凭证，因此保留为部署验收项。
