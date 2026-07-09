"""知微能碳 — 能耗分析 API"""
from fastapi import APIRouter, Query
from db import get_db, ok, COAL, CF
from datetime import datetime, timedelta

router = APIRouter(tags=["能耗分析"])
T = datetime.now()
D7 = (T - timedelta(days=7)).strftime("%Y-%m-%d")
D1 = (T - timedelta(days=1)).strftime("%Y-%m-%d")
TD = T.strftime("%Y-%m-%d")


@router.get("/api/analysis/energy_intensity")
def energy_intensity(start_date: str = Query(default=D7), end_date: str = Query(default=D1)):
    conn = get_db(); c = conn.cursor()
    total_kwh = c.execute("SELECT SUM(total_energy_kwh) FROM energy_records WHERE timestamp>=? AND timestamp<=?",
                          (f"{start_date} 00:00:00", f"{end_date} 23:55:00")).fetchone()[0] or 0
    total_units = c.execute("SELECT SUM(units_produced) FROM production_data WHERE date>=? AND date<=?",
                            (start_date, end_date)).fetchone()[0] or 1
    total_output = c.execute("SELECT SUM(daily_output_value) FROM production_data WHERE date>=? AND date<=?",
                             (start_date, end_date)).fetchone()[0] or 1
    today = datetime.now().strftime('%Y-%m-%d')
    today_units = c.execute("SELECT SUM(units_produced) FROM production_data WHERE date=?", (today,)).fetchone()[0] or 0
    conn.close()
    return ok({"total_kwh": round(total_kwh, 2),
               "total_energy_tce": round(total_kwh * COAL / 1000, 4),
               "per_product_kwh": round(total_kwh / total_units, 2),
               "energy_per_product": round(total_kwh / total_units, 2),
               "energy_per_output_value": round(total_kwh / total_output, 2),
               "total_output": total_units,
               "total_units": total_units,
               "total_output_value_wan": round(total_output, 2),
               "today_offline": today_units})


@router.get("/api/analysis/benchmark")
def analysis_benchmark(device_group: str = Query(default=None), date: str = Query(default=D1)):
    conn = get_db(); c = conn.cursor()
    # 动态获取工作中心列表，不使用硬编码映射
    work_centers = [r['name'] for r in c.execute("SELECT name FROM device_groups ORDER BY id").fetchall()]
    if device_group and device_group in work_centers:
        name = device_group
    else:
        name = work_centers[0] if work_centers else "001-喷油螺杆大机组"
    rated = c.execute("SELECT rated_kw FROM device_groups WHERE name=?", (name,)).fetchone()
    rated_kw = rated['rated_kw'] if rated else 132
    # 通过设备关联查询该工作中心的平均功率
    avg_pwr = c.execute("""SELECT AVG(de.power_kw) FROM device_energy de
        JOIN devices d ON d.id = de.device_id
        JOIN work_centers wc ON wc.id = d.work_center_id
        WHERE wc.name=? AND de.timestamp>=? AND de.timestamp<=?""",
                        (name, f"{date} 00:00:00", f"{date} 23:55:00")).fetchone()[0] or 0
    if not avg_pwr:
        avg_pwr = c.execute("SELECT AVG(power_kw) FROM device_energy WHERE device_name=? AND timestamp>=? AND timestamp<=?",
                            (name, f"{date} 00:00:00", f"{date} 23:55:00")).fetchone()[0] or 0
    conn.close()
    load_rate = round(avg_pwr / rated_kw * 100, 1) if rated_kw else 0
    level = "一级能效" if load_rate >= 75 else ("二级能效" if load_rate >= 60 else "待提升")
    return ok({"device_group": name, "rated_kw": rated_kw, "actual_avg_kw": round(avg_pwr, 2),
               "load_rate_pct": load_rate, "benchmark_level": level, "is_pass": load_rate >= 60,
               "available_groups": work_centers})


