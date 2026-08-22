"""知微能碳管理系统 — JWT 认证模块"""
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import bcrypt
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS, ROLE_PERMISSIONS

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(payload: dict) -> str:
    data = payload.copy()
    data["exp"] = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token 无效")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="未登录")
    return decode_token(credentials.credentials)


# 供前端未登录时返回统一格式
def unauthorized():
    raise HTTPException(status_code=401, detail="未登录")


def get_role_from_request(request: Request) -> str | None:
    """从 Cookie 或 Authorization 头中取出 JWT 并解析角色；无效/缺失返回 None。"""
    token = request.cookies.get("token") or ""
    auth_header = request.headers.get("Authorization", "")
    if not token and auth_header.startswith("Bearer "):
        token = auth_header[7:]
    if not token:
        return None
    try:
        return decode_token(token).get("role")
    except Exception:
        return None


def require_perm(perm: str):
    """依赖工厂：要求当前登录角色拥有指定权限，否则 401/403。供接口级鉴权使用。"""
    def checker(request: Request) -> str:
        role = get_role_from_request(request)
        if role is None:
            raise HTTPException(status_code=401, detail="未登录或登录已过期")
        if perm not in ROLE_PERMISSIONS.get(role, set()):
            raise HTTPException(status_code=403, detail=f"当前账号无[{perm}]权限")
        return role
    return checker
