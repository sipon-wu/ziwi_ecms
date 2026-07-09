"""知微能碳 — 数据字典 API"""
from fastapi import APIRouter, Query
from db import get_db, ok, err

router = APIRouter(prefix="/api/dict", tags=["数据字典"])


@router.get("/types")
def get_dict_types():
    """获取所有字典类型"""
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='data_dict_types'")
    if not c.fetchone():
        return ok({"types": []})
    rows = c.execute("SELECT * FROM data_dict_types ORDER BY id").fetchall()
    conn.close()
    return ok({"types": [dict(r) for r in rows]})


@router.get("/items")
def get_dict_items(dict_code: str = Query(...)):
    """获取指定字典类型的条目"""
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='data_dict_types'")
    if not c.fetchone():
        return ok({"items": []})
    type_row = c.execute("SELECT id FROM data_dict_types WHERE dict_code=?", (dict_code,)).fetchone()
    if not type_row:
        conn.close()
        return ok({"items": []})
    rows = c.execute("SELECT * FROM data_dict_items WHERE dict_type_id=? AND enabled=1 ORDER BY sort_order", (type_row['id'],)).fetchall()
    conn.close()
    return ok({"items": [dict(r) for r in rows]})


@router.post("/types")
async def create_dict_type(body: dict):
    conn = get_db(); c = conn.cursor()
    # 自动建表
    c.execute("CREATE TABLE IF NOT EXISTS data_dict_types (id INTEGER PRIMARY KEY AUTOINCREMENT, dict_code VARCHAR(50) UNIQUE, dict_name VARCHAR(100), description TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    c.execute("CREATE TABLE IF NOT EXISTS data_dict_items (id INTEGER PRIMARY KEY AUTOINCREMENT, dict_type_id INTEGER, item_key VARCHAR(50), item_value VARCHAR(100), sort_order INTEGER DEFAULT 0, extra TEXT, enabled INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    c.execute("INSERT INTO data_dict_types (dict_code, dict_name, description) VALUES (?,?,?)",
              (body['dict_code'], body['dict_name'], body.get('description', '')))
    conn.commit(); conn.close()
    return ok({"id": c.lastrowid})


@router.post("/items")
async def create_dict_item(body: dict):
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT INTO data_dict_items (dict_type_id, item_key, item_value, sort_order) VALUES (?,?,?,?)",
              (body['dict_type_id'], body['item_key'], body['item_value'], body.get('sort_order', 0)))
    conn.commit(); conn.close()
    return ok({"id": c.lastrowid})


@router.delete("/items/{item_id}")
def delete_dict_item(item_id: int):
    conn = get_db(); c = conn.cursor()
    c.execute("DELETE FROM data_dict_items WHERE id=?", (item_id,))
    conn.commit(); conn.close()
    return ok({"message": "已删除"})
