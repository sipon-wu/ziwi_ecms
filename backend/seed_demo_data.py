"""知微能碳 — 全面演示数据生成器
为所有页面填充真实感的演示数据，确保每个页面数据不为空
"""
import sqlite3, os, random, json
from datetime import datetime, timedelta

DB = os.path.join(os.path.dirname(__file__), "energy_data.db")
TODAY = datetime.now().strftime('%Y-%m-%d')
random.seed(42)

conn = sqlite3.connect(DB)
c = conn.cursor()

# 先清空动态数据，保留静态配置
tables = ['energy_records', 'device_energy', 'production_data', 'alarms']
for table in tables:
    try:
        c.execute(f"DELETE FROM {table}")
    except:
        pass
print("✅ 已清空动态数据")

# ========== 设备组（保留现有） ==========
groups = [
    ('双螺杆空压机组', 'production_unit', 132.0, '1号厂房A区'),
    ('数控螺杆转子铣床', 'production_unit', 55.0, '2号厂房B区'),
    ('数控车床/CNC加工中心', 'production_unit', 26.0, '2号厂房C区'),
    ('整机性能测试台', 'production_unit', 37.0, '3号厂房'),
    ('辅助设备（焊接/喷漆/照明）', 'production_unit', 22.0, '全厂'),
]

# ========== 能耗时序数据（近30天，5分钟间隔） ==========
print("生成能耗时序数据...")
# 工作日 vs 周末的功率基数
def base_power(hour, is_weekend):
    if is_weekend:
        return 1800 + random.random() * 300
    if 8 <= hour < 12: return 3200 + random.random() * 500
    if 12 <= hour < 13: return 2500 + random.random() * 300
    if 13 <= hour < 18: return 3400 + random.random() * 600
    if 18 <= hour < 22: return 2200 + random.random() * 400
    return 1800 + random.random() * 300

total_energy = 120000.0
count_er = 0

