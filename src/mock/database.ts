import type { ContentItem, ContentPayload, ContentQuery, ContentType, PublishStatus } from '@/types/content'
import type { Category, CategoryPayload } from '@/types/category'
import type { DashboardData } from '@/types/dashboard'
import type { Department, DepartmentPayload } from '@/types/department'
import type { PageResult } from '@/types/api'
import type { OperationLog, OperationLogQuery, PublishLog, PublishLogQuery, PublishTarget, PublishTargetPayload } from '@/types/publish'
import type { ReviewDetail, ReviewQuery, ReviewRecord } from '@/types/review'
import type { CurrentUser, User, UserPayload, UserQuery, UserStatus } from '@/types/user'

interface StoredUser extends User { password: string }
interface Database {
  users: StoredUser[]
  departments: Department[]
  categories: Category[]
  contents: ContentItem[]
  targets: PublishTarget[]
  reviews: ReviewRecord[]
  operationLogs: OperationLog[]
  publishLogs: PublishLog[]
}

const DB_KEY = 'publish-console-mock-db-v1'
const SESSION_KEY = 'publish-console-mock-session'
const wait = (ms = 220) => new Promise((resolve) => setTimeout(resolve, ms))
const now = () => new Date().toISOString()
const ago = (hours: number) => new Date(Date.now() - hours * 3600_000).toISOString()
const allContentTypes: ContentType[] = ['html', 'dynamic', 'ppt', 'pdf', 'word', 'excel', 'image', 'file']

