"""知微能碳 — 碳资产 / 组织碳管理 / 系统管理 API"""
from fastapi import APIRouter, Query
from db import get_db, ok, err
from datetime import datetime, timedelta

T = datetime.now(); D1 = (T - timedelta(days=1)).strftime("%Y-%m-%d")

# ============ 碳资产 ============
asset_router = APIRouter(tags=["碳资产管理"])


@asset_router.get("/api/carbon_asset/quota")
def carbon_quota(year: int = 2026):
    conn = get_db(); c = conn.cursor()
    rows = c.execute("SELECT * FROM carbon_quotas WHERE year=? ORDER BY org_id", (year,)).fetchall()
    conn.close()
    items = []
    total_q = total_u = 0
    for r in rows:
        items.append({"org_id": r['org_id'],
                       "total_quota_ton": round(r['total_quota_ton'], 2),
                       "used_ton": round(r['used_ton'], 2),
                       "surplus_ton": round(r['total_quota_ton'] - r['used_ton'], 2)})
        total_q += r['total_quota_ton']; total_u += r['used_ton']
    return ok({"year": year, "total_quota_ton": round(total_q, 2), "total_used_ton": round(total_u, 2),
               "surplus_ton": round(total_q - total_u, 2), "details": items})


@asset_router.get("/api/carbon_asset/trading")
def carbon_trading():
    return ok({"current_price": 58.5, "unit": "元/吨CO2", "trend": [
        {"date": "2026-06-04", "price": 56.8}, {"date": "2026-06-05", "price": 57.3},
        {"date": "2026-06-06", "price": 58.1}, {"date": "2026-06-07", "price": 58.5},
        {"date": "2026-06-08", "price": 58.9}, {"date": "2026-06-09", "price": 59.2},
        {"date": "2026-06-10", "price": 58.5},
    ], "volume_today": 35000, "volume_unit": "吨"})


@asset_router.get("/api/carbon_asset/ccer")
def ccer_management():
    return ok({"projects": [
        {"name": "德耐尔光伏屋顶项目", "type": "可再生能源", "status": "已备案", "estimated_reduction_ton": 850, "progress": 75},
        {"name": "空压机余热回收", "type": "节能增效", "status": "开发中", "estimated_reduction_ton": 420, "progress": 40},
        {"name": "厂区绿化碳汇", "type": "碳汇", "status": "已核证", "estimated_reduction_ton": 180, "progress": 100},
    ]})


# ============ 组织碳管理 ============
org_router = APIRouter(tags=["组织碳管理"])


@org_router.get("/api/organization/tree")
def org_tree():
    conn = get_db(); c = conn.cursor()
    rows = c.execute("SELECT * FROM org_structure ORDER BY level, id").fetchall()
    conn.close()
    tree = []; cm = {}
    for r in rows:
        node = {"id": r['id'], "name": r['name'], "level": r['level'], "children": []}
        cm[r['id']] = node
        if r['parent_id'] is None:
            tree.append(node)
        elif r['parent_id'] in cm:
            cm[r['parent_id']]['children'].append(node)
    return ok({"tree": tree})


@org_router.get("/api/organization/carbon")
def org_carbon(org_id: int = 1):
    conn = get_db(); c = conn.cursor()
    row = c.execute("SELECT * FROM carbon_quotas WHERE org_id=?", (org_id,)).fetchone()
    conn.close()
    if not row:
        return err("组织不存在")
    return ok({"org_id": org_id, "year": row['year'], "total_quota_ton": row['total_quota_ton'],
               "used_ton": row['used_ton'], "per_unit_ton": round(row['used_ton'] / 365, 4)})


# ============ 系统管理 ============
sys_router = APIRouter(tags=["系统管理"])


@sys_router.get("/api/system/users")
def system_users():
    return ok({"users": [{"id": 1, "username": "admin", "role": "超级管理员", "created_at": "2026-01-01"},
                         {"id": 2, "username": "zhangwei", "role": "操作员", "created_at": "2026-03-15"},
                         {"id": 3, "username": "lihua", "role": "审核员", "created_at": "2026-04-01"}]})


@sys_router.get("/api/system/config")
def system_config():
    conn = get_db(); c = conn.cursor()
    rows = c.execute("SELECT * FROM system_config ORDER BY id").fetchall()
    conn.close()
    return ok({"configs": [dict(r) for r in rows]})


@sys_router.get("/api/system/logs")
def system_logs(page: int = 1, page_size: int = 20):
    conn = get_db(); c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM operation_logs").fetchone()[0]
    rows = c.execute("SELECT * FROM operation_logs ORDER BY created_at DESC LIMIT ? OFFSET ?",
                     (page_size, (page - 1) * page_size)).fetchall()
    conn.close()
    return ok({"total": total, "page": page, "items": [dict(r) for r in rows]})


@sys_router.get("/api/system/datasource")
@sys_router.get("/api/system/datasource/list")
def system_datasource():
    conn = get_db(); c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS data_sources (id INTEGER PRIMARY KEY AUTOINCREMENT, source_name VARCHAR(100), source_type VARCHAR(50), config TEXT, status VARCHAR(20) DEFAULT 'active', last_data_at TIMESTAMP, remark TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    rows = c.execute("SELECT * FROM data_sources ORDER BY id").fetchall()
    if not rows:
        # 插入演示数据
        demo = [('本地Excel导入','excel','{"path":"import_data/"}','active','手动上传Excel文件'),
                ('生产系统API','http','{"url":"http://mes/api/energy"}','active','自动从MES系统同步'),
                ('手工录入','manual','{}','active','临时手工录入数据')]
        for n, t, cg, s, r in demo:
            c.execute("INSERT INTO data_sources (source_name, source_type, config, status, remark) VALUES (?,?,?,?,?)", (n, t, cg, s, r))
        conn.commit()
        rows = c.execute("SELECT * FROM data_sources ORDER BY id").fetchall()
    conn.close()
    return ok({"sources": [dict(r) for r in rows]})


@sys_router.get("/api/system/peak_valley")
def peak_valley(date: str = Query(default=D1)):
    conn = get_db(); c = conn.cursor()
    rows = c.execute("""SELECT substr(timestamp,12,2) as h, AVG(total_active_power_kw) as avg,
        MAX(total_active_power_kw) as mx, MIN(total_active_power_kw) as mn
        FROM energy_records WHERE timestamp>=? AND timestamp<=? GROUP BY h ORDER BY h""",
                     (f"{date} 00:00:00", f"{date} 23:55:00")).fetchall()
    conn.close()
    hrs = [{"hour": f"{r['h']}:00", "avg_kw": round(r['avg'], 2), "max_kw": round(r['mx'], 2), "min_kw": round(r['mn'], 2)} for r in rows]
    peak = max(hrs, key=lambda x: x['avg_kw']) if hrs else {}
    valley = min(hrs, key=lambda x: x['avg_kw']) if hrs else {}
    return ok({"date": date, "hours": hrs, "peak": peak, "valley": valley})