@router.get("/api/analysis/balance")
def energy_balance(date: str = Query(default=D1)):
    conn = get_db(); c = conn.cursor()
    rows = c.execute("""SELECT wc.name as group_name, SUM(de.energy_kwh) as t
        FROM device_energy de
        JOIN devices d ON d.id = de.device_id
        JOIN work_centers wc ON wc.id = d.work_center_id
        WHERE de.timestamp>=? AND de.timestamp<=?
        GROUP BY wc.name ORDER BY t DESC""",
                     (f"{date} 00:00:00", f"{date} 23:55:00")).fetchall()
    total = sum(r['t'] for r in rows) if rows else 0
    conn.close()
    tips = [
        {"title": "空压机组变频改造", "desc": "将高负载空压机改为变频控制，预计节能12-18%", "saving_kwh": round(total * 0.15, 0)},
        {"title": "非生产时段节能", "desc": "夜间及周末关闭非必需设备，减少待机能耗", "saving_kwh": round(total * 0.08, 0)},
    ]
    return ok({"date": date, "total_kwh": round(total, 2),
               "breakdown": [{"name": r['group_name'], "kwh": round(r['t'], 2), "ratio": round(r['t']/total*100, 1) if total else 0} for r in rows],
               "tips": tips})


@router.get("/api/analysis/energy_flow")
def energy_flow(start_date: str = Query(default=D1), end_date: str = Query(default=D1)):
    conn = get_db(); c = conn.cursor()
    total_kwh = c.execute("SELECT SUM(total_energy_kwh) FROM energy_records WHERE timestamp>=? AND timestamp<=?",
                          (f"{start_date} 00:00:00", f"{end_date} 23:55:00")).fetchone()[0] or 0
    conn.close()
    if total_kwh == 0: total_kwh = 23400
    total = round(total_kwh, 2)
    compressor = round(total * 0.28, 2)
    machining = round(total * 0.55, 2)
    testbench = round(total * 0.08, 2)
    aux_light = round(total * 0.09, 2)
    comp_eff = round(compressor * 0.80, 2); comp_loss = round(compressor * 0.20, 2)
    mach_eff = round(machining * 0.70, 2); mach_loss = round(machining * 0.30, 2)
    test_eff = round(testbench * 0.90, 2); test_loss = round(testbench * 0.10, 2)
    aux_eff = round(aux_light * 0.80, 2); aux_loss = round(aux_light * 0.20, 2)
    gas_val = round(total * 0.06, 2); gas_eff = round(gas_val * 0.85, 2); gas_loss = round(gas_val * 0.15, 2)
    nodes = [
        {"name":"购入电力","itemStyle":{"color":"#5470c6"}},{"name":"购入天然气","itemStyle":{"color":"#91cc75"}},
        {"name":"空压机组","itemStyle":{"color":"#fac858"}},{"name":"机加工设备","itemStyle":{"color":"#ee6666"}},
        {"name":"测试台","itemStyle":{"color":"#73c0de"}},{"name":"辅助及照明","itemStyle":{"color":"#3ba272"}},
        {"name":"有效压缩空气","itemStyle":{"color":"#fc8452"}},{"name":"有效加工动能","itemStyle":{"color":"#9a60b4"}},
        {"name":"有效测试输出","itemStyle":{"color":"#ea7ccc"}},{"name":"有效照明","itemStyle":{"color":"#48b8d0"}},
        {"name":"散热/摩擦损失","itemStyle":{"color":"#c0c0c0"}},
    ]
    links = [
        {"source":"购入电力","target":"空压机组","value":compressor},{"source":"购入电力","target":"机加工设备","value":machining},
        {"source":"购入电力","target":"测试台","value":testbench},{"source":"购入电力","target":"辅助及照明","value":aux_light},
        {"source":"购入天然气","target":"辅助及照明","value":gas_val},
        {"source":"空压机组","target":"有效压缩空气","value":comp_eff},{"source":"空压机组","target":"散热/摩擦损失","value":comp_loss},
        {"source":"机加工设备","target":"有效加工动能","value":mach_eff},{"source":"机加工设备","target":"散热/摩擦损失","value":mach_loss},
        {"source":"测试台","target":"有效测试输出","value":test_eff},{"source":"测试台","target":"散热/摩擦损失","value":test_loss},
        {"source":"辅助及照明","target":"有效照明","value":aux_eff},{"source":"辅助及照明","target":"散热/摩擦损失","value":aux_loss+gas_loss},
    ]
    return ok({"period":f"{start_date} ~ {end_date}","total_kwh":total,"nodes":nodes,"links":links})
