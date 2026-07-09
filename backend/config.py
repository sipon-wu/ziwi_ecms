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
