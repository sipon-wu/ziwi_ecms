<template>
  <div class="app-wraper">
    <!-- 左侧菜单 #212529 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-logo">
        <img :src="logoUrl" alt="logo" class="logo-img" />
        <span v-show="!sidebarCollapsed" class="logo-title">知微能碳管理</span>
      </div>
      <nav class="sidebar-nav">
        <template v-for="menu in menuTree" :key="menu.id">
          <div class="nav-submenu">
            <div class="nav-item parent" :class="{ open: openMenus[menu.id] }" @click="toggleMenu(menu.id)">
              <svg v-if="menu.icon" class="nav-svg" width="18" height="18" viewBox="0 0 24 24" v-html="menu.icon"></svg>
              <span class="nav-label" v-show="!sidebarCollapsed">{{ menu.label }}</span>
              <svg class="nav-arrow" v-show="!sidebarCollapsed" viewBox="0 0 12 12"><path d="M3 4.5l3 3 3-3" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>
            </div>
            <router-link v-show="openMenus[menu.id]" v-for="child in menu.children" :key="child.id"
              :to="child.path" class="nav-item sub" :class="{ active: isActive(child.path) }" @click="addTab(child)">
              <span class="nav-label" v-show="!sidebarCollapsed">{{ child.label }}</span>
            </router-link>
          </div>
        </template>
      </nav>
      <div class="sidebar-footer" v-show="!sidebarCollapsed">
        <span>© 2026 知微  版权所有</span>
      </div>
    </aside>

    <!-- 右侧主体 -->
    <div class="main-area">
      <!-- 顶部栏：双行 -->
      <header class="top-bar">
        <div class="top-row-1">
          <div class="top-left">
            <span class="collapse-btn" @click="sidebarCollapsed=!sidebarCollapsed">
              <svg viewBox="0 0 20 16" width="18" height="14"><path d="M0 1h20M0 8h20M0 15h20" fill="none" stroke="#666" stroke-width="2"/></svg>
            </span>
            <span class="top-title">知微能碳管理系统</span>
          </div>
          <div class="top-right">
            <span class="top-icon" title="搜索">
              <svg viewBox="0 0 24 24" width="17" height="17"><circle cx="10" cy="10" r="7" fill="none" stroke="#666" stroke-width="1.8"/><line x1="15" y1="15" x2="21" y2="21" stroke="#666" stroke-width="1.8"/></svg>
            </span>
            <span class="top-icon msg" title="消息">
              <svg viewBox="0 0 24 24" width="17" height="17"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" fill="none" stroke="#666" stroke-width="1.8"/></svg>
              <span class="msg-badge" v-if="msgCount > 0">{{ msgCount > 99 ? '99+' : msgCount }}</span>
            </span>
            <span class="top-user">{{ currentUser }}</span>
            <span class="top-icon logout" title="退出" @click="logout" style="margin-left:4px">
              <svg viewBox="0 0 24 24" width="17" height="17"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" fill="none" stroke="#666" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </span>
          </div>
        </div>
        <div class="top-row-2">
          <!-- 页面标签 -->
          <div class="page-tabs">
            <span v-for="tab in openedTabs" :key="tab.path"
              class="page-tab" :class="{ active: tab.path === route.path }"
              @click="$router.push(tab.path)">
              <span>{{ tab.label }}</span>
              <span class="tab-close" v-if="openedTabs.length > 1" @click.stop="closeTab(tab)">×</span>
            </span>
          </div>
          <!-- 面包屑（第二行右侧） -->
          <div class="breadcrumb">
            <span v-for="(b,i) in breadcrumbs" :key="i">
              <router-link v-if="b.path && i < breadcrumbs.length-1" :to="b.path">{{ b.label }}</router-link>
              <span v-else>{{ b.label }}</span>
              <span v-if="i < breadcrumbs.length-1" class="sep"> / </span>
            </span>
          </div>
        </div>
      </header>
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
const logoUrl = import.meta.env.BASE_URL + 'ziwilogo.png'

