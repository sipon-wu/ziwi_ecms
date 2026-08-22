"""
知微能碳管理系统（AI版）V2.0 — FastAPI 入口
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from db import ok
from auth import decode_token
from config import ENABLE_RBAC, READONLY_ROLES, RBAC_WRITE_METHODS, RBAC_EXEMPT_PATHS

# ========== 创建应用 ==========
app = FastAPI(title="知微能碳管理系统（AI版）API", version="2.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ========== 全局异常处理 ==========
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("ecms")


@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc} | Path: {request.url.path}", exc_info=True)
    return JSONResponse(status_code=500, content={"code": 1, "message": "服务器内部错误"})


# ========== 请求日志中间件 ==========
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start = time.time()
    response = await call_next(request)
    cost = round((time.time() - start) * 1000, 1)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} [{cost}ms]")
    return response


# ========== RBAC 只读角色拦截中间件 ==========
# 仅对写方法生效；从 cookie 或 Authorization 头读取 JWT，判断角色是否在只读集合。
# 无 token / token 非法 时直接放行（保持原有"未鉴权"行为，不误伤匿名读）。
@app.middleware("http")
async def rbac_readonly_guard(request: Request, call_next):
    if ENABLE_RBAC and request.method in RBAC_WRITE_METHODS and request.url.path not in RBAC_EXEMPT_PATHS:
        token = request.cookies.get("token") or ""
        auth_header = request.headers.get("Authorization", "")
        if not token and auth_header.startswith("Bearer "):
            token = auth_header[7:]
        if token:
            try:
                payload = decode_token(token)
                if payload.get("role") in READONLY_ROLES:
                    return JSONResponse(
                        status_code=403,
                        content={"code": 403, "message": "当前账号为只读权限，无写入操作权限"},
                    )
            except Exception:  # 非法/过期 token：放行，交由后续逻辑处理
                pass
    return await call_next(request)


# ========== License 启动校验（阶段 B：软告警，不阻断运行） ==========
from license.verify import verify_license
try:
    _lic = verify_license()
    if _lic["valid"]:
        logger.info(f"License 校验通过: tenant={_lic['tenant_id']} exp={_lic['exp']}")
    else:
        logger.warning(f"License 未通过校验（软告警，不影响运行）: {_lic['error']}")
except Exception as e:  # noqa: BLE001 阶段 A 开启硬拦截后再改为 re-raise
    logger.error(f"License 硬校验失败: {e}")

# ========== 注册路由 ==========
from routers.dashboard import router as dashboard_router
from routers.monitoring import router as monitoring_router
from routers.analysis import router as analysis_router
from routers.efficiency import router as efficiency_router
from routers.carbon import router as carbon_router
from routers.system import asset_router, org_router, sys_router
from routers.bigscreen import router as bigscreen_router
from routers.heartbeat import router as heartbeat_router
from routers.import_api import router as import_router
from routers.auth_router import router as auth_router
from routers.dict_router import router as dict_router
from routers.supplier import router as supplier_router
from routers.datasource import router as datasource_router
from routers.device_mgmt import router as device_mgmt_router
from routers.license_router import router as license_router

app.include_router(dashboard_router)
app.include_router(monitoring_router)
app.include_router(analysis_router)
app.include_router(efficiency_router)
app.include_router(carbon_router)
app.include_router(asset_router)
app.include_router(org_router)
app.include_router(sys_router)
app.include_router(bigscreen_router)
app.include_router(heartbeat_router)
app.include_router(import_router)
app.include_router(auth_router)
app.include_router(dict_router)
app.include_router(supplier_router)
app.include_router(datasource_router)
app.include_router(device_mgmt_router)
app.include_router(license_router)


# ========== License 启动校验（阶段 B：软告警，不阻断、不误伤现有 demo） ==========
try:
    from license.verify import verify_license as _verify_license
    _lic = _verify_license()
    if not _lic["valid"]:
        logger.warning("License 未通过校验（软告警，不影响运行）: %s", _lic["error"])
    else:
        logger.info("License 校验通过: tenant=%s exp=%s", _lic["tenant_id"], _lic["exp"])
except Exception as _e:  # noqa: BLE001
    logger.error("License 校验异常: %s", _e)


@app.get("/")
def root():
    return {"service": "知微能碳管理系统（AI版）API", "version": "2.0.0", "status": "running"}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8088)
