"""知微能碳 — 每日数据重置器
每晚0点执行：清除动态数据 → 重新生成种子数据 → 重新模拟

保留表（配置）：device_groups, work_centers, devices, emission_factors,
    alarm_rules, org_structure, system_config, suppliers, supplier_users
清除表（动态）：energy_records, device_energy, production_data, daily_energy,
    alarms, carbon_quotas, carbon_trade_prices, ccer_projects,
    optimization_tasks, supplier_carbon_data, operation_logs
"""
import sys, os, sqlite3, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "energy_data.db")
PYTHON = sys.executable

print("=" * 50)
print("知微能碳 — 每日数据重置")
print("=" * 50)

# 1. 清除动态数据
KEEP_TABLES = ['device_groups', 'work_centers', 'devices', 'emission_factors',
               'alarm_rules', 'org_structure', 'system_config',
               'suppliers', 'supplier_users', 'data_dict_types', 'data_dict_items']
CLEAR_TABLES = ['energy_records', 'device_energy', 'production_data',
                'daily_energy', 'alarms', 'carbon_quotas',
                'carbon_trade_prices', 'ccer_projects',
                'optimization_tasks', 'supplier_carbon_data',
                'operation_logs', 'energy_flow_config']

conn = sqlite3.connect(DB)
c = conn.cursor()
for t in CLEAR_TABLES:
    try:
        c.execute(f"DELETE FROM {t}")
        print(f"  CLEAR {t}")
    except Exception as e:
        print(f"  SKIP {t}: {e}")
conn.commit()
conn.close()
print("✅ 动态数据已清除")

# 2. 重新生成种子数据
print("\n📋 重新生成用例数据...")
subprocess.run([PYTHON, os.path.join(BASE, "generate_import_excel.py")],
               cwd=BASE, check=False)

# 3. 重新迁移设备
print("\n📋 重新迁移设备...")
subprocess.run([PYTHON, os.path.join(BASE, "migrate_devices.py")],
               cwd=BASE, check=False)

# 4. 重新模拟月度数据
print("\n📋 重新模拟月度数据...")
subprocess.run([
    PYTHON, os.path.join(BASE, "simulate_monthly.py"),
    "--electricity", "62550", "--water", "1000",
    "--diesel", "4500", "--gasoline", "100",
    "--month", "2026-05", "--mode", "new"
], cwd=BASE, check=False)
subprocess.run([
    PYTHON, os.path.join(BASE, "simulate_monthly.py"),
    "--electricity", "68000", "--water", "1000", "--diesel", "5000", "--gasoline", "100",
    "--month", "2026-06", "--mode", "new"
], cwd=BASE, check=False)

# 5. 补充当前日期数据（energy_records + device_energy）
import random
from datetime import datetime
random.seed(99)
today = datetime.now().strftime("%Y-%m-%d")
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# 5a. 能耗时序
for h in range(24):
    for m in range(0, 60, 5):
        ts = f"{today} {h:02d}:{m:02d}"
        if 8 <= h < 12: bp = 3200 + random.random() * 500
        elif 12 <= h < 13: bp = 2500 + random.random() * 300
        elif 13 <= h < 18: bp = 3400 + random.random() * 600
        elif 18 <= h < 22: bp = 2200 + random.random() * 400
        else: bp = 1800 + random.random() * 300
        p = round(bp + (random.random() - 0.5) * 200, 2)
        c.execute("INSERT INTO energy_records (timestamp,total_energy_kwh,total_active_power_kw,power_factor) VALUES (?,?,?,?)",
                  (ts, round(p * 5 / 60, 2), p, round(0.90 + random.random() * 0.08, 2)))

# 5b. 设备能耗（8-18点，按额定功率比例分摊）
devices = c.execute("SELECT id, device_code, rated_power FROM devices WHERE rated_power>0").fetchall()
if devices:
    for h in range(8, 18):
        for m in range(0, 60, 5):
            ts = f"{today} {h:02d}:{m:02d}"
            for d in devices:
                rp = d['rated_power'] or 50
                load = 0.4 + random.random() * 0.45
                pw = round(rp * load, 2)
                c.execute("INSERT INTO device_energy (timestamp,device_name,power_kw,energy_kwh,current_a,voltage_v,power_factor,device_id) VALUES (?,?,?,?,?,?,?,?)",
                          (ts, d['device_code'], pw, round(pw * 5 / 60, 2),
                           round(pw / (1.732 * 0.38 * 0.9), 1),
                           round(375 + random.random() * 10, 1),
                           round(0.85 + random.random() * 0.12, 2), d['id']))
    print(f"  → {len(devices)} 台设备 x 10h x 12点 = {len(devices)*10*12} 条")