function initialDatabase(): Database {
  return {
    users: [
      { id: 1, username: 'admin', password: 'admin123', name: '系统管理员', department: '管理部', role: 'admin', status: 'active', created_at: ago(24 * 120), updated_at: ago(24 * 120) },
      { id: 2, username: 'employee', password: 'employee123', name: '林知夏', department: '产品部', role: 'employee', status: 'active', created_at: ago(24 * 70), updated_at: ago(24 * 70) },
      { id: 3, username: 'wangqi', password: 'demo123', name: '王启', department: '销售部', role: 'employee', status: 'active', created_at: ago(24 * 42), updated_at: ago(24 * 42) },
      { id: 4, username: 'chenmo', password: 'demo123', name: '陈默', department: '研发部', role: 'employee', status: 'disabled', created_at: ago(24 * 30), updated_at: ago(24 * 30) }
    ],
    departments: ['管理部', '综合部', '产品部', '销售部', '研发部'].map((name, index) => ({
      id: index + 1,
      name,
      enabled: true,
      sort_order: (index + 1) * 10,
      created_at: ago(24 * 120),
      updated_at: ago(24 * 120)
    })),
    categories: ['制度规范', '产品资料', '销售方案', '培训材料', '品牌素材', '公共资源'].map((name, index) => ({
      id: index + 1,
      name,
      enabled: true,
      sort_order: (index + 1) * 10,
      visibility_scope: 'all',
      department: null,
      created_at: ago(24 * 120),
      updated_at: ago(24 * 120)
    })),
    targets: [
      { id: 1, name: '产品部发布区', target_type: 'local', content_types: [...allContentTypes], config: {}, publish_root: '/data/company/site/', base_url: 'https://internal.example.com/site/', enabled: true, created_at: ago(24 * 90) },
      { id: 2, name: '培训部发布区', target_type: 'local', content_types: [...allContentTypes], config: {}, publish_root: '/data/company/presentation/', base_url: 'https://internal.example.com/presentation/', enabled: true, created_at: ago(24 * 80) },
      { id: 3, name: '综合管理部发布区', target_type: 'local', content_types: [...allContentTypes], config: {}, publish_root: '/var/www/company/docs/', base_url: 'https://internal.example.com/docs/', enabled: true, created_at: ago(24 * 65) },
      { id: 4, name: '公共资料发布区', target_type: 'local', content_types: [...allContentTypes], config: {}, publish_root: '/data/company/assets/', base_url: 'https://internal.example.com/assets/', enabled: true, created_at: ago(24 * 40) }
    ],
    contents: [
      { id: 101, title: '2026 秋季产品路线图', description: '面向销售与交付团队的产品方向说明与里程碑。', category: '产品资料', content_type: 'ppt', file_name: 'product-roadmap-2026.pptx', file_size: 8_421_300, content_body: null, created_by: 2, creator_name: '林知夏', created_at: ago(62), updated_at: ago(4), submitted_at: ago(4), review_status: 'pending', publish_status: 'unpublished', publish_target_id: 2, publish_target_name: '培训部发布区', published_at: null, view_url: null, reject_reason: null, failure_reason: null },
      { id: 102, title: '品牌视觉资产使用规范', description: 'Logo、安全区、字体与常用物料规范。', category: '品牌素材', content_type: 'pdf', file_name: 'brand-guideline-v3.pdf', file_size: 4_109_120, created_by: 2, creator_name: '林知夏', created_at: ago(120), updated_at: ago(29), review_status: 'rejected', publish_status: 'unpublished', publish_target_id: 3, publish_target_name: '综合管理部发布区', reject_reason: '请补充深色背景下的 Logo 使用示例，并更新文档版本号。' },
      { id: 103, title: '新员工信息安全培训', description: '入职必修的信息安全培训材料。', category: '培训材料', content_type: 'ppt', file_name: 'security-onboarding.pptx', file_size: 11_480_200, created_by: 2, creator_name: '林知夏', created_at: ago(350), updated_at: ago(190), submitted_at: ago(200), review_status: 'approved', publish_status: 'published', publish_target_id: 2, publish_target_name: '培训部发布区', published_at: ago(190), view_url: 'https://internal.example.com/presentation/security-onboarding/' },
      { id: 104, title: '客户案例素材包', description: '制造业客户案例图片与可公开使用素材。', category: '销售方案', content_type: 'file', file_name: 'case-assets.zip', file_size: 22_309_500, created_by: 2, creator_name: '林知夏', created_at: ago(14), updated_at: ago(12), review_status: 'draft', publish_status: 'unpublished', publish_target_id: 4, publish_target_name: '公共资料发布区' },
      { id: 105, title: '差旅费用报销制度', description: '适用于全体员工的差旅申请与费用报销标准。', category: '制度规范', content_type: 'pdf', file_name: 'travel-policy-2026.pdf', file_size: 1_804_300, created_by: 3, creator_name: '王启', created_at: ago(420), updated_at: ago(260), submitted_at: ago(270), review_status: 'approved', publish_status: 'published', publish_target_id: 3, publish_target_name: '综合管理部发布区', published_at: ago(260), view_url: 'https://internal.example.com/docs/travel-policy-2026/' },
      { id: 106, title: '区域销售数据模板', description: '区域团队月度销售数据填报模板。', category: '销售方案', content_type: 'excel', file_name: 'regional-sales.xlsx', file_size: 784_300, created_by: 3, creator_name: '王启', created_at: ago(180), updated_at: ago(90), submitted_at: ago(94), review_status: 'approved', publish_status: 'failed', publish_target_id: 3, publish_target_name: '综合管理部发布区', failure_reason: '转换服务暂时无法读取工作簿中的外部链接。' },
      { id: 107, title: '研发环境访问指南', description: '开发环境、测试环境和常见权限申请入口。', category: '制度规范', content_type: 'html', file_name: 'dev-access.html', file_size: 43_800, created_by: 1, creator_name: '系统管理员', created_at: ago(58), updated_at: ago(38), review_status: 'approved', publish_status: 'published', publish_target_id: 1, publish_target_name: '产品部发布区', published_at: ago(38), view_url: 'https://internal.example.com/site/dev-access/' },
      { id: 108, title: '月度运营播报', description: '八月重点运营数据与九月行动安排。', category: '产品资料', content_type: 'ppt', file_name: 'monthly-operations.pptx', file_size: 6_340_000, created_by: 3, creator_name: '王启', created_at: ago(31), updated_at: ago(7), submitted_at: ago(7), review_status: 'pending', publish_status: 'unpublished', publish_target_id: 2, publish_target_name: '培训部发布区' }
    ],
    reviews: [
      { id: 1, content_id: 101, action: 'submit', from_status: 'draft', to_status: 'pending', operated_by: 2, operator_name: '林知夏', comment: '提交发布审核', created_at: ago(4) },
      { id: 2, content_id: 102, action: 'submit', from_status: 'draft', to_status: 'pending', operated_by: 2, operator_name: '林知夏', comment: '提交发布审核', created_at: ago(31) },
      { id: 3, content_id: 102, action: 'reject', from_status: 'pending', to_status: 'rejected', operated_by: 1, operator_name: '系统管理员', comment: '请补充深色背景下的 Logo 使用示例，并更新文档版本号。', created_at: ago(29) },
      { id: 4, content_id: 108, action: 'submit', from_status: 'draft', to_status: 'pending', operated_by: 3, operator_name: '王启', comment: '提交发布审核', created_at: ago(7) }
    ],
    operationLogs: [
      { id: 1, created_at: ago(4), user_id: 2, user_name: '林知夏', action: '提交审核', object: '2026 秋季产品路线图', description: '提交《2026 秋季产品路线图》发布审核' },
      { id: 2, created_at: ago(7), user_id: 3, user_name: '王启', action: '提交审核', object: '月度运营播报', description: '提交《月度运营播报》发布审核' },
      { id: 3, created_at: ago(29), user_id: 1, user_name: '系统管理员', action: '审核驳回', object: '品牌视觉资产使用规范', description: '驳回《品牌视觉资产使用规范》' },
      { id: 4, created_at: ago(38), user_id: 1, user_name: '系统管理员', action: '发布内容', object: '研发环境访问指南', description: '发布《研发环境访问指南》' }
    ],
    publishLogs: [
      { id: 1, created_at: ago(38), content_id: 107, content_title: '研发环境访问指南', content_type: 'html', target_name: '产品部发布区', status: 'success', view_url: 'https://internal.example.com/site/dev-access/' },
      { id: 2, created_at: ago(90), content_id: 106, content_title: '区域销售数据模板', content_type: 'excel', target_name: '综合管理部发布区', status: 'failed', failure_reason: '转换服务暂时无法读取工作簿中的外部链接。' },
      { id: 3, created_at: ago(190), content_id: 103, content_title: '新员工信息安全培训', content_type: 'ppt', target_name: '培训部发布区', status: 'success', view_url: 'https://internal.example.com/presentation/security-onboarding/' },
      { id: 4, created_at: ago(260), content_id: 105, content_title: '差旅费用报销制度', content_type: 'pdf', target_name: '综合管理部发布区', status: 'success', view_url: 'https://internal.example.com/docs/travel-policy-2026/' }
    ]
  }
}

