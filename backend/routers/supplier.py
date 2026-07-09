"""知微能碳 — 供应商管理 API"""
from fastapi import APIRouter, Query, UploadFile, File
from db import get_db, ok, err
from auth import hash_password
from data_import import import_excel, generate_template_excel
import tempfile, os, json

router = APIRouter(prefix="/api/admin/suppliers", tags=["供应商管理"])


@router.get("")
def list_suppliers(page: int = 1, page_size: int = 20):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='suppliers'")
    if not c.fetchone():
        conn.close()
        return ok({"total": 0, "page": page, "items": []})
    total = c.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0]
    # 检查 supplier_carbon_data 表是否存在
    has_data = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='supplier_carbon_data'").fetchone()
    if has_data:
        rows = c.execute("""SELECT s.*, sc.carbon_score, sc.carbon_level,
            (SELECT MAX(report_month) FROM supplier_carbon_data WHERE supplier_code=s.supplier_code) as last_submit
            FROM suppliers s
            LEFT JOIN supplier_carbon_data sc ON sc.id = (
                SELECT id FROM supplier_carbon_data WHERE supplier_code=s.supplier_code ORDER BY report_month DESC LIMIT 1
            )
            ORDER BY s.id LIMIT ? OFFSET ?""", (page_size, (page - 1) * page_size)).fetchall()
    else:
        rows = c.execute("SELECT *, NULL as carbon_score, NULL as carbon_level, NULL as last_submit FROM suppliers ORDER BY id LIMIT ? OFFSET ?",
                         (page_size, (page - 1) * page_size)).fetchall()
    conn.close()
    items = []
    for r in rows:
        d = dict(r)
        if d.get('last_submit'): d['last_submit'] = str(d['last_submit'])[:7]
        items.append(d)
    return ok({"total": total, "page": page, "items": items})


@router.post("")
async def create_supplier(body: dict):
    conn = get_db(); c = conn.cursor()
    _ensure_tables(c, conn)
    c.execute("INSERT INTO suppliers (supplier_code, supplier_name, contact_person, contact_email, contact_phone) VALUES (?,?,?,?,?)",
              (body['supplier_code'], body['supplier_name'],
               body.get('contact_person', ''), body.get('contact_email', ''),
               body.get('contact_phone', '')))
    sid = c.lastrowid
    # 自动创建供应商账号
    username = f"sup_{sid}"
    pwd = _gen_password()
    c.execute("INSERT INTO supplier_users (supplier_id, username, password_hash) VALUES (?,?,?)",
              (sid, username, hash_password(pwd)))
    conn.commit(); conn.close()
    return ok({"id": sid, "username": username, "password": pwd, "message": f"供应商已创建，账号：{username}"})


@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: int):
    conn = get_db(); c = conn.cursor()
    c.execute("DELETE FROM suppliers WHERE id=?", (supplier_id,))
    c.execute("DELETE FROM supplier_users WHERE supplier_id=?", (supplier_id,))
    c.execute("DELETE FROM supplier_carbon_data WHERE supplier_id=?", (supplier_id,))
    conn.commit(); conn.close()
    return ok({"message": "已删除"})


@router.post("/{supplier_id}/reset_password")
def reset_supplier_password(supplier_id: int):
    conn = get_db(); c = conn.cursor()
    pwd = _gen_password()
    c.execute("UPDATE supplier_users SET password_hash=? WHERE supplier_id=?", (hash_password(pwd), supplier_id))
    row = c.execute("SELECT username FROM supplier_users WHERE supplier_id=?", (supplier_id,)).fetchone()
    conn.commit(); conn.close()
    if not row:
        return err("供应商不存在")
    return ok({"username": row['username'], "password": pwd, "message": "密码已重置"})


@router.get("/{supplier_id}/data")
def get_supplier_data(supplier_id: int):
    """获取供应商能碳数据"""
    conn = get_db(); c = conn.cursor()
    # 先查供应商编码
    code_row = c.execute("SELECT supplier_code FROM suppliers WHERE id=?", (supplier_id,)).fetchone()
    if not code_row:
        conn.close()
        return ok({"items": []})
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='supplier_carbon_data'")
    if not c.fetchone():
        conn.close()
        return ok({"items": []})
    rows = c.execute("SELECT * FROM supplier_carbon_data WHERE supplier_code=? ORDER BY report_month DESC",
                     (code_row['supplier_code'],)).fetchall()
    conn.close()
    return ok({"items": [dict(r) for r in rows]})


@router.post("/import")
async def import_suppliers(file: UploadFile = File(...)):
    if not file.filename.endswith((".xlsx", ".xls")):
        return err("仅支持 .xlsx 格式")
    suffix = ".xlsx" if file.filename.endswith(".xlsx") else ".xls"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        result, error = import_excel(tmp_path, "suppliers")
        if error:
            return err(str(error))
        return ok(result)
    finally:
        try: os.unlink(tmp_path)
        except: pass


@router.get("/template")
def download_template():
    wb = generate_template_excel("suppliers")
    tmp_path = os.path.join(tempfile.gettempdir(), "template_suppliers.xlsx")
    wb.save(tmp_path)
    from fastapi.responses import FileResponse
    return FileResponse(tmp_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        filename="知微能碳-导入模板-供应商信息.xlsx")


def _ensure_tables(c, conn):
    c.execute("CREATE TABLE IF NOT EXISTS suppliers (id INTEGER PRIMARY KEY AUTOINCREMENT, supplier_code VARCHAR(50) UNIQUE, supplier_name VARCHAR(200), contact_person VARCHAR(100), contact_email VARCHAR(200), contact_phone VARCHAR(50), carbon_score REAL DEFAULT 0, carbon_level VARCHAR(10), annual_co2_ton REAL DEFAULT 0, status VARCHAR(20) DEFAULT 'active', source VARCHAR(20) DEFAULT 'manual', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    c.execute("CREATE TABLE IF NOT EXISTS supplier_users (id INTEGER PRIMARY KEY AUTOINCREMENT, supplier_id INTEGER, username VARCHAR(100) UNIQUE, password_hash VARCHAR(128), api_key VARCHAR(64), must_change_password INTEGER DEFAULT 1, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()


def _table_exists(c, name):
    return c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def _gen_password():
    import random, string
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return "GP@" + ''.join(random.choice(string.ascii_uppercase) for _ in range(6)) + ''.join(random.choice(string.digits) for _ in range(2))
