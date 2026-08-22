// 角色 → 权限映射（与后端 config.py 中 ROLE_PERMISSIONS 保持一致）
// 权限键：view_data 查看数据 / edit_config 编辑配置 / export_report 导出报告
//        user_manage 用户管理 / audit 审核 / system_config 系统配置
export const ROLE_PERMISSIONS = {
  super_admin: ['view_data', 'edit_config', 'export_report', 'user_manage', 'audit', 'system_config'],
  admin:       ['view_data', 'edit_config', 'export_report', 'user_manage', 'audit', 'system_config'],
  operator:    ['view_data', 'export_report'],
  auditor:     ['view_data', 'audit', 'export_report'],
  guest:       ['view_data'],
}

export function hasPerm(role, perm) {
  return Array.isArray(ROLE_PERMISSIONS[role]) && ROLE_PERMISSIONS[role].includes(perm)
}