for day_offset in range(30, 0, -1):
    date = datetime.now() - timedelta(days=day_offset)
    is_weekend = date.weekday() >= 5
    for hour in range(24):
        for minute in range(0, 60, 5):
            ts = date.strftime('%Y-%m-%d') + f' {hour:02d}:{minute:02d}'
            bp = base_power(hour, is_weekend)
            total_p = round(bp + (random.random() - 0.5) * 200, 2)
            total_energy += total_p * 5 / 60
            # 各设备功率（按比例分配）
            compressor_p = round(total_p * 0.28, 2)
            milling_p = round(total_p * 0.35, 2)
            cnc_p = round(total_p * 0.20, 2)
            testbench_p = round(total_p * 0.08, 2)
            aux_p = round(total_p - compressor_p - milling_p - cnc_p - testbench_p, 2)
            pf = round(0.90 + random.random() * 0.08, 2)
            current = round(total_p / (1.732 * 0.38 * pf), 1)
            voltage = round(375 + random.random() * 10, 1)
            c.execute("""INSERT INTO energy_records (timestamp, total_active_power_kw, compressor_power_kw, milling_power_kw, cnc_power_kw, testbench_power_kw, aux_power_kw, total_energy_kwh, power_factor, phase_current_a, phase_voltage_v)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                      (ts, total_p, compressor_p, milling_p, cnc_p, testbench_p, aux_p, round(total_energy, 2), pf, current, voltage))
            count_er += 1
            if count_er % 5000 == 0: conn.commit()

conn.commit()
print(f"  ✅ 能耗时序数据: {count_er} 条 ({30}天×24h×12点)")

# ========== 设备能耗数据 ==========
print("生成设备能耗数据...")
count_de = 0
group_names = [g[0] for g in groups]
group_rated = {g[0]: g[2] for g in groups}

for day_offset in range(30, 0, -1):
    date = datetime.now() - timedelta(days=day_offset)
    is_weekend = date.weekday() >= 5
    for hour in range(8, 18):  # 工作时间 8:00-17:00
        if is_weekend and random.random() < 0.6:
            continue  # 周末部分设备停机
        for minute in range(0, 60, 5):
            ts = date.strftime('%Y-%m-%d') + f' {hour:02d}:{minute:02d}'
            for g_name in group_names:
                rated = group_rated[g_name]
                load = 0.5 + random.random() * 0.4 if not is_weekend else 0.2 + random.random() * 0.2
                power = round(rated * load, 2)
                energy = round(power * 5 / 60, 2)
                current = round(power / (1.732 * 0.38 * 0.9), 1)
                voltage = round(375 + random.random() * 10, 1)
                pf = round(0.85 + random.random() * 0.12, 2)
                c.execute("INSERT INTO device_energy (timestamp, device_name, power_kw, energy_kwh, current_a, voltage_v, power_factor) VALUES (?,?,?,?,?,?,?)",
                          (ts, g_name, power, energy, current, voltage, pf))
                count_de += 1
                if count_de % 5000 == 0: conn.commit()

conn.commit()
print(f"  ✅ 设备能耗数据: {count_de} 条")

# ========== 日产量数据（近30天） ==========
print("生成日产量数据...")
count_pd = 0
for day_offset in range(30, 0, -1):
    date = datetime.now() - timedelta(days=day_offset)
    is_weekend = date.weekday() >= 5
    if is_weekend and random.random() < 0.7:
        continue
    units = random.randint(80, 180)
    output = round(units * 0.3 + random.random() * 2, 2)
    c.execute("INSERT INTO production_data (date, units_produced, daily_output_value) VALUES (?,?,?)",
              (date.strftime('%Y-%m-%d'), units, output))
    count_pd += 1
conn.commit()
print(f"  ✅ 日产量数据: {count_pd} 条")

# ========== 报警数据 ==========
print("生成报警数据...")
count_al = 0
for day_offset in range(7, 0, -1):
    date = datetime.now() - timedelta(days=day_offset)
    for i in range(random.randint(1, 4)):
        hour = random.randint(8, 20)
        minute = random.randint(0, 59)
        ts = date.strftime('%Y-%m-%d') + f' {hour:02d}:{minute:02d}'
        g = random.choice(group_names)
        level = random.choice(['warning', 'warning', 'error'])
        metric = random.choice(['功率', '电流', '功率因数'])
        threshold = round(random.uniform(80, 150), 1)
        curr_val = round(threshold * (0.9 + random.random() * 0.2), 1)
        status = 'resolved' if day_offset > 2 else 'active'
        c.execute("INSERT INTO alarms (device_group, meter_name, alarm_level, alarm_msg, current_value, threshold_value, status, created_at) VALUES (?,?,?,?,?,?,?,?)",
                  (g, g + '-表', level, f'{metric}超限', curr_val, threshold, status, ts))
        count_al += 1
conn.commit()
print(f"  ✅ 报警数据: {count_al} 条")

# ========== 排放因子扩展 ==========
emission_factors_data = [
    ('电力排放因子', 0.5566, '2026'),
    ('天然气排放因子', 2.1600, '2026'),
    ('蒸汽排放因子', 276.0, '2026'),
    ('柴油排放因子', 2.6300, '2026'),
    ('汽油排放因子', 2.3000, '2026'),
    ('煤炭排放因子', 2060.0, '2026'),
]
c.execute("DELETE FROM emission_factors")
for ef in emission_factors_data:
    c.execute("INSERT INTO emission_factors (factor_type, value, effective_year) VALUES (?,?,?)", (ef[0], ef[1], ef[2]))
conn.commit()
print(f"  ✅ 排放因子: {len(emission_factors_data)} 条")

# ========== 碳配额 ==========
c.execute("DELETE FROM carbon_quotas")
for org_id in range(1, 4):
    for year in [2025, 2026]:
        quota = random.randint(8000, 25000)
        used = round(quota * (0.4 + random.random() * 0.4), 2)
        c.execute("INSERT INTO carbon_quotas (year, total_quota_ton, used_ton, org_id) VALUES (?,?,?,?)",
                  (year, quota, used, org_id))
conn.commit()
print(f"  ✅ 碳配额: 6 条")

# ========== 优化任务 ==========
tasks = [
    ('空压机群控优化', '双螺杆空压机组', 185000, '执行中'),
    ('CNC加工参数优化', '数控车床/CNC加工中心', 96000, '待执行'),
    ('车间照明LED改造', '辅助设备（焊接/喷漆/照明）', 42000, '已完成'),
    ('测试台待机管理', '整机性能测试台', 28000, '待执行'),
    ('空压机变频改造', '双螺杆空压机组', 150000, '执行中'),
    ('余热回收利用', '双螺杆空压机组', 220000, '待执行'),
]
c.execute("DELETE FROM optimization_tasks")
for t in tasks:
    c.execute("INSERT INTO optimization_tasks (title, suggestion, expected_saving_kwh, device_group, status) VALUES (?,?,?,?,?)",
              (t[0], f'{t[0]}方案', t[2], t[1], t[3]))
conn.commit()
print(f"  ✅ 优化任务: {len(tasks)} 条")

# ========== 供应商演示数据 ==========
suppliers_demo = [
    ('SHTEEL001', '上海XX钢材有限公司', '张三', '华东'),
    ('JSCAST002', '江苏YY精密铸造', '李四', '华东'),
    ('ZJMOTOR003', '浙江ZZ电机科技', '王五', '华东'),
    ('AHSEAL004', '安徽WW密封件', '赵六', '华东'),
    ('SDBEAR005', '山东BB轴承', '钱七', '华北'),
]
c.execute("CREATE TABLE IF NOT EXISTS suppliers (id INTEGER PRIMARY KEY AUTOINCREMENT, supplier_code VARCHAR(50) UNIQUE, supplier_name VARCHAR(200), contact_person VARCHAR(100), contact_email VARCHAR(200), contact_phone VARCHAR(50), carbon_score REAL DEFAULT 0, carbon_level VARCHAR(10), annual_co2_ton REAL DEFAULT 0, status VARCHAR(20) DEFAULT 'active', source VARCHAR(20) DEFAULT 'manual', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
c.execute("CREATE TABLE IF NOT EXISTS supplier_users (id INTEGER PRIMARY KEY AUTOINCREMENT, supplier_id INTEGER, username VARCHAR(100) UNIQUE, password_hash VARCHAR(128), api_key VARCHAR(64), must_change_password INTEGER DEFAULT 1, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
c.execute("CREATE TABLE IF NOT EXISTS supplier_carbon_data (id INTEGER PRIMARY KEY AUTOINCREMENT, supplier_code VARCHAR(50), supplier_id INTEGER, report_month DATE, production_units INTEGER DEFAULT 0, electricity_kwh REAL DEFAULT 0, natural_gas_m3 REAL DEFAULT 0, steam_ton REAL DEFAULT 0, water_ton REAL DEFAULT 0, diesel_l REAL DEFAULT 0, gasoline_l REAL DEFAULT 0, coal_ton REAL DEFAULT 0, compressed_air_m3 REAL DEFAULT 0, calculated_co2_kg REAL DEFAULT 0, carbon_score REAL DEFAULT 0, carbon_level VARCHAR(10), notes TEXT, data_source VARCHAR(20) DEFAULT 'excel', submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(supplier_code, report_month))")
c.execute("DELETE FROM suppliers"); c.execute("DELETE FROM supplier_users"); c.execute("DELETE FROM supplier_carbon_data")

from auth import hash_password
for code, name, contact, region in suppliers_demo:
    c.execute("INSERT INTO suppliers (supplier_code, supplier_name, contact_person) VALUES (?,?,?)",
              (code, name, contact))
    sid = c.lastrowid
    c.execute("INSERT INTO supplier_users (supplier_id, username, password_hash) VALUES (?,?,?)",
              (sid, f"sup_{sid}", hash_password("supplier123")))

# 供应商月度数据
for code, name, contact, region in suppliers_demo:
    for m in range(1, 6):  # 1-5月
        month_str = f"2026-{m:02d}"
        units = random.randint(8000, 20000)
        elec = round(random.uniform(80000, 180000), 2)
        gas = round(random.uniform(2000, 8000), 2)
        diesel = round(random.uniform(500, 5000), 2)
        co2 = round(elec * 0.5566 + gas * 2.16 + diesel * 2.63, 2)
        intensity = co2 / units
        score = max(0, min(100, round(100 - intensity * 0.5, 1)))
        level = 'A' if score >= 80 else ('B' if score >= 60 else ('C' if score >= 40 else 'D'))
        c.execute("""INSERT INTO supplier_carbon_data (supplier_code, report_month, production_units, electricity_kwh, natural_gas_m3, diesel_l, calculated_co2_kg, carbon_score, carbon_level, data_source)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
                  (code, month_str + '-01', units, elec, gas, diesel, round(co2, 2), score, level, 'excel'))

conn.commit()
print(f"  ✅ 供应商: {len(suppliers_demo)} 家, 月度数据: {len(suppliers_demo)*5} 条")

# ========== 系统配置 ==========
configs = [
    ('peak_start', '08:00', '峰时开始'),
    ('peak_end', '20:00', '峰时结束'),
    ('emission_factor', '0.5566', '电网排放因子 kgCO2/kWh'),
    ('carbon_budget_monthly', '180', '月度碳预算 吨'),
    ('refresh_interval', '10', '实时刷新间隔 秒'),
    ('page_size', '20', '默认分页大小'),
    ('alarm_retention_days', '90', '告警保留天数'),
]
c.execute("DELETE FROM system_config")
for k, v, desc in configs:
    c.execute("INSERT INTO system_config (config_key, config_value, description) VALUES (?,?,?)", (k, v, desc))
conn.commit()

conn.close()
print("\n" + "=" * 50)
print(f"🎉 演示数据生成完成！TODAY = {TODAY}")
print(f"   支持展示最近 30 天的完整数据")
