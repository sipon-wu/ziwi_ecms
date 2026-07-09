"""
知微能碳管理系统（AI版）V2.0 - 数据模拟器
德耐尔空压机制造工厂能耗 + 碳排放数据生成
"""
import sqlite3, os, numpy as np, json
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "energy_data.db")
CARBON_FACTOR = 0.5566  # kgCO2/kWh

DEVICE_GROUPS = [
    {"name": "双螺杆空压机组", "type": "动力设备", "count": 2, "rated_kw": 132, "ratio_pct": 28, "location": "1号厂房A区"},
    {"name": "数控螺杆转子铣床", "type": "机加工设备", "count": 4, "rated_kw": 55, "ratio_pct": 35, "location": "2号厂房B区"},
    {"name": "数控车床/CNC加工中心", "type": "机加工设备", "count": 8, "rated_kw": 26, "ratio_pct": 20, "location": "2号厂房C区"},
    {"name": "整机性能测试台", "type": "测试设备", "count": 2, "rated_kw": 37, "ratio_pct": 8, "location": "3号厂房"},
    {"name": "辅助设备（焊接/喷漆/照明）", "type": "工艺辅助", "count": 5, "rated_kw": 22, "ratio_pct": 9, "location": "全厂"},
]

# 组织架构
ORG_TREE = [
    {"id": 1, "name": "知微集团", "parent_id": None, "level": 0},
    {"id": 2, "name": "德耐尔工厂", "parent_id": 1, "level": 1},
    {"id": 3, "name": "1号厂房", "parent_id": 2, "level": 2},
    {"id": 4, "name": "2号厂房", "parent_id": 2, "level": 2},
    {"id": 5, "name": "3号厂房", "parent_id": 2, "level": 2},
    {"id": 6, "name": "4号总装车间", "parent_id": 2, "level": 2},
]

# 报警规则
ALARM_RULES = [
    {"device_group": "双螺杆空压机组", "metric": "active_power_kw", "threshold": 120, "operator": "gt", "level": "warning", "message": "空压机组功率超120kW"},
    {"device_group": "数控螺杆转子铣床", "metric": "active_power_kw", "threshold": 210, "operator": "gt", "level": "danger", "message": "铣床组功率超210kW"},
    {"device_group": "总功率", "metric": "active_power_kw", "threshold": 480, "operator": "gt", "level": "danger", "message": "全厂总有功功率超480kW"},
]


def init_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ---- 基础表 ----
    c.execute('''CREATE TABLE IF NOT EXISTS device_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, type TEXT NOT NULL,
        count INTEGER, rated_kw REAL, ratio_pct REAL, location TEXT DEFAULT ''
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS energy_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
        total_active_power_kw REAL, compressor_power_kw REAL, milling_power_kw REAL,
        cnc_power_kw REAL, testbench_power_kw REAL, aux_power_kw REAL,
        total_energy_kwh REAL, power_factor REAL DEFAULT 0.92,
        phase_current_a REAL DEFAULT 0, phase_voltage_v REAL DEFAULT 380
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS device_energy (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
        device_name TEXT NOT NULL, power_kw REAL, energy_kwh REAL,
        current_a REAL DEFAULT 0, voltage_v REAL DEFAULT 380, power_factor REAL DEFAULT 0.92
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS production_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL,
        units_produced INTEGER, daily_output_value REAL
    )''')

    # ---- V2.0 新增 ----
    c.execute('''CREATE TABLE IF NOT EXISTS alarms (
        id INTEGER PRIMARY KEY AUTOINCREMENT, device_group TEXT, meter_name TEXT,
        alarm_level TEXT, alarm_msg TEXT, current_value REAL, threshold_value REAL,
        status TEXT DEFAULT 'active', created_at TEXT, resolved_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS alarm_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT, device_group TEXT, metric TEXT,
        threshold REAL, operator TEXT, level TEXT, message TEXT, enabled INTEGER DEFAULT 1
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS org_structure (
        id INTEGER PRIMARY KEY, name TEXT, parent_id INTEGER, level INTEGER
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT, config_key TEXT UNIQUE, config_value TEXT, description TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS operation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, action TEXT,
        target TEXT, details TEXT, created_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS emission_factors (
        id INTEGER PRIMARY KEY AUTOINCREMENT, factor_type TEXT, value REAL, effective_year INTEGER
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS carbon_quotas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, year INTEGER, total_quota_ton REAL,
        used_ton REAL DEFAULT 0, org_id INTEGER DEFAULT 1
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS optimization_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, suggestion TEXT,
        expected_saving_kwh REAL, device_group TEXT, status TEXT DEFAULT 'pending',
        created_at TEXT, completed_at TEXT
    )''')

    # 索引
    c.execute('CREATE INDEX IF NOT EXISTS idx_energy_ts ON energy_records(timestamp)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_device_ts ON device_energy(timestamp)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_alarms_ts ON alarms(created_at)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_logs_ts ON operation_logs(created_at)')

    conn.commit()
    conn.close()


