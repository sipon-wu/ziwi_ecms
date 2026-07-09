"""知微能碳 — 用户认证 API（本地登录 + JWT）"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from auth import hash_password, verify_password, create_token, decode_token
from db import ok, err
import os, json

router = APIRouter(prefix="/api/auth", tags=["用户认证"])

# 本地账号
DEFAULT_USER = {
    "username": "admin", "password_hash": hash_password(os.getenv("DEFAULT_ADMIN_PASS", "admin123")),
    "role": "super_admin", "real_name": "系统管理员",
}
GUEST_USER = {
    "username": "guest", "password_hash": hash_password(os.getenv("DEFAULT_GUEST_PASS", "123")),
    "role": "guest", "real_name": "访客用户",
}


@router.post("/login")
async def login(body: dict):
    username = body.get("username", "")
    password = body.get("password", "")
    if not username or not password:
        return err("用户名和密码不能为空")

    user = None
    if username == "admin" and verify_password(password, DEFAULT_USER["password_hash"]):
        user = DEFAULT_USER
    elif username == "guest" and verify_password(password, GUEST_USER["password_hash"]):
        user = GUEST_USER

    if user:
        token = create_token({
            "user_id": 1 if user == DEFAULT_USER else 2,
            "username": username, "role": user["role"], "real_name": user["real_name"],
        })
        resp = JSONResponse(content=ok({
            "token": token,
            "user": {"username": username, "role": user["role"], "real_name": user["real_name"]}
        }))
        resp.set_cookie(key="token", value=token, httponly=True, max_age=86400, samesite="lax")
        return resp
    return err("用户名或密码错误")


@router.get("/me")
async def get_me(request: Request):
    """获取当前登录用户信息（从Cookie或Header读取Token）"""
    token = request.cookies.get("token") or ""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    if not token:
        return JSONResponse(content={"code": 1, "message": "未登录"})
    try:
        payload = decode_token(token)
        return ok({
            "user_id": payload.get("user_id"),
            "username": payload.get("username"),
            "role": payload.get("role"),
            "real_name": payload.get("real_name"),
        })
    except HTTPException:
        return JSONResponse(content={"code": 1, "message": "Token 无效或已过期"})


@router.post("/logout")
async def logout():
    """退出登录"""
    resp = JSONResponse(content=ok({"message": "已退出"}))
    resp.delete_cookie("token")
    return resp