function load(): Database {
  const saved = localStorage.getItem(DB_KEY)
  if (!saved) {
    const db = initialDatabase()
    save(db)
    return db
  }
  try {
    const db = JSON.parse(saved) as Database
    let migrated = false
    if (!Array.isArray(db.departments)) {
      const names = [...new Set([
        ...db.users.map((user) => user.department),
        ...(Array.isArray(db.categories) ? db.categories.map((category) => category.department) : []),
      ].filter((name): name is string => Boolean(name)))]
      db.departments = names.map((name, index) => ({ id: index + 1, name, enabled: true, sort_order: (index + 1) * 10, created_at: now(), updated_at: now() }))
      migrated = true
    }
    if (!Array.isArray(db.categories)) {
      db.categories = initialDatabase().categories
      migrated = true
    }
    db.users.forEach((user) => { if (user.department === undefined) { user.department = null; migrated = true } })
    db.categories.forEach((category) => {
      if (category.visibility_scope === undefined) { category.visibility_scope = 'all'; migrated = true }
      if (category.department === undefined) { category.department = null; migrated = true }
    })
    if (migrated) save(db)
    return db
  } catch { return initialDatabase() }
}

function save(db: Database) { localStorage.setItem(DB_KEY, JSON.stringify(db)) }
function nextId(items: { id: number }[]) { return Math.max(0, ...items.map((item) => item.id)) + 1 }
function paginate<T>(items: T[], page = 1, pageSize = 10): PageResult<T> {
  const start = (page - 1) * pageSize
  return { items: items.slice(start, start + pageSize), total: items.length, page, page_size: pageSize }
}
function activeUser(db: Database): StoredUser {
  const id = Number(localStorage.getItem(SESSION_KEY))
  const user = db.users.find((item) => item.id === id && item.status === 'active')
  if (!user) throw new Error('登录状态已失效')
  return user
}
function publicUser(user: StoredUser): CurrentUser {
  const { password: _password, created_at: _createdAt, ...result } = user
  void _password; void _createdAt
  return result
}
function recordOperation(db: Database, action: string, object: string, description: string) {
  const user = activeUser(db)
  db.operationLogs.unshift({ id: nextId(db.operationLogs), created_at: now(), user_id: user.id, user_name: user.name, action, object: readableOperationObject(db, object), description })
}
function requireAdmin(db: Database) {
  if (activeUser(db).role !== 'admin') throw new Error('没有管理员权限')
}
function requireDepartment(db: Database, name?: string | null) {
  if (!name) return undefined
  const department = db.departments.find((item) => item.name.toLowerCase() === name.trim().toLowerCase())
  if (!department) throw new Error('所选部门不存在，请刷新部门列表')
  if (!department.enabled) throw new Error('所选部门已禁用，请重新选择')
  return department
}
function findContent(db: Database, id: number): ContentItem {
  const item = db.contents.find((content) => content.id === id)
  if (!item) throw new Error('内容不存在')
  const user = activeUser(db)
  if (user.role !== 'admin' && item.created_by !== user.id && (item.publish_status !== 'published' || !canViewPublished(db, item, user))) throw new Error('无权查看该内容')
  return item
}
function canViewPublished(db: Database, item: ContentItem, user: StoredUser) {
  if (user.role === 'admin' || item.created_by === user.id) return true
  const category = db.categories.find((entry) => entry.name === item.category)
  if (!category) return false
  if (category.visibility_scope === 'all') return true
  return category.visibility_scope === 'department' && Boolean(category.department && user.department && category.department.toLowerCase() === user.department.toLowerCase())
}
function targetName(db: Database, id?: number) { return db.targets.find((item) => item.id === id)?.name }
function readableOperationObject(db: Database, object: string) {
  const match = /^(用户|内容|发布目标|分类|部门) #(\d+)$/.exec(object)
  if (!match) return object
  const id = Number(match[2])
  if (match[1] === '用户') return db.users.find((item) => item.id === id)?.username || object
  if (match[1] === '内容') return db.contents.find((item) => item.id === id)?.title || object
  if (match[1] === '分类') return db.categories.find((item) => item.id === id)?.name || object
  if (match[1] === '部门') return db.departments.find((item) => item.id === id)?.name || object
  return db.targets.find((item) => item.id === id)?.name || object
}
function requireEnabledCategory(db: Database, name: string) {
  const category = db.categories.find((item) => item.name.toLowerCase() === name.trim().toLowerCase())
  if (!category) throw new Error('所选分类不存在，请刷新分类列表')
  if (!category.enabled) throw new Error('所选分类已禁用，请重新选择')
}
function mockDocumentContent(item: ContentItem) {
  if (item.content_type === 'ppt') return `<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0;padding:28px;background:#f4f5f1;font-family:Arial,"Microsoft YaHei",sans-serif;color:#222}.slide{position:relative;min-height:260px;margin:0 auto 24px;padding:48px;background:#fff;border:1px solid #ddd;box-shadow:0 8px 24px #2221}.slide h1{font-size:30px}.slide h2{color:#648f0e}.slide i{position:absolute;right:18px;bottom:14px;color:#81b119;font-style:normal}</style></head><body><section class="slide"><h1>本季度关键进展</h1><p>核心交付已按计划完成，下一阶段进入区域推广。</p><i>01</i></section><section class="slide"><h2>下一步行动</h2><ul><li>完成重点客户验证</li><li>同步交付材料与培训计划</li><li>按周复盘发布数据</li></ul><i>02</i></section></body></html>`
  if (item.content_type === 'excel') return `<!doctype html><html><head><meta charset="utf-8"><style>body{padding:28px;font-family:Arial,"Microsoft YaHei",sans-serif;color:#222}table{width:100%;border-collapse:collapse}caption{text-align:left;margin-bottom:12px;color:#648f0e;font-weight:700}th,td{padding:10px;border:1px solid #ddd;text-align:left}th{background:#f2f7e8}</style></head><body><table><caption>区域销售数据</caption><thead><tr><th>区域</th><th>目标</th><th>完成</th><th>完成率</th></tr></thead><tbody><tr><td>东部</td><td>120</td><td>116</td><td>96.7%</td></tr><tr><td>西部</td><td>90</td><td>94</td><td>104.4%</td></tr></tbody></table></body></html>`
  if (item.content_type === 'pdf' || item.content_type === 'word') return `<!doctype html><html><head><meta charset="utf-8"><style>body{max-width:760px;margin:0 auto;padding:42px;font-family:Arial,"Microsoft YaHei",sans-serif;color:#222;line-height:1.8}h1{font-size:25px;border-bottom:3px solid #81b119;padding-bottom:12px}h2{margin-top:28px;font-size:17px;color:#648f0e}</style></head><body><h1>制度正文</h1><h2>一、适用范围</h2><p>本制度适用于公司全体员工及相关业务活动。</p><h2>二、执行要求</h2><p>申请、审批与归档应在规定时限内完成，并保留必要凭证。</p><h2>三、生效与解释</h2><p>本制度自发布之日起执行，由相关职能部门负责解释。</p></body></html>`
  return item.content_body || '<!doctype html><html><body style="font-family:Arial,sans-serif;padding:32px"><main><h1>内部访问指南</h1><p>请根据所属环境选择对应入口，并按流程申请所需权限。</p><h2>访问步骤</h2><ol><li>确认所需环境与权限范围</li><li>提交访问申请</li><li>审批后使用公司账号登录</li></ol></main></body></html>'
}
function dateInRange(value: string, from?: string, to?: string) {
  if (from && value < from) return false
  if (to && value.slice(0, 10) > to) return false
  return true
}

