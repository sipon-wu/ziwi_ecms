"""知微能碳 — 数据监控 API"""
from fastapi import APIRouter, Query
from db import get_db, ok

router = APIRouter(tags=["数据监控"])


@router.get("/api/monitoring/current")
def monitoring_current(view: str = "groups"):
    """实时数据监控
       view=groups: 按工作中心聚合设备组功率
       view=devices: 按单个设备显示
    """
    conn = get_db(); c = conn.cursor()
    latest = c.execute("SELECT MAX(timestamp) FROM energy_records").fetchone()[0]
    rec = c.execute("SELECT * FROM energy_records WHERE timestamp=? LIMIT 1", (latest,)).fetchone()
    if not rec:
        conn.close()
        return ok({"timestamp": latest, "total_active_power_kw": 0, "devices": [], "view": view})

    # 设备数据使用 device_energy 的最新时间
    de_latest = c.execute("SELECT MAX(timestamp) FROM device_energy").fetchone()[0] or latest

    if view == "groups":
        rows = c.execute("""SELECT wc.name, wc.rated_power,
            SUM(de.power_kw) as total_pw, AVG(de.power_kw) as avg_pw,
            AVG(de.power_factor) as avg_pf, SUM(de.current_a) as total_a
            FROM device_energy de
            JOIN devices d ON d.id = de.device_id
            JOIN work_centers wc ON wc.id = d.work_center_id
            WHERE de.timestamp=? GROUP BY wc.name ORDER BY total_pw DESC""",
                         (de_latest,)).fetchall()
        devices = [{"name": r['name'], "active_power_kw": round(r['total_pw'], 2),
                     "rated_power_kw": r['rated_power'] or 0,
                     "current_a": round(r['total_a'], 1),
                     "voltage_v": 380, "power_factor": round(r['avg_pf'], 3) if r['avg_pf'] else 0.92} for r in rows]
    else:
        rows = c.execute("SELECT * FROM device_energy WHERE timestamp=? ORDER BY power_kw DESC",
                         (de_latest,)).fetchall()
        devices = [{"name": d['device_name'], "active_power_kw": d['power_kw'],
                     "current_a": d['current_a'], "voltage_v": d['voltage_v'],
                     "power_factor": d['power_factor']} for d in rows]

    conn.close()
    return ok({
        "timestamp": latest,
        "total_active_power_kw": rec['total_active_power_kw'],
        "power_factor": rec['power_factor'],
        "view": view,
        "devices": devices
    })

@router.get("/api/monitoring/alarms")
def monitoring_alarms(status: str = "active", page: int = 1, page_size: int = 20):
    conn = get_db(); c = conn.cursor()
    where = "WHERE status=?" if status != "all" else ""
    params = (status,) if status != "all" else ()
    total = c.execute(f"SELECT COUNT(*) FROM alarms {where}", params).fetchone()[0]
    rows = c.execute(f"SELECT * FROM alarms {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                     params + (page_size, (page - 1) * page_size)).fetchall()
    conn.close()
    return ok({"total": total, "page": page, "items": [dict(r) for r in rows]})


@router.get("/api/monitoring/alarm_rules")
def get_alarm_rules():
    conn = get_db(); c = conn.cursor()
    rows = c.execute("SELECT * FROM alarm_rules ORDER BY id").fetchall()
    conn.close()
    return ok({"rules": [dict(r) for r in rows]})


@router.post("/api/monitoring/alarm_rules")
async def add_alarm_rule(body: dict):
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT INTO alarm_rules (device_group,metric,threshold,operator,level,message,enabled) VALUES (?,?,?,?,?,?,1)",
              (body['device_group'], body['metric'], body['threshold'],
               body.get('operator', 'gt'), body.get('level', 'warning'), body.get('message', '')))
    conn.commit()
    rid = c.lastrowid
    conn.close()
    return ok({"id": rid, "message": "规则已添加"})