def simulate_energy():
    start = datetime(2026, 5, 1, 0, 0, 0)
    end = start + timedelta(days=7)
    ts = start
    timestamps = []
    while ts < end:
        timestamps.append(ts)
        ts += timedelta(minutes=5)

    energy_records, device_records = [], []

    for ts in timestamps:
        h, m = ts.hour, ts.minute

        # 空压机
        if 8 <= h < 20:  comp = 132 * np.random.uniform(0.6, 0.85)
        elif 20 <= h < 22: comp = 132 * np.random.uniform(0.45, 0.55)
        else: comp = 132 * np.random.uniform(0.35, 0.50)

        # 铣床
        if 8 <= h < 20: mill = 55 * np.random.uniform(0.65, 0.95) * 4
        elif 20 <= h < 22: mill = 1.2 * 4 * np.random.uniform(0.8, 1.2)
        else: mill = 1.2 * 4 * np.random.uniform(0.5, 0.8)

        # CNC
        if (9 <= h < 12) or (13 <= h < 18): cnc = np.random.uniform(90, 120)
        elif h == 12: cnc = np.random.uniform(40, 60)
        else: cnc = 0.8 * 8 * np.random.uniform(0.8, 1.2)

        # 测试台
        test = 0
        if ((9 <= h < 11 and (h > 9 or m >= 30)) or (14 <= h < 16 and (h < 15 or m <= 30)) or 19 <= h < 20):
            if np.random.random() < 0.7: test = 37 * np.random.uniform(0.7, 0.9)

        # 辅助
        if 8 <= h < 20: aux = np.random.uniform(8, 12)
        elif 20 <= h < 22: aux = np.random.uniform(4, 6)
        else: aux = np.random.uniform(2, 4)

        total = comp + mill + cnc + test + aux
        e_kwh = total * (5 / 60.0)
        pf = round(np.random.uniform(0.88, 0.95), 2)
        current = round(total * 1000 / (380 * 1.732 * pf), 2) if total > 0 else 0

        ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')
        energy_records.append({
            'timestamp': ts_str, 'total_active_power_kw': round(total, 2),
            'compressor_power_kw': round(comp, 2), 'milling_power_kw': round(mill, 2),
            'cnc_power_kw': round(cnc, 2), 'testbench_power_kw': round(test, 2),
            'aux_power_kw': round(aux, 2), 'total_energy_kwh': round(e_kwh, 4),
            'power_factor': pf, 'phase_current_a': round(current, 2), 'phase_voltage_v': 380
        })

        for name, kw in [
            ('双螺杆空压机组', comp), ('数控螺杆转子铣床', mill),
            ('数控车床/CNC加工中心', cnc), ('整机性能测试台', test),
            ('辅助设备（焊接/喷漆/照明）', aux)
        ]:
            device_records.append({
                'timestamp': ts_str, 'device_name': name,
                'power_kw': round(kw, 2), 'energy_kwh': round(kw * (5/60), 4),
                'current_a': round(kw * 1000 / (380 * 1.732 * pf), 2) if kw > 0 else 0,
                'voltage_v': 380, 'power_factor': pf
            })

    return energy_records, device_records


