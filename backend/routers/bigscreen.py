"""知微能碳 — 大屏看板 API（供独立看板服务器调用）"""
from fastapi import APIRouter, Query
from db import get_db, ok, CF
from datetime import datetime

router = APIRouter(prefix="/api/bigscreen", tags=["大屏看板"])


@router.get("/summary")
def bigscreen_summary(date: str = Query(default=None)):
    if not date: date = datetime.now().strftime('%Y-%m-%d')
    conn = get_db(); c = conn.cursor()
    t_kwh = c.execute("SELECT SUM(total_energy_kwh) FROM energy_records WHERE timestamp>=? AND timestamp<=?",
                      (f"{date} 00:00:00", f"{date} 23:55:00")).fetchone()[0] or 0
    y = (datetime.strptime(date, '%Y-%m-%d') - __import__('datetime').timedelta(days=1)).strftime('%Y-%m-%d')
    y_kwh = c.execute("SELECT SUM(total_energy_kwh) FROM energy_records WHERE timestamp>=? AND timestamp<=?",
                      (f"{y} 00:00:00", f"{y} 23:55:00")).fetchone()[0] or 0
    m_start = date[:7] + '-01'
    m_kwh = c.execute("SELECT SUM(total_energy_kwh) FROM energy_records WHERE timestamp>=? AND timestamp<=?",
                      (f"{m_start} 00:00:00", f"{date} 23:55:00")).fetchone()[0] or 0
    devices = c.execute("SELECT COUNT(DISTINCT device_name) as cnt FROM device_energy").fetchone()[0] or 0
    alarms = c.execute("SELECT COUNT(*) FROM alarms WHERE status='active'").fetchone()[0] or 0
    conn.close()
    return ok({"date": date, "today_kwh": round(t_kwh, 2), "yesterday_kwh": round(y_kwh, 2),
               "month_kwh": round(m_kwh, 2), "carbon_today_ton": round(t_kwh * CF / 1000, 2),
               "device_count": devices, "alarm_count": alarms})


@router.get("/energy_trend")
def bigscreen_trend(date: str = Query(default=None)):
    if not date: date = datetime.now().strftime('%Y-%m-%d')
    conn = get_db(); c = conn.cursor()
    rows = c.execute("""SELECT substr(timestamp,12,2) as h, AVG(total_active_power_kw) as avg
        FROM energy_records WHERE timestamp>=? AND timestamp<=? GROUP BY h ORDER BY h""",
                     (f"{date} 00:00:00", f"{date} 23:55:00")).fetchall()
    conn.close()
    hours = [{"hour": f"{r['h']}:00", "kw": round(r['avg'], 2)} for r in rows]
    peak = max(hours, key=lambda x: x['kw']) if hours else {}
    valley = min(hours, key=lambda x: x['kw']) if hours else {}
    return ok({"date": date, "hours": hours, "peak_kw": peak.get("kw",0), "peak_hour": peak.get("hour",""),
               "valley_kw": valley.get("kw",0), "valley_hour": valley.get("hour","")})


@router.get("/energy_structure")
def bigscreen_structure(date: str = Query(default=None)):
    if not date: date = datetime.now().strftime('%Y-%m-%d')
    conn = get_db(); c = conn.cursor()
    rows = c.execute("""SELECT device_name, SUM(energy_kwh) as t FROM device_energy
        WHERE timestamp>=? AND timestamp<=? GROUP BY device_name ORDER BY t DESC""",
                     (f"{date} 00:00:00", f"{date} 23:55:00")).fetchall()
    conn.close()
    total = sum(r['t'] for r in rows) or 1
    colors = ["#5470c6","#91cc75","#fac858","#ee6666","#73c0de","#3ba272","#fc8452","#9a60b4"]
    breakdown = [{"name": r['device_name'], "kwh": round(r['t'],2),
                  "ratio_pct": round(r['t']/total*100,1),
                  "color": colors[i%len(colors)]} for i,r in enumerate(rows)]
    return ok({"date": date, "total_kwh": round(sum(r['t'] for r in rows),2), "breakdown": breakdown})


@router.get("/carbon_overview")
def bigscreen_carbon(date: str = Query(default=None)):
    if not date: date = datetime.now().strftime('%Y-%m-%d')
    conn = get_db(); c = conn.cursor()
    t_kwh = c.execute("SELECT SUM(total_energy_kwh) FROM energy_records WHERE timestamp>=? AND timestamp<=?",
                      (f"{date} 00:00:00", f"{date} 23:55:00")).fetchone()[0] or 0
    m_start = date[:7] + '-01'
    m_kwh = c.execute("SELECT SUM(total_energy_kwh) FROM energy_records WHERE timestamp>=? AND timestamp<=?",
                      (f"{m_start} 00:00:00", f"{date} 23:55:00")).fetchone()[0] or 0
    conn.close()
    t_co2 = round(t_kwh * CF / 1000, 2)
    m_co2 = round(m_kwh * CF / 1000, 2)
    return ok({"date": date, "total_co2_ton": t_co2, "month_co2_ton": m_co2,
               "reduction_vs_yesterday_pct": 0,
               "budget_used_pct": round(m_co2 / 180 * 100, 1) if m_co2 else 0})


@router.get("/device_status")
def bigscreen_device_status():
    conn = get_db(); c = conn.cursor()
    names = c.execute("SELECT DISTINCT device_name FROM device_energy").fetchall()
    devices = []
    for n in names:
        r = c.execute("SELECT AVG(power_kw) as a FROM device_energy WHERE device_name=? AND timestamp>=datetime('now','localtime','-1 hour')",
                      (n['device_name'],)).fetchone()
        power = round(r['a'], 2) if r and r['a'] else 0
        status = "online" if power > 0 else "offline"
        devices.append({"name": n['device_name'], "status": status, "power_kw": power})
    conn.close()
    online = sum(1 for d in devices if d['status'] == 'online')
    return ok({"total": len(devices), "online": online, "offline": len(devices)-online, "devices": devices})


@router.get("/alarm_summary")
def bigscreen_alarm(date: str = Query(default=None)):
    if not date: date = datetime.now().strftime('%Y-%m-%d')
    conn = get_db(); c = conn.cursor()
    active = c.execute("SELECT COUNT(*) FROM alarms WHERE status='active'").fetchone()[0] or 0
    today_new = c.execute("SELECT COUNT(*) FROM alarms WHERE created_at>=?", (f"{date} 00:00:00",)).fetchone()[0] or 0
    recent = c.execute("SELECT * FROM alarms WHERE status='active' ORDER BY created_at DESC LIMIT 5").fetchall()
    conn.close()
    return ok({"date": date, "total_active": active, "today_new": today_new,
               "recent": [{"time": r['created_at'], "device": r['device_group'],
                           "message": r['alarm_msg']} for r in recent]})


@router.get("/ranking")
def bigscreen_ranking(date: str = Query(default=None), limit: int = 5):
    if not date: date = datetime.now().strftime('%Y-%m-%d')
    conn = get_db(); c = conn.cursor()
    rows = c.execute("""SELECT device_name, SUM(energy_kwh) as t FROM device_energy
        WHERE timestamp>=? AND timestamp<=? GROUP BY device_name ORDER BY t DESC LIMIT ?""",
                     (f"{date} 00:00:00", f"{date} 23:55:00", limit)).fetchall()
    total = sum(r['t'] for r in rows) or 1
    conn.close()
    return ok({"date": date, "ranking": [{"rank": i+1, "name": r['device_name'],
                                           "kwh": round(r['t'],2), "ratio": round(r['t']/total*100,1)}
                                          for i,r in enumerate(rows)]})
