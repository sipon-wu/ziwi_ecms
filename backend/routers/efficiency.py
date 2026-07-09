"""知微能碳 — 能效管理 API"""
from fastapi import APIRouter, Query
from db import get_db, ok

router = APIRouter(tags=["能效管理"])


@router.get("/api/efficiency/trend")
def efficiency_trend(device_group: str = None, days: int = 7):
    conn = get_db(); c = conn.cursor()
    # 使用工作中心名称直接查询
    if not device_group:
        row = c.execute("SELECT name FROM device_groups LIMIT 1").fetchone()
        device_group = row['name'] if row else "001-喷油螺杆大机组"
    # 查找工作中心对应的设备
    wc = c.execute("SELECT id, rated_power FROM work_centers WHERE name=?", (device_group,)).fetchone()
    if not wc:
        # 回退到 device_groups
        dg = c.execute("SELECT rated_kw FROM device_groups WHERE name=?", (device_group,)).fetchone()
        rated_kw = dg['rated_kw'] if dg else 132
    else:
        rated_kw = wc['rated_power'] or 132
    # 通过设备关联查询该工作中心下所有设备的能耗
    rows = c.execute("""SELECT date(de.timestamp) as d, AVG(de.power_kw) as avg_p, MAX(de.power_kw) as max_p
        FROM device_energy de
        JOIN devices d ON d.id = de.device_id
        JOIN work_centers wc ON wc.id = d.work_center_id
        WHERE wc.name=? GROUP BY d ORDER BY d DESC LIMIT ?""", (device_group, days)).fetchall()
    if not rows:
        # 回退: 按 device_name 直接查询
        rows = c.execute("""SELECT date(timestamp) as d, AVG(power_kw) as avg_p, MAX(power_kw) as max_p
            FROM device_energy WHERE device_name=? GROUP BY d ORDER BY d DESC LIMIT ?""", (device_group, days)).fetchall()
    conn.close()
    return ok({"device_group": device_group, "rated_kw": rated_kw,
               "trend": [{"date": r['d'], "avg_power_kw": round(r['avg_p'], 2),
                          "max_power_kw": round(r['max_p'], 2),
                          "efficiency_pct": round(r['avg_p'] / rated_kw * 100, 1) if rated_kw else 0} for r in reversed(rows)]})


@router.get("/api/efficiency/overview")
def efficiency_overview():
    conn = get_db(); c = conn.cursor()
    groups = c.execute("SELECT name, rated_kw FROM device_groups").fetchall()
    result = []
    for g in groups:
        latest = c.execute(
            "SELECT AVG(power_kw) as a FROM device_energy WHERE device_name=? AND timestamp>=datetime('now','localtime','-1 day')",
            (g['name'],)).fetchone()
        actual = round(latest['a'], 2) if latest and latest['a'] else 0
        load = round(actual / g['rated_kw'] * 100, 1) if g['rated_kw'] else 0
        level = "一级" if load >= 75 else ("二级" if load >= 60 else "三级")
        potential = round(g['rated_kw'] * 0.15 * 24 * 365 / 10000, 2)
        result.append({"name": g['name'], "rated_kw": g['rated_kw'], "actual_kw": actual,
                       "load_pct": load, "level": level, "potential_wan_kwh": potential})
    conn.close()
    return ok({"devices": result})


@router.get("/api/efficiency/optimization_tasks")
def optimization_tasks():
    conn = get_db(); c = conn.cursor()
    rows = c.execute("SELECT * FROM optimization_tasks ORDER BY status, id").fetchall()
    conn.close()
    return ok({"tasks": [dict(r) for r in rows]})