def simulate_production():
    records = []
    for i in range(7):
        d = (datetime(2026, 5, 1) + timedelta(days=i)).strftime('%Y-%m-%d')
        units = np.random.randint(3, 6) if i >= 5 else np.random.randint(6, 13)
        records.append({'date': d, 'units_produced': units, 'daily_output_value': round(units * 0.85, 2)})
    return records


def generate_alarms(energy_records):
    """基于模拟数据生成告警"""
    alarms = []
    for row in energy_records:
        ts = row['timestamp']
        if row['compressor_power_kw'] > 120:
            alarms.append({'device_group': '双螺杆空压机组', 'meter_name': '空压机1#',
                           'alarm_level': 'warning', 'alarm_msg': f"功率{row['compressor_power_kw']}kW超120kW阈值",
                           'current_value': row['compressor_power_kw'], 'threshold_value': 120,
                           'status': 'resolved' if np.random.random() < 0.95 else 'active',
                           'created_at': ts, 'resolved_at': None})
        if row['milling_power_kw'] > 210:
            alarms.append({'device_group': '数控螺杆转子铣床', 'meter_name': '铣床2#',
                           'alarm_level': 'danger', 'alarm_msg': f"功率{row['milling_power_kw']}kW超210kW阈值",
                           'current_value': row['milling_power_kw'], 'threshold_value': 210,
                           'status': 'resolved' if np.random.random() < 0.9 else 'active',
                           'created_at': ts, 'resolved_at': None})
    return alarms


