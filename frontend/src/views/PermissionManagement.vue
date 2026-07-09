<template>
  <div class="page">
    <h2 class="page-title">权限管理</h2>

    <div class="section">
      <table>
        <thead>
          <tr>
            <th>角色</th>
            <th v-for="perm in permissions" :key="perm.key" style="text-align:center">{{ perm.label }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="role in roles" :key="role.name">
            <td>
              <span :class="['badge', roleBadgeClass(role.name)]">{{ role.name }}</span>
            </td>
            <td v-for="perm in permissions" :key="perm.key" style="text-align:center">
              <input
                type="checkbox"
                :checked="role.permissions.includes(perm.key)"
                @change="togglePermission(role, perm.key)"
                style="cursor:pointer"
              />
            </td>
          </tr>
        </tbody>
      </table>

      <div style="margin-top:16px; text-align:right">
        <button class="btn btn-primary" @click="savePermissions">保存权限</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const permissions = [
  { key: 'view_data', label: '查看数据' },
  { key: 'edit_config', label: '编辑配置' },
  { key: 'export_report', label: '导出报告' },
  { key: 'user_manage', label: '用户管理' },
  { key: 'audit', label: '审核' },
  { key: 'system_config', label: '系统配置' }
]

const roles = ref([
  {
    name: '超级管理员',
    permissions: ['view_data', 'edit_config', 'export_report', 'user_manage', 'audit', 'system_config']
  },
  {
    name: '操作员',
    permissions: ['view_data', 'export_report']
  },
  {
    name: '审核员',
    permissions: ['view_data', 'audit', 'export_report']
  }
])

function roleBadgeClass(name) {
  switch (name) {
    case '超级管理员': return 'badge-danger'
    case '操作员': return 'badge-info'
    case '审核员': return 'badge-warning'
    default: return 'badge-info'
  }
}

function togglePermission(role, permKey) {
  const idx = role.permissions.indexOf(permKey)
  if (idx > -1) {
    role.permissions.splice(idx, 1)
  } else {
    role.permissions.push(permKey)
  }
}

function savePermissions() {
  alert('权限配置已保存')
}
</script>

<style scoped>
.page { display:flex; flex-direction:column; gap:16px }
.page-title { font-size:18px; color:#333; margin:0 }
.section { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:20px }
.card { background:#fff; border:1px solid #e8eaed; border-radius:8px; padding:16px }
table { width:100%; border-collapse:collapse; font-size:13px }
th, td { padding:10px 14px; text-align:left; border-bottom:1px solid #f0f0f0 }
th { background:#f5f7fa; color:#666; font-weight:600 }
td { color:#333 }
.badge { padding:2px 8px; border-radius:4px; font-size:11px; font-weight:500 }
.badge-success { background:#e6f7f1; color:#00a870 }
.badge-warning { background:#fff3e0; color:#f57c00 }
.badge-danger { background:#ffebee; color:#d32f2f }
.badge-info { background:#e3f2fd; color:#1976d2 }
.btn { padding:6px 16px; border:none; border-radius:6px; cursor:pointer; font-size:12px }
.btn-primary { background:#0d7377; color:#fff }
.btn-danger { background:#d32f2f; color:#fff }
.btn:hover { opacity:0.8 }
.kpi-card { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:18px; text-align:center }
.kpi-card .kpi-label { font-size:12px; color:#999 }
.kpi-card .kpi-val { font-size:26px; font-weight:700; color:#333; margin:6px 0 }
.loading { text-align:center; padding:40px; color:#aaa }
</style>
