"""知微能碳 — 驾驶舱 API"""
from fastapi import APIRouter, Query
from db import get_db, ok, CF
from datetime import datetime, timedelta

router = APIRouter(tags=["驾驶舱"])


@router.get("/api/dashboard/summary")
def dashboard_summary(date: str = Query(default=None)):
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    conn = get_db()
    c = conn.cursor()
    t = datetime.strptime(date, '%Y-%m-%d')
    y = (t - timedelta(days=1)).strftime('%Y-%m-%d')
    m_start = t.strftime('%Y-%m') + '-01'
    y_start = t.strftime('%Y') + '-01-01'

    today_kwh = c.execute(
        "SELECT SUM(total_energy_kwh) FROM energy_records WHERE timestamp>=? AND timestamp<=?",
        (f"{date} 00:00:00", f"{date} 23:55:00")).fetchone()[0] or 0
    yesterday_kwh = c.execute(
        "SELECT SUM(total_energy_kwh) FROM energy_records WHERE timestamp>=? AND timestamp<=?",
        (f"{y} 00:00:00", f"{y} 23:55:00")).fetchone()[0] or 0
    month_kwh = c.execute(
        "SELECT SUM(total_energy_kwh) FROM energy_records WHERE timestamp>=? AND timestamp<=?",
        (f"{m_start} 00:00:00", f"{date} 23:55:00")).fetchone()[0] or 0
    year_kwh = c.execute(
        "SELECT SUM(total_energy_kwh) FROM energy_records WHERE timestamp>=? AND timestamp<=?",
        (f"{y_start} 00:00:00", f"{date} 23:55:00")).fetchone()[0] or 0
    lm = (t.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
    last_month_kwh = c.execute(
        "SELECT SUM(total_energy_kwh) FROM energy_records WHERE timestamp>=? AND timestamp<=?",
        (f"{lm}-01 00:00:00", f"{lm}-{min(t.day,28):02d} 23:55:00")).fetchone()[0] or 0
    ly = t.year - 1
    last_year_kwh = c.execute(
        "SELECT SUM(total_energy_kwh) FROM energy_records WHERE timestamp>=? AND timestamp<=?",
        (f"{ly}-{t.month:02d}-01 00:00:00",
         f"{ly}-{t.month:02d}-{min(t.day,28):02d} 23:55:00")).fetchone()[0] or 0
    conn.close()

    carbon_today = round(today_kwh * CF, 2)
    return ok({
        "date": date,
        "today_kwh": round(today_kwh, 2), "yesterday_kwh": round(yesterday_kwh, 2),
        "month_kwh": round(month_kwh, 2), "year_kwh": round(year_kwh, 2),
        "last_month_kwh": round(last_month_kwh, 2), "last_year_kwh": round(last_year_kwh, 2),
        "today_vs_yesterday_pct": round((today_kwh - yesterday_kwh) / yesterday_kwh * 100, 2) if yesterday_kwh else 0,
        "month_vs_last_month_pct": round((month_kwh - last_month_kwh) / last_month_kwh * 100, 2) if last_month_kwh else 0,
        "year_vs_last_year_pct": round((year_kwh - last_year_kwh) / last_year_kwh * 100, 2) if last_year_kwh else 0,
        "carbon_emission_kg": carbon_today, "carbon_emission_ton": round(carbon_today / 1000, 4),
    })


@router.get("/api/dashboard/trend")
def dashboard_trend(date: str = Query(default=None)):
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    conn = get_db()
    c = conn.cursor()
    t = datetime.strptime(date, '%Y-%m-%d')
    y = (t - timedelta(days=1)).strftime('%Y-%m-%d')
    cur = c.execute(
        "SELECT timestamp,total_active_power_kw FROM energy_records WHERE timestamp>=? AND timestamp<=? ORDER BY timestamp",
        (f"{date} 00:00:00", f"{date} 23:55:00")).fetchall()
    yst = c.execute(
        "SELECT timestamp,total_active_power_kw FROM energy_records WHERE timestamp>=? AND timestamp<=? ORDER BY timestamp",
        (f"{y} 00:00:00", f"{y} 23:55:00")).fetchall()
    conn.close()
    ct, cp = [r['timestamp'].split(' ')[1][:5]
              for r in cur], [round(r['total_active_power_kw'], 2) for r in cur]
    yt, yp = [r['timestamp'].split(' ')[1][:5]
              for r in yst], [round(r['total_active_power_kw'], 2) for r in yst]
    pi, pv = max(enumerate(cp), key=lambda x: x[1]) if cp else (0, 0)
    return ok({"current_date": date, "yesterday_date": y, "current_timestamps": ct, "current_power": cp,
               "yesterday_timestamps": yt, "yesterday_power": yp,
               "peak": {"index": pi, "time": ct[pi] if ct else "", "value": round(pv, 2)}})


@router.get("/api/dashboard/ranking")
def dashboard_ranking(date: str = Query(default=None), limit: int = 10):
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    conn = get_db()
    c = conn.cursor()
    rows = c.execute("""SELECT wc.name as group_name, wc.rated_power, SUM(de.energy_kwh) as t, AVG(de.power_kw) as a
        FROM device_energy de
        JOIN devices d ON d.id = de.device_id
        JOIN work_centers wc ON wc.id = d.work_center_id
        WHERE de.timestamp>=? AND de.timestamp<=?
        GROUP BY wc.name ORDER BY t DESC LIMIT ?""",
                     (f"{date} 00:00:00", f"{date} 23:55:00", limit)).fetchall()
    total = sum(r['t'] for r in rows) if rows else 0
    conn.close()
    return ok({"date": date, "ranking": [{"device_name": r['group_name'],
                                           "group_name": r['group_name'],
                                           "rated_power_kw": r['rated_power'] or 0,
                                           "consumption_kwh": round(r['t'], 2),
                                           "avg_power_kw": round(r['a'], 2),
                                           "ratio_pct": round(r['t'] / total * 100, 1) if total else 0,
                                           "load_rate_pct": round(r['a'] / (r['rated_power'] or 132) * 100, 1) if r['rated_power'] else 0} for r in rows]})
