"""知微能碳 — 数据源管理 API"""
from fastapi import APIRouter, Query
from db import get_db, ok, err
from datetime import datetime

router = APIRouter(prefix="/api/datasource", tags=["数据源管理"])


@router.get("/list")
def list_datasources():
    """列出所有数据源"""
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='data_sources'")
    if not c.fetchone():
        return ok({"sources": []})
    rows = c.execute("SELECT * FROM data_sources ORDER BY id").fetchall()
    conn.close()
    return ok({"sources": [dict(r) for r in rows]})


@router.post("/create")
async def create_datasource(body: dict):
    """新增数据源"""
    conn = get_db(); c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS data_sources (id INTEGER PRIMARY KEY AUTOINCREMENT, source_name VARCHAR(100), source_type VARCHAR(50), config TEXT, status VARCHAR(20) DEFAULT 'active', last_data_at TIMESTAMP, remark TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    c.execute("INSERT INTO data_sources (source_name, source_type, config, status, remark) VALUES (?,?,?,?,?)",
              (body['source_name'], body.get('source_type', 'excel'),
               body.get('config', '{}'), body.get('status', 'active'),
               body.get('remark', '')))
    conn.commit(); conn.close()
    return ok({"id": c.lastrowid})


@router.delete("/{source_id}")
def delete_datasource(source_id: int):
    conn = get_db(); c = conn.cursor()
    c.execute("DELETE FROM data_sources WHERE id=?", (source_id,))
    conn.commit(); conn.close()
    return ok({"message": "已删除"})


@router.get("/logs")
def list_import_logs(page: int = 1, page_size: int = 20):
    """列出导入记录"""
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='import_logs'")
    if not c.fetchone():
        return ok({"total": 0, "items": []})
    total = c.execute("SELECT COUNT(*) FROM import_logs").fetchone()[0]
    rows = c.execute("SELECT * FROM import_logs ORDER BY imported_at DESC LIMIT ? OFFSET ?",
                     (page_size, (page - 1) * page_size)).fetchall()
    conn.close()
    return ok({"total": total, "page": page, "items": [dict(r) for r in rows]})
