"""知微能碳 — 系统心跳 API"""
from fastapi import APIRouter
from db import get_db
from datetime import datetime
import os

router = APIRouter(tags=["系统心跳"])
start_time = datetime.now()


@router.get("/api/heartbeat")
def heartbeat():
    conn = get_db()
    try:
        conn.execute("SELECT 1")
        db_status = "connected"
    except:
        db_status = "error"
    finally:
        conn.close()
    # 获取最新数据日期
    conn2 = get_db()
    c = conn2.cursor()
    last = c.execute("SELECT MAX(date(timestamp)) as d FROM energy_records").fetchone()
    data_date = last['d'] if last and last['d'] else "—"
    conn2.close()
    return {
        "code": 0,
        "data": {
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "uptime_seconds": int((datetime.now() - start_time).total_seconds()),
            "db_status": db_status,
            "data_date": data_date,
        }
    }