# 5c. 生成报警记录（基于规则阈值检查 + 补充几条演示数据）
alarm_cnt = 0
rules = c.execute("SELECT * FROM alarm_rules").fetchall()
for rule in rules:
    metric = rule['metric']
    col_map = {'功率': 'power_kw', '电流': 'current_a'}
    col = col_map.get(metric, 'power_kw')
    row = c.execute(f"SELECT MAX({col}) as mv FROM device_energy de "
                    f"JOIN devices d ON d.id=de.device_id "
                    f"JOIN work_centers wc ON wc.id=d.work_center_id "
                    f"WHERE wc.name=?", (rule['device_group'],)).fetchone()
    if row and row['mv'] and row['mv'] > rule['threshold']:
        ts = f"{today} 0{8+alarm_cnt}:30:00"
        c.execute("INSERT INTO alarms (device_group, meter_name, alarm_level, alarm_msg, "
                  "current_value, threshold_value, status, created_at) "
                  "VALUES (?,?,?,?,?,?,?,?)",
                  (rule['device_group'], metric, rule['level'],
                   rule['message'], round(row['mv'], 2), rule['threshold'],
                   'active', ts))
        alarm_cnt += 1
# 补充几条演示报警（确保页面有数据展示）
demo_alarms = [
    ("001-喷油螺杆大机组", "功率", "warning", "功率接近满载", 238.5, 240, "resolved"),
    ("008-制氮制氧机组", "电流", "error", "电流异常升高", 295.3, 280, "active"),
    ("009-真空泵机组", "功率", "warning", "真空泵负载偏高", 43.8, 40, "active"),
    ("003-喷油螺杆小机组", "功率", "info", "设备维保到期提醒", 58.2, 60, "pending"),
    ("006-离心机组", "温度", "warning", "轴承温度偏高", 78.5, 75, "active"),
]
for dg, met, lvl, msg, cv, th, st in demo_alarms:
    ts = f"{today} {8+alarm_cnt:02d}:{55-alarm_cnt*6:02d}"
    c.execute("INSERT INTO alarms (device_group, meter_name, alarm_level, alarm_msg, "
              "current_value, threshold_value, status, created_at) "
              "VALUES (?,?,?,?,?,?,?,?)", (dg, met, lvl, msg, cv, th, st, ts))
    alarm_cnt += 1

# 5d. 碳预算超限报警（关联碳预算警告）
budget_row = c.execute("SELECT config_value FROM system_config WHERE config_key='carbon_budget_monthly'").fetchone()
budget = float(budget_row[0]) if budget_row else 350
month_co2 = c.execute("SELECT SUM(total_energy_kwh) FROM energy_records WHERE timestamp>=? AND timestamp<=?",
                      (f"{today[:7]}-01 00:00:00", f"{today[:7]}-28 23:55:00")).fetchone()[0] or 0
month_co2_ton = round(month_co2 * 0.5566 / 1000, 2)
budget_pct = round(month_co2_ton / budget * 100, 1)
if budget_pct > 80:
    ts = f"{today} 08:00:00"
    c.execute("INSERT INTO alarms (device_group, meter_name, alarm_level, alarm_msg, "
              "current_value, threshold_value, status, created_at) "
              "VALUES (?,?,?,?,?,?,?,?)",
              ("碳预算", "碳排放", "error" if budget_pct > 95 else "warning",
               f"月度碳预算使用率已达{budget_pct}%，请关注减排",
               month_co2_ton, budget, 'active', ts))
    alarm_cnt += 1
print(f"  → 生成 {alarm_cnt} 条报警记录")

conn.commit(); conn.close()
print(f"\n✅ 今日数据已补充 ({today})")
print("=" * 50)
print("🎉 数据重置完成")
