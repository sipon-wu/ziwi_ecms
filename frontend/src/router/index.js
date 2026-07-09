import { createRouter, createWebHashHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import Login from '../views/Login.vue'

const routes = [
  {
    path: '/login', name: 'Login', component: Login,
    meta: { title: '登录', noAuth: true },
  },
  {
    path: '/', component: MainLayout, redirect: '/dashboard',
    children: [
      { path: '/dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '驾驶舱概览' } },
      { path: '/energy/overview', name: 'EnergyOverview', component: () => import('../views/EnergyOverview.vue'), meta: { title: '用能概况' } },
      { path: '/energy/structure', name: 'EnergyStructure', component: () => import('../views/EnergyStructure.vue'), meta: { title: '用能结构' } },
      { path: '/energy/trend', name: 'EnergyTrend', component: () => import('../views/EnergyTrend.vue'), meta: { title: '能耗趋势' } },
      { path: '/monitoring/real', name: 'RealTimeMonitor', component: () => import('../views/RealTimeMonitor.vue'), meta: { title: '实时数据' } },
      { path: '/monitoring/device', name: 'DeviceMonitor', component: () => import('../views/DeviceMonitor.vue'), meta: { title: '设备监控' } },
      { path: '/monitoring/alarms', name: 'AlarmManagement', component: () => import('../views/AlarmManagement.vue'), meta: { title: '报警管理' } },
      { path: '/analysis/consumption', name: 'ConsumptionAnalysis', component: () => import('../views/ConsumptionAnalysis.vue'), meta: { title: '消费量及强度' } },
      { path: '/analysis/benchmark', name: 'Benchmarking', component: () => import('../views/Benchmarking.vue'), meta: { title: '能效对标' } },
      { path: '/analysis/energy_flow', name: 'EnergyFlow', component: () => import('../views/EnergyFlow.vue'), meta: { title: '能流分析' } },
      { path: '/analysis/balance', name: 'EnergyBalance', component: () => import('../views/EnergyBalance.vue'), meta: { title: '能效平衡与优化' } },
      { path: '/efficiency/analysis', name: 'EfficiencyAnalysis', component: () => import('../views/EfficiencyAnalysis.vue'), meta: { title: '能效分析' } },
      { path: '/efficiency/level', name: 'EfficiencyLevel', component: () => import('../views/EfficiencyLevel.vue'), meta: { title: '能效水平总览' } },
      { path: '/efficiency/tasks', name: 'OptimizationTasks', component: () => import('../views/OptimizationTasks.vue'), meta: { title: '优化任务管理' } },
      { path: '/carbon/accounting', name: 'CarbonAccounting', component: () => import('../views/CarbonAccounting.vue'), meta: { title: '碳排放核算' } },
      { path: '/carbon/footprint', name: 'ProductFootprint', component: () => import('../views/ProductFootprint.vue'), meta: { title: '产品碳足迹' } },
      { path: '/carbon/supply', name: 'SupplyChainCarbon', component: () => import('../views/SupplyChainCarbon.vue'), meta: { title: '供应链碳管理' } },
      { path: '/carbon/budget', name: 'CarbonBudget', component: () => import('../views/CarbonBudget.vue'), meta: { title: '碳预算管理' } },
      { path: '/carbon/audit', name: 'CarbonAudit', component: () => import('../views/CarbonAudit.vue'), meta: { title: '碳核查支撑' } },
      { path: '/carbon_asset/quota', name: 'QuotaManagement', component: () => import('../views/QuotaManagement.vue'), meta: { title: '碳配额管理' } },
      { path: '/carbon_asset/trading', name: 'CarbonTrading', component: () => import('../views/CarbonTrading.vue'), meta: { title: '碳交易管理' } },
      { path: '/carbon_asset/ccer', name: 'CCERManagement', component: () => import('../views/CCERManagement.vue'), meta: { title: 'CCER项目管理' } },
      { path: '/organization/tree', name: 'OrganizationTree', component: () => import('../views/OrganizationTree.vue'), meta: { title: '组织架构' } },
      { path: '/organization/permission', name: 'PermissionManagement', component: () => import('../views/PermissionManagement.vue'), meta: { title: '权限管理' } },
      { path: '/organization/suppliers', name: 'SupplierManagement', component: () => import('../views/SupplierManagement.vue'), meta: { title: '供应商列表' } },
      { path: '/organization/suppliers/:id', name: 'SupplierDetail', component: () => import('../views/SupplierDetail.vue'), meta: { title: '导入数据详情' } },
      { path: '/system/user', name: 'UserManagement', component: () => import('../views/UserManagement.vue'), meta: { title: '用户管理' } },
      { path: '/system/config', name: 'SystemConfig', component: () => import('../views/SystemConfig.vue'), meta: { title: '参数配置' } },
      { path: '/system/logs', name: 'OperationLogs', component: () => import('../views/OperationLogs.vue'), meta: { title: '操作日志' } },
      { path: '/system/import', name: 'DataImport', component: () => import('../views/DataImport.vue'), meta: { title: '数据导入' } },
      { path: '/system/dict', name: 'DataDict', component: () => import('../views/DataDict.vue'), meta: { title: '数据字典' } },
      { path: '/system/datasource', name: 'DataSourceConfig', component: () => import('../views/DataSourceConfig.vue'), meta: { title: '数据源管理' } },
      { path: '/system/notify', name: 'NotifyConfig', component: () => import('../views/NotifyConfig.vue'), meta: { title: '通知配置' } },
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

// 路由守卫：未登录跳转登录页 + 系统管理仅admin
router.beforeEach(async (to, from, next) => {
  if (to.meta?.noAuth) { next(); return }
  const token = localStorage.getItem('token')
  let userRole = ''
  if (token) {
    try {
      const resp = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const d = await resp.json()
      if (d.code === 0) {
        userRole = d.data.role || ''
        // 缓存角色到 localStorage（供布局使用）
        const cached = JSON.parse(localStorage.getItem('user') || '{}')
        cached.role = userRole
        localStorage.setItem('user', JSON.stringify(cached))
        // 系统管理页面权限校验
        if (to.path.startsWith('/system/') && !['super_admin', 'admin', 'guest'].includes(userRole)) {
          next('/dashboard'); return
        }
        next(); return
      }
    } catch {}
  }
  next('/login')
})

export default router
