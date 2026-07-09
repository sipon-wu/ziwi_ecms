"""
知微能碳管理系统（AI版）V2.0 — FastAPI 入口
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from db import ok

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


@app.get("/")
def root():
    return {"service": "知微能碳管理系统（AI版）API", "version": "2.0.0", "status": "running"}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8088)
