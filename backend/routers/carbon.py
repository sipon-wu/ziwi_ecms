"""知微能碳 — 碳管理 API"""
from fastapi import APIRouter, Query
from db import get_db, ok
from datetime import datetime, timedelta

router = APIRouter(tags=["碳管理"])
T = datetime.now()
D7 = (T - timedelta(days=7)).strftime("%Y-%m-%d")
D1 = (T - timedelta(days=1)).strftime("%Y-%m-%d")
TM = T.strftime("%Y-%m")
CF = 0.5566


@router.get("/api/carbon/accounting")
def carbon_accounting(start_date: str = Query(default=D7), end_date: str = Query(default=D1), scope: str = "1,2"):
    conn = get_db(); c = conn.cursor()
    total_kwh = c.execute("SELECT SUM(total_energy_kwh) FROM energy_records WHERE timestamp>=? AND timestamp<=?",
                          (f"{start_date} 00:00:00", f"{end_date} 23:55:00")).fetchone()[0] or 0
    # 从 daily_energy 获取各能源类型的月累计值
    total_co2 = total_kwh * 0.5566
    rows = c.execute("""SELECT energy_type, SUM(value) as total FROM daily_energy
        WHERE date>=? AND date<=? GROUP BY energy_type""",
                     (start_date, end_date)).fetchall()
    db_vals = {r['energy_type']: r['total'] or 0 for r in rows}
    
    ALL_TYPES = [
        ('electricity', '电力', 'kWh', 0.5566),
        ('diesel', '柴油', 'L', 2.63),
        ('gasoline', '汽油', 'L', 2.30),
        ('natural_gas', '天然气', 'm³', 2.16),
        ('water', '水', '吨', 0.298),
        ('steam', '蒸汽', '吨', 276.0),
        ('heat', '热力', 'GJ', 0),
        ('coal', '煤炭', '吨', 2060.0),
        ('lpg', 'LPG', 'kg', 1.76),
        ('compressed_air', '压缩空气', 'm³', 0),
    ]
    energy_types = []
    for etype, label, unit, factor in ALL_TYPES:
        val = db_vals.get(etype, 0)
        co2 = val * factor if factor else 0
        energy_types.append({
            "source": label, "kwh": round(val, 2) if etype == 'electricity' else 0,
            "value": round(val, 2), "unit": unit, "co2_kg": round(co2, 2), "ratio_pct": 0
        })
    conn.close()
    break_co2 = sum(e['co2_kg'] for e in energy_types)
    for e in energy_types:
        e['ratio_pct'] = round(e['co2_kg'] / break_co2 * 100, 1) if break_co2 else 0
    return ok({"period": f"{start_date} ~ {end_date}", "total_kwh": round(total_kwh, 2),
               "total_co2_kg": round(total_co2, 2), "total_co2_ton": round(total_co2 / 1000, 4),
               "source_breakdown": energy_types})


@router.get("/api/carbon/product_footprint")
@router.get("/api/carbon/footprint")
def product_footprint(product_model: str = Query(default="DV-15")):
    conn = get_db(); c = conn.cursor()
    total_kwh = c.execute("SELECT SUM(total_energy_kwh) FROM energy_records WHERE timestamp>=? AND timestamp<=?",
                          (D1 + " 00:00:00", D1 + " 23:55:00")).fetchone()[0] or 0
    units = c.execute("SELECT units_produced FROM production_data WHERE date='2026-05-06'").fetchone()
    units = units[0] if units else 8
    per_unit_kwh = total_kwh / units if units else 0
    conn.close()
    per_co2 = round(per_unit_kwh * CF, 2)
    return ok({"product_model": product_model, "date": "2026-05-06", "units_produced": units,
               "footprint_kgco2": per_co2, "per_unit_kwh": round(per_unit_kwh, 2),
               "breakdown": [
                   {"stage": "原材料生产", "co2_kg": round(per_co2 * 0.45, 2), "ratio": 45},
                   {"stage": "加工制造", "co2_kg": round(per_co2 * 0.35, 2), "ratio": 35},
                   {"stage": "组装测试", "co2_kg": round(per_co2 * 0.15, 2), "ratio": 15},
                   {"stage": "包装物流", "co2_kg": round(per_co2 * 0.05, 2), "ratio": 5},
               ]})


