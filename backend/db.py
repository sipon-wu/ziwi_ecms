"""知微能碳管理系统 — 数据库连接管理"""
import sqlite3, os
from config import DB_TYPE, SQLITE_PATH

DB = SQLITE_PATH


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def ok(data=None, msg="success"):
    return {"code": 0, "message": msg, "data": data}


def err(msg="error"):
    return {"code": 1, "message": msg, "data": None}


# 常用常数
CF = 0.5566  # kgCO2/kWh
COAL = 0.1229  # kgce/kWh
