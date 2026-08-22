"""知微能碳管理系统 — 配置管理"""
import os

# 数据库
DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # sqlite / postgres
SQLITE_PATH = os.getenv("SQLITE_PATH", os.path.join(os.path.dirname(__file__), "energy_data.db"))
PG_DSN = os.getenv("PG_DSN", "postgresql://ecms:ecms@localhost:5432/ecms")

# JWT
SECRET_KEY = os.getenv("JWT_SECRET", "ziwi-ecms-dev-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# 默认系数
DEFAULT_CF = 0.5566  # kgCO2/kWh
DEFAULT_COAL = 0.1229  # kgce/kWh

# 默认管理员
DEFAULT_ADMIN = {"username": "admin", "password": os.getenv("DEFAULT_ADMIN_PASS", "admin123")}

# 知微云平台同步
PLATFORM_BASE_URL = os.getenv("PLATFORM_BASE_URL", "http://localhost:8000/api/v1")
SYNC_API_KEY = os.getenv("SYNC_API_KEY", "ziwi_dev_sync_key_please_change_in_production")

# 基于角色的访问控制（RBAC）
# 设为 False 可完全关闭（恢复无鉴权行为）；设为 True 后，READONLY_ROLES 中的角色
# 调用写接口（POST/PUT/PATCH/DELETE）将被拦截返回 403，仅保留读权限。
ENABLE_RBAC = os.getenv("ENABLE_RBAC", "true").lower() in ("1", "true", "yes", "on")
READONLY_ROLES = {"guest"}  # 只读角色集合
RBAC_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
# 写接口中允许匿名/访客调用的白名单（登录/登出/获取自身信息必须放行）
RBAC_EXEMPT_PATHS = {"/api/auth/login", "/api/auth/logout", "/api/auth/me"}

# 角色 → 权限集合（权限键与前端 auth-permissions.js 保持一致）
PERMISSION_KEYS = ["view_data", "edit_config", "export_report", "user_manage", "audit", "system_config"]
ROLE_PERMISSIONS = {
    "super_admin": set(PERMISSION_KEYS),
    "admin": set(PERMISSION_KEYS),
    "operator": {"view_data", "export_report"},
    "auditor": {"view_data", "audit", "export_report"},
    "guest": {"view_data"},
}