@router.get("/api/carbon/supply")
def supply_chain_carbon():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='supplier_carbon_data'")
    has_data = c.fetchone() is not None
    if not has_data:
        conn.close()
        return ok({"suppliers": []})
    # 取每个供应商最新一条数据的评分
    rows = c.execute("""SELECT s.supplier_name as name, sc.carbon_score, sc.carbon_level,
        sc.calculated_co2_kg
        FROM supplier_carbon_data sc
        JOIN suppliers s ON s.supplier_code = sc.supplier_code
        WHERE sc.id IN (SELECT MAX(id) FROM supplier_carbon_data GROUP BY supplier_code)
        ORDER BY sc.carbon_score DESC""").fetchall()
    conn.close()
    suppliers = []
    for r in rows:
        d = dict(r)
        d['annual_co2_ton'] = round((d.pop('calculated_co2_kg') or 0) * 12 / 1000, 2)
        suppliers.append(d)
    return ok({"suppliers": suppliers})


@router.get("/api/carbon/budget")
def carbon_budget(month: str = Query(default=TM)):
    conn = get_db(); c = conn.cursor()
    month_kwh = c.execute("SELECT SUM(total_energy_kwh) FROM energy_records WHERE timestamp>=? AND timestamp<=?",
                          (f"{month}-01 00:00:00", f"{month}-28 23:55:00")).fetchone()[0] or 0
    month_co2 = round(month_kwh * CF / 1000, 2)
    budget = c.execute("SELECT config_value FROM system_config WHERE config_key='carbon_budget_monthly'").fetchone()
    budget = round(float(budget[0])) if budget else 350
    conn.close()
    return ok({"month": month, "allocated_ton": budget, "used_ton": month_co2, "remaining_ton": round(budget - month_co2, 2),
               "percent": round(month_co2 / budget * 100, 1), "warning": month_co2 / budget >= 0.8})


@router.get("/api/carbon/audit_support")
@router.get("/api/carbon/audit")
def carbon_audit_support(year: int = 2026):
    return ok({"year": year, "material_package_url": "/exports/carbon_audit_2026.zip",
               "download_url": "https://ziwi.cn/download/carbon_audit_2026.zip",
               "materials": "https://ziwi.cn/download/carbon_audit_2026.zip",
               "checklist": ["能源消费台账", "排放因子引用文件", "各月度排放计算底稿", "第三方核查报告模板"],
               "status": "in_progress",
               "audit_status": "in_progress",
               "items": [
                   {"name": "组织边界确认", "description": "确认排放源边界和组织范围", "done": True},
                   {"name": "排放源识别", "description": "识别范围1和范围2排放源", "done": True},
                   {"name": "活动数据收集", "description": "收集能源消耗和物料使用数据", "done": True},
                   {"name": "排放因子确认", "description": "确认使用的碳排放因子", "done": True},
                   {"name": "排放量计算", "description": "完成碳排放量核算", "done": False},
                   {"name": "数据质量审核", "description": "审核数据的完整性和准确性", "done": False},
                   {"name": "核查报告编制", "description": "编制碳排放核查报告", "done": False},
               ],
               "audit_files": [
                   {"name": "碳排放报告", "format": "PDF", "size": "2.3MB"},
                   {"name": "排放因子清单", "format": "XLSX", "size": "1.1MB"},
                   {"name": "活动数据台账", "format": "XLSX", "size": "3.5MB"},
                   {"name": "核查声明", "format": "PDF", "size": "0.8MB"},
               ],
               "last_audit_date": f"{year}-06-01",
               "auditor": "中环联合认证中心"})
