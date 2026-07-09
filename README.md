# 知微能碳管理系统（ziwi-ecms）

空压机能碳管理 Demo 系统：FastAPI 后端 + Vue3/Vite 前端 + Nginx 反向代理，含能碳监测、分析、碳资产、能效、设备管理等模块。

> ⚠️ **安全说明**：本项目已做脱敏，服务器密码、IP、应用账号均通过环境变量注入（见 `.env.example`），**仓库内不含任何明文密钥**。请勿将真实 `.env` 提交到版本库。

## 目录结构
- `backend/` — FastAPI 服务（`main.py` + `routers/`），SQLite 演示库 `energy_data.db`（不入库，可经 seed 脚本重建）
- `frontend/` — Vue3 + Vite 前端（`npm install && npm run build` 产物在 `dist/`，不入库）
- `deploy/` — 部署/运维辅助脚本（已脱敏，依赖 `SERVER_HOST` / `SERVER_PASS` 环境变量）
- 根目录 `*.py` — 一次性检查/修复脚本（SSH 连接生产服务器，需配置环境变量）
- `运维纪要-云端部署与故障处理.md` — 部署 SOP 与故障处理（密码已脱敏为 `********`）

## 本地运行
```bash
# 后端
cd backend && pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8088

# 前端
cd frontend && npm install && npm run dev
```

## 环境变量
复制 `.env.example` 为 `.env` 并填入真实值：
- `SERVER_HOST` / `SERVER_PASS`：部署脚本连接生产服务器使用
- `DEFAULT_ADMIN_PASS` / `DEFAULT_GUEST_PASS`：覆盖默认账号密码（默认 admin/admin123、guest/123）
- `JWT_SECRET` / `PG_DSN` / `SYNC_API_KEY`：后端可选项

## 部署密钥（CI / 自动同步）
本仓库通过 SSH 部署密钥（写权限）推送到 GitHub，对应公钥已登记在目标仓库的 Deploy keys 中。本地推送使用 `~/.ssh/cloud_deploy_key`。