const route = useRoute()
const router = useRouter()
const currentUser = ref('管理员')

onMounted(() => {
  try {
    const u = JSON.parse(localStorage.getItem('user') || '{}')
    if (u.real_name) currentUser.value = u.real_name
  } catch {}
})

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}
const sidebarCollapsed = ref(false)
const now = ref('')
const msgCount = ref(8)
let timer = null

// 页面标签
const openedTabs = reactive([])

function findMenuByPath(path) {
  for (const m of menuTree.value) {
    if (m.children) {
      for (const c of m.children) {
        if (c.path === path) return c
      }
    } else if (m.path === path) return m
  }
  return null
}

function addTab(item) {
  if (!item) return
  if (!openedTabs.find(t => t.path === item.path)) {
    openedTabs.push({ label: item.label, path: item.path })
  }
}

function closeTab(tab) {
  const idx = openedTabs.findIndex(t => t.path === tab.path)
  if (idx === -1 || openedTabs.length <= 1) return
  openedTabs.splice(idx, 1)
  if (tab.path === route.path) {
    const next = openedTabs[Math.min(idx, openedTabs.length - 1)]
    if (next) router.push(next.path)
  }
}

// 根据当前路由自动添加标签
function syncTabFromRoute() {
  const m = findMenuByPath(route.path)
  if (m) addTab(m)
}
watch(() => route.path, syncTabFromRoute)
onMounted(() => {
  syncTabFromRoute()
  // 确保默认展开当前所在菜单
  const path = route.path
  for (const m of menuTree.value) {
    if (m.children) {
      for (const c of m.children) {
        if (c.path === path) { openMenus[m.id] = true; return }
      }
    }
  }
})


// SVG 图标 —— 统一 24×24 viewBox
const userRole = ref('admin')
onMounted(() => {
  try {
    const u = JSON.parse(localStorage.getItem('user') || '{}')
    if (u.role) userRole.value = u.role
    if (u.real_name) currentUser.value = u.real_name
  } catch {}
})