export const mockDb = {
  async login(username: string, password: string) {
    await wait(420)
    const db = load()
    const user = db.users.find((item) => item.username === username && item.password === password)
    if (!user) throw new Error('用户名或密码错误')
    if (user.status === 'disabled') throw new Error('账号已禁用，请联系管理员')
    localStorage.setItem(SESSION_KEY, String(user.id))
    localStorage.setItem('publish-console-token', `mock-token-${user.id}`)
    recordOperation(db, '登录', `用户 #${user.id}`, '登录内容发布台')
    save(db)
    return { token: `mock-token-${user.id}`, user: publicUser(user) }
  },
  async logout() { await wait(100); localStorage.removeItem(SESSION_KEY); localStorage.removeItem('publish-console-token') },
  async me() { await wait(120); return publicUser(activeUser(load())) },

  async getUsers(query: UserQuery) {
    await wait(); const db = load(); requireAdmin(db)
    let items: User[] = db.users.map(({ password: _password, ...user }) => { void _password; return user })
    if (query.keyword) items = items.filter((item) => `${item.username}${item.name}${item.department || ''}`.toLowerCase().includes(query.keyword!.toLowerCase()))
    if (query.role) items = items.filter((item) => item.role === query.role)
    if (query.status) items = items.filter((item) => item.status === query.status)
    return paginate(items, query.page, query.page_size)
  },
  async getUser(id: number) { await wait(); const db = load(); requireAdmin(db); const { password: _password, ...user } = db.users.find((item) => item.id === id) ?? (() => { throw new Error('用户不存在') })(); void _password; return user },
  async createUser(payload: UserPayload) {
    await wait(); const db = load(); requireAdmin(db)
    if (db.users.some((item) => item.username === payload.username)) throw new Error('用户名已存在')
    const department = requireDepartment(db, payload.department)
    const user: StoredUser = { ...payload, department: department?.name || null, password: payload.password || 'demo123', id: nextId(db.users), created_at: now(), updated_at: now() }
    db.users.unshift(user); recordOperation(db, '新增用户', `用户 #${user.id}`, `新增用户 ${user.name}`); save(db)
    return this.getUser(user.id)
  },
  async updateUser(id: number, payload: UserPayload) {
    await wait(); const db = load(); requireAdmin(db); const user = db.users.find((item) => item.id === id)
    if (!user) throw new Error('用户不存在')
    const department = requireDepartment(db, payload.department)
    Object.assign(user, payload, { department: department?.name || null, password: payload.password || user.password }); recordOperation(db, '编辑用户', `用户 #${id}`, `更新用户 ${user.name}`); save(db)
    return this.getUser(id)
  },
  async updateUserStatus(id: number, status: UserStatus) {
    await wait(); const db = load(); requireAdmin(db); const user = db.users.find((item) => item.id === id)
    if (!user) throw new Error('用户不存在')
    if (user.id === activeUser(db).id && status === 'disabled') throw new Error('不能禁用当前登录账号')
    user.status = status; recordOperation(db, status === 'active' ? '启用用户' : '禁用用户', `用户 #${id}`, `${status === 'active' ? '启用' : '禁用'}用户 ${user.name}`); save(db); return true
  },
  async deleteUser(id: number) {
    await wait(); const db = load(); requireAdmin(db)
    if (id === activeUser(db).id) throw new Error('不能删除当前登录账号')
    if (db.contents.some((item) => item.created_by === id)) throw new Error('该用户已产生内容记录，无法删除，建议禁用账号')
    const user = db.users.find((item) => item.id === id); if (!user) throw new Error('用户不存在')
    db.users = db.users.filter((item) => item.id !== id); recordOperation(db, '删除用户', user.username, '删除未产生业务数据的用户'); save(db); return true
  },
  async getDepartments(includeDisabled = false): Promise<Department[]> {
    await wait(); const db = load(); const user = activeUser(db)
    return db.departments.filter((item) => user.role === 'admin' && includeDisabled ? true : item.enabled).sort((a, b) => a.sort_order - b.sort_order || a.id - b.id).map((item) => ({ ...item }))
  },
  async createDepartment(payload: DepartmentPayload): Promise<Department> {
    await wait(); const db = load(); requireAdmin(db)
    const name = payload.name.trim()
    if (db.departments.some((item) => item.name.toLowerCase() === name.toLowerCase())) throw new Error('部门名称已存在')
    const item: Department = { ...payload, name, id: nextId(db.departments), created_at: now(), updated_at: now() }
    db.departments.push(item); recordOperation(db, '新增部门', `部门 #${item.id}`, `新增部门 ${item.name}`); save(db); return { ...item }
  },
  async updateDepartment(id: number, payload: DepartmentPayload): Promise<Department> {
    await wait(); const db = load(); requireAdmin(db); const item = db.departments.find((department) => department.id === id)
    if (!item) throw new Error('部门不存在')
    const name = payload.name.trim()
    if (db.departments.some((department) => department.id !== id && department.name.toLowerCase() === name.toLowerCase())) throw new Error('部门名称已存在')
    if (item.name !== name) {
      db.users.forEach((user) => { if (user.department === item.name) user.department = name })
      db.categories.forEach((category) => { if (category.department === item.name) category.department = name })
    }
    Object.assign(item, payload, { name, updated_at: now() }); recordOperation(db, '编辑部门', `部门 #${id}`, `更新部门 ${item.name}`); save(db); return { ...item }
  },
  async updateDepartmentStatus(id: number, enabled: boolean): Promise<Department> {
    await wait(); const db = load(); requireAdmin(db); const item = db.departments.find((department) => department.id === id)
    if (!item) throw new Error('部门不存在')
    item.enabled = enabled; item.updated_at = now(); recordOperation(db, enabled ? '启用部门' : '禁用部门', `部门 #${id}`, `${enabled ? '启用' : '禁用'}部门 ${item.name}`); save(db); return { ...item }
  },
  async deleteDepartment(id: number) {
    await wait(); const db = load(); requireAdmin(db); const item = db.departments.find((department) => department.id === id)
    if (!item) throw new Error('部门不存在')
    if (db.users.some((user) => user.department === item.name) || db.categories.some((category) => category.department === item.name)) throw new Error('该部门已被用户或分类使用，请改为禁用')
    db.departments = db.departments.filter((department) => department.id !== id); recordOperation(db, '删除部门', item.name, `删除部门 ${item.name}`); save(db); return true
  },

  async getContents(query: ContentQuery) {
    await wait(); const db = load(); const user = activeUser(db)
    let items = user.role === 'admin' ? [...db.contents] : db.contents.filter((item) => item.created_by === user.id)
    if (query.keyword) items = items.filter((item) => `${item.title}${item.description}`.toLowerCase().includes(query.keyword!.toLowerCase()))
    if (query.content_type) items = items.filter((item) => item.content_type === query.content_type)
    if (query.category) items = items.filter((item) => item.category === query.category)
    if (query.review_status) items = items.filter((item) => item.review_status === query.review_status)
    if (query.publish_status) items = items.filter((item) => item.publish_status === query.publish_status)
    items.sort((a, b) => b.updated_at.localeCompare(a.updated_at))
    return paginate(items, query.page, query.page_size)
  },
  async getContent(id: number) { await wait(); return { ...findContent(load(), id) } },
  async createContent(payload: ContentPayload) {
    await wait(360); const db = load(); const user = activeUser(db)
    requireEnabledCategory(db, payload.category)
    const selected = payload.files || []
    const item: ContentItem = { id: nextId(db.contents), title: payload.title, description: payload.description, category: payload.category, content_type: payload.content_type, content_body: payload.content_body, file_name: selected.length === 1 ? selected[0].file.name : payload.file_name, file_size: selected.reduce((total, entry) => total + entry.file.size, 0) || payload.file_size, files: selected.map((entry) => ({ name: entry.file.name, relative_path: entry.relative_path, size: entry.file.size })), source_is_directory: selected.length > 1 || selected.some((entry) => entry.relative_path.includes('/')), created_by: user.id, creator_name: user.name, created_at: now(), updated_at: now(), review_status: 'draft', publish_status: 'unpublished', publish_target_id: payload.publish_target_id, publish_target_name: targetName(db, payload.publish_target_id) }
    db.contents.unshift(item); recordOperation(db, '新建内容', `内容 #${item.id}`, `新建《${item.title}》`); save(db); return item
  },
  async updateContent(id: number, payload: ContentPayload) {
    await wait(320); const db = load(); const item = findContent(db, id); const user = activeUser(db)
    if (user.role !== 'admin' && (item.created_by !== user.id || item.review_status === 'pending')) throw new Error('当前状态不允许编辑')
    requireEnabledCategory(db, payload.category)
    const selected = payload.files || []
    Object.assign(item, { title: payload.title, description: payload.description, category: payload.category, content_type: payload.content_type, content_body: payload.content_body, file_name: selected.length === 1 ? selected[0].file.name : payload.file_name || item.file_name, file_size: selected.length ? selected.reduce((total, entry) => total + entry.file.size, 0) : payload.file_size || item.file_size, files: selected.length ? selected.map((entry) => ({ name: entry.file.name, relative_path: entry.relative_path, size: entry.file.size })) : item.files, source_is_directory: selected.length ? selected.length > 1 || selected.some((entry) => entry.relative_path.includes('/')) : item.source_is_directory, publish_target_id: payload.publish_target_id, publish_target_name: targetName(db, payload.publish_target_id), updated_at: now() })
    recordOperation(db, '编辑内容', `内容 #${id}`, `更新《${item.title}》`); save(db); return item
  },
  async deleteContent(id: number) {
    await wait(); const db = load(); const item = findContent(db, id); const user = activeUser(db)
    if (user.role !== 'admin' && (item.created_by !== user.id || item.publish_status === 'published' || item.review_status === 'pending')) throw new Error('当前内容不可删除')
    db.contents = db.contents.filter((content) => content.id !== id); recordOperation(db, '删除内容', `内容 #${id}`, `删除《${item.title}》`); save(db); return true
  },
  async submitContent(id: number) {
    await wait(360); const db = load(); const item = findContent(db, id); const user = activeUser(db)
    if (user.role !== 'admin' && item.created_by !== user.id) throw new Error('只能提交自己的内容')
    if (!['draft', 'rejected'].includes(item.review_status)) throw new Error('当前状态不能提交审核')
    const fromStatus = item.review_status
    item.review_status = 'pending'; item.publish_status = 'unpublished'; item.submitted_at = now(); item.updated_at = now(); item.reject_reason = undefined
    db.reviews.unshift({ id: nextId(db.reviews), content_id: id, action: 'submit', from_status: fromStatus, to_status: 'pending', operated_by: user.id, operator_name: user.name, comment: '提交发布审核', created_at: now() })
    recordOperation(db, '提交审核', `内容 #${id}`, `提交《${item.title}》发布审核`); save(db); return item
  },
  async publishContent(id: number) { await wait(500); const db = load(); requireAdmin(db); const item = findContent(db, id); return publish(db, item, '管理员直接发布') },
  async republishContent(id: number) { await wait(520); const db = load(); requireAdmin(db); const item = findContent(db, id); if (item.publish_status !== 'failed') throw new Error('仅发布失败的内容可重新发布'); return publish(db, item, '重新发布') },

  async getCategories(includeDisabled = false): Promise<Category[]> {
    await wait(); const db = load(); const user = activeUser(db)
    return db.categories.filter((item) => user.role === 'admin' && includeDisabled ? true : item.enabled).sort((a, b) => a.sort_order - b.sort_order || a.id - b.id).map((item) => ({ ...item }))
  },
  async createCategory(payload: CategoryPayload): Promise<Category> {
    await wait(); const db = load(); requireAdmin(db)
    if (db.categories.some((item) => item.name.toLowerCase() === payload.name.trim().toLowerCase())) throw new Error('分类名称已存在')
    if (payload.visibility_scope === 'department' && !payload.department?.trim()) throw new Error('部门可见时必须选择所属部门')
    const department = payload.visibility_scope === 'department' ? requireDepartment(db, payload.department) : undefined
    const item: Category = { ...payload, name: payload.name.trim(), department: department?.name || null, id: nextId(db.categories), created_at: now(), updated_at: now() }
    db.categories.push(item); recordOperation(db, '新增分类', `分类 #${item.id}`, `新增分类 ${item.name}`); save(db); return { ...item }
  },
  async updateCategory(id: number, payload: CategoryPayload): Promise<Category> {
    await wait(); const db = load(); requireAdmin(db); const item = db.categories.find((category) => category.id === id)
    if (!item) throw new Error('分类不存在')
    const name = payload.name.trim()
    if (payload.visibility_scope === 'department' && !payload.department?.trim()) throw new Error('部门可见时必须选择所属部门')
    const department = payload.visibility_scope === 'department' ? requireDepartment(db, payload.department) : undefined
    if (db.categories.some((category) => category.id !== id && category.name.toLowerCase() === name.toLowerCase())) throw new Error('分类名称已存在')
    if (item.name !== name) db.contents.forEach((content) => { if (content.category === item.name) content.category = name })
    Object.assign(item, payload, { name, department: department?.name || null, updated_at: now() }); recordOperation(db, '编辑分类', `分类 #${id}`, `更新分类 ${item.name}`); save(db); return { ...item }
  },
  async updateCategoryStatus(id: number, enabled: boolean): Promise<Category> {
    await wait(); const db = load(); requireAdmin(db); const item = db.categories.find((category) => category.id === id)
    if (!item) throw new Error('分类不存在')
    item.enabled = enabled; item.updated_at = now(); recordOperation(db, enabled ? '启用分类' : '禁用分类', `分类 #${id}`, `${enabled ? '启用' : '禁用'}分类 ${item.name}`); save(db); return { ...item }
  },
  async deleteCategory(id: number) {
    await wait(); const db = load(); requireAdmin(db); const item = db.categories.find((category) => category.id === id)
    if (!item) throw new Error('分类不存在')
    if (db.contents.some((content) => content.category === item.name)) throw new Error('该分类已被内容使用，请改为禁用')
    db.categories = db.categories.filter((category) => category.id !== id); recordOperation(db, '删除分类', item.name, `删除分类 ${item.name}`); save(db); return true
  },

  async getTargets(): Promise<PublishTarget[]> {
    await wait(); const db = load(); const user = activeUser(db)
    return db.targets.filter((item) => user.role === 'admin' || item.enabled).map((item) => user.role === 'admin' ? { ...item } : { id: item.id, name: item.name, target_type: item.target_type, content_types: item.content_types, enabled: item.enabled, created_at: item.created_at })
  },
  async createTarget(payload: PublishTargetPayload) { await wait(); const db = load(); requireAdmin(db); const item = { ...payload, id: nextId(db.targets), created_at: now() }; db.targets.unshift(item); recordOperation(db, '新增发布配置', `发布目标 #${item.id}`, `新增 ${item.name}`); save(db); return item },
  async updateTarget(id: number, payload: PublishTargetPayload) { await wait(); const db = load(); requireAdmin(db); const item = db.targets.find((target) => target.id === id); if (!item) throw new Error('发布目标不存在'); Object.assign(item, payload); recordOperation(db, '编辑发布配置', `发布目标 #${id}`, `更新 ${item.name}`); save(db); return item },
  async updateTargetStatus(id: number, enabled: boolean) { await wait(); const db = load(); requireAdmin(db); const item = db.targets.find((target) => target.id === id); if (!item) throw new Error('发布目标不存在'); item.enabled = enabled; recordOperation(db, enabled ? '启用发布配置' : '禁用发布配置', `发布目标 #${id}`, `${enabled ? '启用' : '禁用'} ${item.name}`); save(db); return true },
  async deleteTarget(id: number) { await wait(); const db = load(); requireAdmin(db); if (db.contents.some((content) => content.publish_target_id === id)) throw new Error('该发布目标已被内容引用，无法删除，请改为禁用'); const target = db.targets.find((item) => item.id === id); if (!target) throw new Error('发布目标不存在'); db.targets = db.targets.filter((item) => item.id !== id); recordOperation(db, '删除发布配置', target.name, '删除发布目标'); save(db); return true },

  async getReviews(query: ReviewQuery) {
    await wait(); const db = load(); requireAdmin(db)
    let items = db.contents.filter((item) => item.review_status === (query.status || 'pending'))
    if (query.keyword) items = items.filter((item) => item.title.toLowerCase().includes(query.keyword!.toLowerCase()))
    if (query.content_type) items = items.filter((item) => item.content_type === query.content_type)
    if (query.category) items = items.filter((item) => item.category === query.category)
    if (query.submitted_by) items = items.filter((item) => item.creator_name.includes(query.submitted_by!))
    if (query.date_from || query.date_to) items = items.filter((item) => dateInRange(item.submitted_at || item.updated_at, query.date_from, query.date_to))
    return paginate(items.sort((a, b) => (b.submitted_at || '').localeCompare(a.submitted_at || '')), query.page, query.page_size)
  },
  async getReviewDetail(id: number): Promise<ReviewDetail> { await wait(); const db = load(); requireAdmin(db); const content = findContent(db, id); return { content: { ...content }, publish_target: db.targets.find((item) => item.id === content.publish_target_id) ?? null, history: db.reviews.filter((item) => item.content_id === id).sort((a, b) => b.created_at.localeCompare(a.created_at)) } },
  async approve(id: number, comment = '审核通过') { await wait(650); const db = load(); requireAdmin(db); const item = findContent(db, id); if (item.review_status !== 'pending') throw new Error('该内容当前不在待审核状态'); const operator = activeUser(db); item.review_status = 'approved'; db.reviews.unshift({ id: nextId(db.reviews), content_id: id, action: 'approve', from_status: 'pending', to_status: 'approved', operated_by: operator.id, operator_name: operator.name, comment, created_at: now() }); recordOperation(db, '审核通过', `内容 #${id}`, `通过《${item.title}》并触发发布`); return publish(db, item, '审核通过自动发布') },
  async reject(id: number, comment: string) { await wait(380); const db = load(); requireAdmin(db); const item = findContent(db, id); if (item.review_status !== 'pending') throw new Error('该内容当前不在待审核状态'); const operator = activeUser(db); item.review_status = 'rejected'; item.publish_status = 'unpublished'; item.reject_reason = comment; item.updated_at = now(); db.reviews.unshift({ id: nextId(db.reviews), content_id: id, action: 'reject', from_status: 'pending', to_status: 'rejected', operated_by: operator.id, operator_name: operator.name, comment, created_at: now() }); recordOperation(db, '审核驳回', `内容 #${id}`, `驳回《${item.title}》`); save(db); return item },

  async search(query: ContentQuery & { date_from?: string; date_to?: string }) { await wait(320); const db = load(); const user = activeUser(db); let items = db.contents.filter((item) => item.publish_status === 'published' && canViewPublished(db, item, user)); if (query.keyword) items = items.filter((item) => `${item.title}${item.description}`.toLowerCase().includes(query.keyword!.toLowerCase())); if (query.content_type) items = items.filter((item) => item.content_type === query.content_type); if (query.category) items = items.filter((item) => item.category === query.category); if (query.date_from || query.date_to) items = items.filter((item) => dateInRange(item.published_at || '', query.date_from, query.date_to)); return paginate(items.sort((a, b) => (b.published_at || '').localeCompare(a.published_at || '')), query.page, query.page_size) },
  async getOperationLogs(query: OperationLogQuery) { await wait(); const db = load(); requireAdmin(db); let items = db.operationLogs.map((item) => ({ ...item, object: readableOperationObject(db, item.object) })); if (query.user_id) items = items.filter((item) => item.user_id === query.user_id); if (query.action) items = items.filter((item) => item.action === query.action); if (query.date_from || query.date_to) items = items.filter((item) => dateInRange(item.created_at, query.date_from, query.date_to)); return paginate(items, query.page, query.page_size) },
  async getPublishLogs(query: PublishLogQuery) { await wait(); const db = load(); requireAdmin(db); let items = [...db.publishLogs]; if (query.keyword) items = items.filter((item) => item.content_title.toLowerCase().includes(query.keyword!.toLowerCase())); if (query.content_type) items = items.filter((item) => item.content_type === query.content_type); if (query.status) items = items.filter((item) => item.status === query.status); if (query.date_from || query.date_to) items = items.filter((item) => dateInRange(item.created_at, query.date_from, query.date_to)); return paginate(items, query.page, query.page_size) },
  async dashboard(): Promise<DashboardData> { await wait(300); const db = load(); const user = activeUser(db); const items = user.role === 'admin' ? db.contents : db.contents.filter((item) => item.created_by === user.id); return { ...(user.role === 'admin' ? { content_total: items.length, publish_failed: items.filter((item) => item.publish_status === 'failed').length } : { my_content_total: items.length, rejected: items.filter((item) => item.review_status === 'rejected').length }), pending_review: items.filter((item) => item.review_status === 'pending').length, published: items.filter((item) => item.publish_status === 'published').length, recent_submissions: [...items].sort((a, b) => b.updated_at.localeCompare(a.updated_at)).slice(0, 5), recent_publishes: items.filter((item) => item.publish_status === 'published').sort((a, b) => (b.published_at || '').localeCompare(a.published_at || '')).slice(0, 5) } },
  async preview(id: number) { await wait(); const item = findContent(load(), id); if (item.source_is_directory || (item.files?.length || 0) > 1) return { preview_type: 'files' as const, files: item.files || [] }; if (item.content_type === 'image') return { preview_type: 'image' as const, preview_url: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200' }; if (['html', 'dynamic', 'pdf', 'word', 'excel'].includes(item.content_type)) return { preview_type: 'text' as const, content: mockDocumentContent(item) }; if (item.file_name) return { preview_type: 'file' as const, file_name: item.file_name, file_size: item.file_size }; return { preview_type: 'unsupported' as const } },
  reset() { localStorage.removeItem(DB_KEY) }
}

function publish(db: Database, item: ContentItem, action: string) {
  const target = db.targets.find((targetItem) => targetItem.id === item.publish_target_id)
  if (!target?.enabled) throw new Error('发布目标不可用，请检查发布配置')
  item.review_status = 'approved'; item.publish_status = 'published'; item.published_at = now(); item.updated_at = now(); item.failure_reason = undefined
  const slug = `${item.id}-${item.content_type}`
  item.view_url = `${target.base_url || 'https://internal.example.com/content/'}${slug}/`
  db.publishLogs.unshift({ id: nextId(db.publishLogs), created_at: now(), content_id: item.id, content_title: item.title, content_type: item.content_type, target_name: target.name, status: 'success', view_url: item.view_url })
  recordOperation(db, action, `内容 #${item.id}`, `${action}《${item.title}》`); save(db); return { ...item }
}

export type { ContentType, PublishStatus }