def populate_database(energy_records, device_records, prod_records, alarms):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 清空
    for t in ['device_groups','energy_records','device_energy','production_data','alarms','alarm_rules',
              'org_structure','system_config','operation_logs','emission_factors','carbon_quotas','optimization_tasks']:
        c.execute(f'DELETE FROM {t}')

    # 设备组
    for d in DEVICE_GROUPS:
        c.execute('INSERT INTO device_groups (name,type,count,rated_kw,ratio_pct,location) VALUES (?,?,?,?,?,?)',
                  (d['name'], d['type'], d['count'], d['rated_kw'], d['ratio_pct'], d['location']))

    # 能耗数据
    c.executemany('''INSERT INTO energy_records (timestamp,total_active_power_kw,compressor_power_kw,milling_power_kw,
        cnc_power_kw,testbench_power_kw,aux_power_kw,total_energy_kwh,power_factor,phase_current_a,phase_voltage_v)
        VALUES (:timestamp,:total_active_power_kw,:compressor_power_kw,:milling_power_kw,:cnc_power_kw,
                :testbench_power_kw,:aux_power_kw,:total_energy_kwh,:power_factor,:phase_current_a,:phase_voltage_v)''', energy_records)

    c.executemany('''INSERT INTO device_energy (timestamp,device_name,power_kw,energy_kwh,current_a,voltage_v,power_factor)
        VALUES (:timestamp,:device_name,:power_kw,:energy_kwh,:current_a,:voltage_v,:power_factor)''', device_records)

    # 产量
    c.executemany('INSERT INTO production_data (date,units_produced,daily_output_value) VALUES (:date,:units_produced,:daily_output_value)', prod_records)

    # 告警
    for a in alarms:
        c.execute('INSERT INTO alarms (device_group,meter_name,alarm_level,alarm_msg,current_value,threshold_value,status,created_at,resolved_at) VALUES (?,?,?,?,?,?,?,?,?)',
                  (a['device_group'], a['meter_name'], a['alarm_level'], a['alarm_msg'], a['current_value'], a['threshold_value'], a['status'], a['created_at'], a.get('resolved_at')))

    # 告警规则
    for r in ALARM_RULES:
        c.execute('INSERT INTO alarm_rules (device_group,metric,threshold,operator,level,message,enabled) VALUES (?,?,?,?,?,?,1)',
                  (r['device_group'], r['metric'], r['threshold'], r['operator'], r['level'], r['message']))

    # 组织架构
    for o in ORG_TREE:
        c.execute('INSERT INTO org_structure (id,name,parent_id,level) VALUES (?,?,?,?)',
                  (o['id'], o['name'], o['parent_id'], o['level']))

    # 系统配置
    configs = [
        ('peak_start', '08:00', '峰时开始'), ('peak_end', '20:00', '峰时结束'),
        ('emission_factor', '0.5566', '电网排放因子 kgCO2/kWh'),
        ('carbon_budget_monthly', '180', '月度碳预算 吨'), ('refresh_interval', '10', '实时刷新间隔 秒'),
        ('page_size', '20', '默认分页大小'), ('alarm_retention_days', '90', '告警保留天数'),
    ]
    c.executemany('INSERT INTO system_config (config_key,config_value,description) VALUES (?,?,?)', configs)

    # 操作日志
    logs = [
        ('admin', 'login', '系统', '管理员登录', '2026-05-06 08:00:00'),
        ('admin', 'config', '报警规则', '修改空压机报警阈值130→120kW', '2026-05-06 09:15:00'),
        ('admin', 'export', '碳排放报告', '导出2026年4月碳核算报告', '2026-05-06 14:30:00'),
        ('zhangwei', 'login', '系统', '操作员登录', '2026-05-06 08:30:00'),
        ('zhangwei', 'query', '能耗数据', '查询5月5日用能概况', '2026-05-06 10:00:00'),
    ]
    c.executemany('INSERT INTO operation_logs (username,action,target,details,created_at) VALUES (?,?,?,?,?)', logs)

    # 排放因子
    c.execute('INSERT INTO emission_factors (factor_type,value,effective_year) VALUES (?,?,?)', ('electricity', 0.5566, 2026))

    # 碳配额
    c.execute('INSERT INTO carbon_quotas (year,total_quota_ton,used_ton,org_id) VALUES (?,?,?,?)', (2026, 2200, 980, 1))
    c.execute('INSERT INTO carbon_quotas (year,total_quota_ton,used_ton,org_id) VALUES (?,?,?,?)', (2026, 1800, 820, 2))

    # 优化建议
    tasks = [
        ('空压机组变频改造', '将2#空压机改为变频控制，预计节能15%', 28500, '双螺杆空压机组', 'pending'),
        ('铣床主轴优化', '优化铣床切削参数，减少空载时间', 12600, '数控螺杆转子铣床', 'in_progress'),
        ('车间照明LED替换', '1号厂房灯具升级为LED', 8400, '辅助设备（焊接/喷漆/照明）', 'pending'),
    ]
    c.executemany('INSERT INTO optimization_tasks (title,suggestion,expected_saving_kwh,device_group,status,created_at) VALUES (?,?,?,?,?,datetime("now"))', tasks)

    conn.commit()
    c.execute('SELECT COUNT(*) FROM energy_records')
    print(f"✅ V2.0 数据库初始化完成: {c.fetchone()[0]}条能耗记录 | 5类设备 | 7天数据")
    conn.close()


def main():
    print("=" * 60)
    print("  知微能碳管理系统（AI版）V2.0 - 数据模拟器")
    print("=" * 60)
    init_database()
    print("[1/3] 模拟能耗数据...")
    er, dr = simulate_energy()
    print(f"  总记录: {len(er)} 条 | 设备记录: {len(dr)} 条")
    print("[2/3] 模拟产量 & 生成告警...")
    pr = simulate_production()
    alarms = generate_alarms(er)
    print(f"  产量记录: {len(pr)} 天 | 告警: {len(alarms)} 条")
    print("[3/3] 写入数据库...")
    populate_database(er, dr, pr, alarms)
    print("\n✅ V2.0 数据全部生成完毕！")


if __name__ == '__main__':
    main()