const allMenuTree = [
  {
    id: 'dashboard', label: '首页',
    icon: '<rect x="3" y="3" width="18" height="18" rx="3" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M9 15V10M15 15V7" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
    children: [
      { id: 'dash_overview', path: '/dashboard', label: '驾驶舱概览' },
    ]
  },
  {
    id: 'energy_group', label: '用能概况',
    icon: '<rect x="3" y="3" width="7" height="8" rx="1" fill="none" stroke="currentColor" stroke-width="1.4"/><rect x="14" y="3" width="7" height="12" rx="1" fill="none" stroke="currentColor" stroke-width="1.4"/><rect x="3" y="14" width="7" height="7" rx="1" fill="none" stroke="currentColor" stroke-width="1.4"/><rect x="14" y="18" width="7" height="3" rx="1" fill="none" stroke="currentColor" stroke-width="1.4"/>',
    children: [
      { id: 'eg_overview', path: '/energy/overview', label: '企业总览' },
      { id: 'eg_structure', path: '/energy/structure', label: '用能结构' },
      { id: 'eg_trend', path: '/energy/trend', label: '能耗趋势' },
    ]
  },
  {
    id: 'monitoring', label: '数据监控',
    icon: '<circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="1.6"/><circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="1.2"/><line x1="12" y1="2" x2="12" y2="4" stroke="currentColor" stroke-width="1.5"/><line x1="12" y1="20" x2="12" y2="22" stroke="currentColor" stroke-width="1.5"/>',
    children: [
      { id: 'mon_real', path: '/monitoring/real', label: '实时数据' },
      { id: 'mon_device', path: '/monitoring/device', label: '设备监控' },
      { id: 'mon_alarms', path: '/monitoring/alarms', label: '报警管理' },
    ]
  },
  {
    id: 'analysis', label: '能耗分析',
    icon: '<rect x="3" y="4" width="18" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"/><line x1="3" y1="9" x2="21" y2="9" stroke="currentColor" stroke-width="1.2"/><line x1="12" y1="9" x2="12" y2="20" stroke="currentColor" stroke-width="1.2"/>',
    children: [
      { id: 'ana_consumption', path: '/analysis/consumption', label: '消费量及强度' },
      { id: 'ana_energy_flow', path: '/analysis/energy_flow', label: '能流分析' },
      { id: 'ana_benchmark', path: '/analysis/benchmark', label: '能效对标' },
      { id: 'ana_balance', path: '/analysis/balance', label: '能效平衡与优化' },
    ]
  },
  {
    id: 'efficiency', label: '能效管理',
    icon: '<rect x="5" y="4" width="14" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="1.6"/><line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="12" cy="15" r="1" fill="currentColor"/>',
    children: [
      { id: 'eff_analysis', path: '/efficiency/analysis', label: '能效分析' },
      { id: 'eff_level', path: '/efficiency/level', label: '能效水平总览' },
      { id: 'eff_tasks', path: '/efficiency/tasks', label: '优化任务管理' },
    ]
  },
  {
    id: 'carbon', label: '碳管理',
    icon: '<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.5"/><ellipse cx="12" cy="12" rx="4" ry="9" fill="none" stroke="currentColor" stroke-width="1"/><line x1="3" y1="12" x2="21" y2="12" stroke="currentColor" stroke-width="1"/>',
    children: [
      { id: 'carb_accounting', path: '/carbon/accounting', label: '碳排放核算' },
      { id: 'carb_footprint', path: '/carbon/footprint', label: '产品碳足迹' },
      { id: 'carb_supply', path: '/carbon/supply', label: '供应链碳管理' },
      { id: 'carb_budget', path: '/carbon/budget', label: '碳预算管理' },
      { id: 'carb_audit', path: '/carbon/audit', label: '碳核查支撑' },
    ]
  },
  {
    id: 'carbon_asset', label: '碳资产管理',
    icon: '<rect x="3" y="6" width="18" height="10" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"/><line x1="9" y1="3" x2="9" y2="19" stroke="currentColor" stroke-width="1"/><line x1="15" y1="3" x2="15" y2="19" stroke="currentColor" stroke-width="1"/><circle cx="12" cy="11" r="2" fill="currentColor" opacity="0.3"/>',
    children: [
      { id: 'ca_quota', path: '/carbon_asset/quota', label: '碳配额管理' },
      { id: 'ca_trading', path: '/carbon_asset/trading', label: '碳交易管理' },
      { id: 'ca_ccer', path: '/carbon_asset/ccer', label: 'CCER项目管理' },
    ]
  },
  {
    id: 'org', label: '组织碳管理',
    icon: '<rect x="3" y="5" width="8" height="7" rx="1" fill="none" stroke="currentColor" stroke-width="1.4"/><rect x="13" y="5" width="8" height="7" rx="1" fill="none" stroke="currentColor" stroke-width="1.4"/><rect x="8" y="14" width="8" height="7" rx="1" fill="none" stroke="currentColor" stroke-width="1.4"/>',
    children: [
      { id: 'org_tree', path: '/organization/tree', label: '组织架构' },
      { id: 'org_perm', path: '/organization/permission', label: '权限管理' },
      { id: 'org_suppliers', path: '/organization/suppliers', label: '供应商列表' },
    ]
  },
  {
    id: 'system', label: '系统管理',
    icon: '<circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="1.5"/><circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="1.2" stroke-dasharray="3 2"/>',
    children: [
      { id: 'sys_user', path: '/system/user', label: '用户管理' },
      { id: 'sys_config', path: '/system/config', label: '参数配置' },
      { id: 'sys_dict', path: '/system/dict', label: '数据字典' },
      { id: 'sys_datasource', path: '/system/datasource', label: '数据源管理' },
      { id: 'sys_import', path: '/system/import', label: '数据导入' },
      { id: 'sys_notify', path: '/system/notify', label: '通知配置' },
      { id: 'sys_logs', path: '/system/logs', label: '操作日志' },
    ]
  },
]

// 系统管理菜单仅对 super_admin 和 admin 角色显示
const menuTree = computed(() => {
  const excludeIds = ['super_admin', 'admin', 'guest'].includes(userRole.value) ? [] : ['system']
  return allMenuTree.filter(m => !excludeIds.includes(m.id))
})

// 手风琴展开
const openMenus = reactive({})
function toggleMenu(id) {
  const wasOpen = openMenus[id]
  for (const k in openMenus) delete openMenus[k]
  if (!wasOpen) openMenus[id] = true
}
function isActive(path) { return route.path === path }

const breadcrumbs = computed(() => {
  const path = route.path
  const result = [{ label: '首页', path: '/dashboard' }]
  for (const m of menuTree.value) {
    if (m.children) {
      for (const c of m.children) {
        if (c.path === path) { result.push({ label: m.label }); result.push({ label: c.label }); return result }
      }
    } else if (m.path === path) { result.push({ label: m.label }); return result }
  }
  return result
})

onMounted(() => { tick(); timer = setInterval(tick, 1000) })
onUnmounted(() => { if (timer) clearInterval(timer) })
function tick() { now.value = new Date().toLocaleString('zh-CN', { hour12: false }) }
</script>

<style scoped>
.app-wraper { display:flex; height:100vh; overflow:hidden }

/* ========== 侧边栏 #212529 ========== */
.sidebar {
  width: 200px; min-width:200px;
  background: #212529;
  display:flex; flex-direction:column;
  transition: width 0.25s ease;
  overflow:hidden;
}
.sidebar.collapsed { width: 50px; min-width: 50px; }

.sidebar-logo {
  display:flex; align-items:center; gap:10px;
  padding: 18px 14px; border-bottom: 1px solid rgba(255,255,255,0.06);
}
.logo-img { width: 28px; height: 28px; object-fit: contain; flex-shrink:0 }
.logo-title { font-size: 15px; font-weight: 600; white-space:nowrap; color:#e9ecef }

/* 导航容器 — block 布局，子元素自行控制对齐 */
.sidebar-nav { flex:1; overflow-y:auto; padding: 4px 0 }

/* 导航组 */
.nav-submenu { display:flex; flex-direction:column }

/* ---- 基础菜单项：block 级别 flex 行，内容全部紧左 ---- */
.nav-item,
.nav-item:link,
.nav-item:visited {
  display:flex; flex-direction:row; align-items:center; gap: 6px;
  width:100%;
  padding: 10px 8px 10px 18px;
  border-radius: 0;
  color: #adb5bd;
  text-decoration: none;
  font-size: 13px;
  line-height: 1.4;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
  user-select: none;
  border: none;
  background: transparent;
  box-sizing: border-box;
}
.nav-item:hover { background: rgba(255,255,255,0.04); color:#ced4da }
.nav-item.active { background: rgba(255,255,255,0.06); color:#e9ecef; font-weight:500 }

/* 有子菜单的父项 — 箭头推到最右 */
.nav-item.parent { padding-right: 12px; }

/* 二级子项 — 无图标，文字左边缘对齐一级文字（18+20+6=44px → padding-left:44px） */
.nav-item.sub {
  padding-left: 44px;
  color: #6c757d;
  font-size: 13px;
}
.nav-item.sub:hover { color:#adb5bd }
.nav-item.sub.active { color:#ced4da }

/* 折叠态 */
.collapsed .nav-item { padding: 10px 0; justify-content:center }
.collapsed .nav-item.sub { display:none }

/* 图标 */
.nav-svg { width: 20px; height: 20px; flex-shrink:0; color: #6c757d }
.nav-item:hover .nav-svg,
.nav-item.active .nav-svg { color: #adb5bd }

/* 展开箭头 */
.nav-arrow { width: 14px; height: 14px; flex-shrink:0; color: #6c757d; margin-left: auto; transition: transform 0.2s }
.nav-item.parent.open .nav-arrow { transform: rotate(180deg) }
.nav-submenu .nav-item.sub { animation:slideIn 0.2s ease }
@keyframes slideIn { from{opacity:0;transform:translateY(-4px)} to{opacity:1;transform:translateY(0)} }

/* 底部版权 — #444C53 居中 */
.sidebar-footer {
  padding: 10px 18px; font-size:11px; color: #444C53;
  border-top: 1px solid rgba(255,255,255,0.04);
  text-align: center;
  opacity: 0.7;
}
.sidebar-footer span { display:block }

/* ========== 主区域 ========== */
.main-area { flex:1; display:flex; flex-direction:column; overflow:hidden; background:#f0f2f5 }

/* ---- 顶部栏双行 ---- */
.top-bar {
  background:#fff; border-bottom:1px solid #e4e7ed; flex-shrink:0;
}
.top-row-1 {
  height: 44px; display:flex; align-items:center; justify-content:space-between;
  padding:0 18px;
}
.top-row-2 {
  height: 36px; display:flex; align-items:center; justify-content:space-between;
  padding:0 18px; border-top:1px solid #f0f0f0;
}

.top-left { display:flex; align-items:center; gap:12px }
.collapse-btn { cursor:pointer; color:#888; padding:2px 6px; border-radius:4px; display:flex; align-items:center }
.collapse-btn:hover { background:#f5f5f5; color:#555 }
.top-title { font-size:15px; font-weight:600; color:#212529 }

.top-right { display:flex; align-items:center; gap:18px }
.top-icon { cursor:pointer; padding:4px; border-radius:4px; position:relative; display:flex; align-items:center; color:#888 }
.top-icon:hover { background:#f5f5f5; color:#555 }
.top-icon.msg:hover .msg-badge { transform:scale(1.05) }
.msg-badge {
  position:absolute; top:-2px; right:-6px;
  background:#dc3545; color:#fff; font-size:10px; min-width:18px; height:16px;
  border-radius:8px; display:flex; align-items:center; justify-content:center;
  padding:0 4px; font-weight:600; transition:transform 0.15s;
}
.top-user { font-size:13px; color:#666 }

/* ---- 页面标签 ---- */
.page-tabs {
  display:flex; align-items:center; gap:2px; flex:1; overflow-x:auto;
}
.page-tabs::-webkit-scrollbar { height:2px }
.page-tab {
  position:relative;
  display:flex; align-items:center; gap:6px;
  padding:4px 22px 4px 12px; font-size:12px; color:#888;
  background:#f8f9fa; border:1px solid #e8eaed; border-radius:4px 4px 0 0;
  cursor:pointer; white-space:nowrap; user-select:none; transition:all 0.15s;
}
.page-tab:hover { background:#e9ecef; color:#555 }
.page-tab.active { background:#fff; color:#212529; font-weight:500; border-bottom-color:#fff }
.tab-close {
  position:absolute; top:1px; right:2px;
  font-size:11px; line-height:1; padding:1px 3px; border-radius:2px; color:#bbb;
}
.tab-close:hover { background:#dee2e6; color:#555 }

/* 面包屑 */
.breadcrumb { font-size:11px; color:#aaa; white-space:nowrap; flex-shrink:0 }
.breadcrumb a { color:#6c757d; text-decoration:none }
.breadcrumb a:hover { text-decoration:underline }
.breadcrumb .sep { color:#ddd; margin:0 3px }

.content { flex:1; overflow-y:auto; padding:16px 20px }
</style>
