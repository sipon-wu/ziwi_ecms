"""知微能碳 — 设备管理体系迁移脚本
三步：建表→插数据→关联device_energy
"""
import sys, os, sqlite3, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
random.seed(42)

DB = os.path.join(os.path.dirname(__file__), "energy_data.db")
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 50)
print("设备管理体系迁移")

# ====== 第一步：创建 work_centers 表 ======
c.execute("CREATE TABLE IF NOT EXISTS work_centers ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "code VARCHAR(50) UNIQUE,"
    "name VARCHAR(200) NOT NULL,"
    "parent_id INTEGER REFERENCES work_centers(id),"
    "level INTEGER DEFAULT 1,"
    "rated_power REAL,"
    "location VARCHAR(200),"
    "tags TEXT,"
    "sort_order INTEGER DEFAULT 0,"
    "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
print("✅ 表 work_centers 已就绪")

# ====== 第二步：创建 devices 表 ======
c.execute("CREATE TABLE IF NOT EXISTS devices ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "device_code VARCHAR(50) UNIQUE NOT NULL,"
    "device_name VARCHAR(200) NOT NULL,"
    "work_center_id INTEGER REFERENCES work_centers(id),"
    "rated_power REAL,"
    "device_type VARCHAR(100),"
    "tags TEXT,"
    "status VARCHAR(20) DEFAULT 'active',"
    "notes TEXT,"
    "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
print("✅ 表 devices 已就绪")

# ====== 第三步：device_energy 加 device_id 列（如无） ======
try:
    c.execute("ALTER TABLE device_energy ADD COLUMN device_id INTEGER REFERENCES devices(id)")
    print("✅ device_energy 已添加 device_id 列")
except sqlite3.OperationalError as e:
    if "duplicate" in str(e).lower():
        print("ℹ️  device_energy 已有 device_id 列，跳过")
    else:
        print(f"ℹ️  device_energy device_id 列已存在")

# ====== 第四步：填充工作中心数据（10个真实工作中心+车间层级） ======
c.execute("DELETE FROM work_centers")
c.execute("DELETE FROM devices")

# 先插入车间级（level 1）
workshops = [
    ('WS-001', '一车间', None, 1, None, '1号厂房', '["总装产线"]'),
    ('WS-002', '二车间', None, 1, None, '2号厂房', '["精密加工"]'),
    ('WS-003', '三车间', None, 1, None, '3号厂房', '["总装产线"]'),
    ('WS-004', '空压站', None, 1, None, '公用工程区', '["动力"]'),
]

for code, name, pid, lv, rp, loc, tags in workshops:
    c.execute("INSERT INTO work_centers (code, name, parent_id, level, rated_power, location, tags) VALUES (?,?,?,?,?,?,?)",
              (code, name, pid, lv, rp, loc, tags))

# 查询实际 ID
ws_map = {r['code']: r['id'] for r in c.execute("SELECT code, id FROM work_centers").fetchall()}

# 工作中心（level 2，挂在车间下）
workcenters = [
    ('WC-001', '001-喷油螺杆大机组', ws_map['WS-001'], 2, 250.0, '1号厂房A区'),
    ('WC-002', '002-无油螺杆组', ws_map['WS-002'], 2, 180.0, '2号厂房B区'),
    ('WC-003', '003-喷油螺杆小机组', ws_map['WS-002'], 2, 120.0, '2号厂房C区'),
    ('WC-004', '004-移动大机组', ws_map['WS-003'], 2, 80.0, '3号厂房D区'),
    ('WC-005', '005-移动小机组', ws_map['WS-003'], 2, 60.0, '3号厂房E区'),
    ('WC-006', '006-离心机组', ws_map['WS-001'], 2, 200.0, '1号厂房F区'),
    ('WC-007', '007-活塞机组', ws_map['WS-002'], 2, 75.0, '2号厂房G区'),
    ('WC-008', '008-制氮制氧机组', ws_map['WS-004'], 2, 150.0, '空压站东侧'),
    ('WC-009', '009-真空泵机组', ws_map['WS-003'], 2, 45.0, '3号厂房H区'),
    ('WC-010', '010-无油涡旋机组', ws_map['WS-002'], 2, 90.0, '2号厂房B区'),
]

for code, name, pid, lv, rp, loc in workcenters:
    c.execute("INSERT INTO work_centers (code, name, parent_id, level, rated_power, location) VALUES (?,?,?,?,?,?)",
              (code, name, pid, lv, rp, loc))

print("✅ 工作中心: 4车间 + 10产线组")

# ====== 第五步：插入独立设备（含设备编号和标签） ======
wc_map = {r['code']: r['id'] for r in c.execute("SELECT code, id FROM work_centers WHERE code LIKE 'WC-%'").fetchall()}

devices_data = [
    # (device_code, device_name, work_center_code, rated_power, device_type, tags)
    ('DEV-001', '喷油螺杆空压机#1', 'WC-001', 132.0, '螺杆空压机', '["高压","变频","重点"]'),
    ('DEV-002', '喷油螺杆空压机#2', 'WC-001', 110.0, '螺杆空压机', '["高压","定频"]'),
    ('DEV-003', '冷干机#1', 'WC-001', 8.0, '冷干机', '["辅助"]'),
    ('DEV-004', '无油螺杆空压机#1', 'WC-002', 90.0, '螺杆空压机', '["中压","变频"]'),
    ('DEV-005', '无油螺杆空压机#2', 'WC-002', 90.0, '螺杆空压机', '["中压","变频"]'),
    ('DEV-006', '喷油螺杆空压机#3', 'WC-003', 60.0, '螺杆空压机', '["低压","变频"]'),
    ('DEV-007', '喷油螺杆空压机#4', 'WC-003', 60.0, '螺杆空压机', '["低压","定频"]'),
    ('DEV-008', '移动式空压机#1', 'WC-004', 37.0, '移动空压机', '["移动"]'),
    ('DEV-009', '移动式空压机#2', 'WC-004', 37.0, '移动空压机', '["移动"]'),
    ('DEV-010', '移动式空压机#3', 'WC-005', 30.0, '移动空压机', '["移动"]'),
    ('DEV-011', '移动式空压机#4', 'WC-005', 30.0, '移动空压机', '["移动"]'),
    ('DEV-012', '离心空压机#1', 'WC-006', 200.0, '离心空压机', '["高压","变频","重点"]'),
    ('DEV-013', '离心空压机#2', 'WC-006', 180.0, '离心空压机', '["高压","变频"]'),
    ('DEV-014', '活塞空压机#1', 'WC-007', 37.0, '活塞空压机', '["低压"]'),
    ('DEV-015', '活塞空压机#2', 'WC-007', 37.0, '活塞空压机', '["低压"]'),
    ('DEV-016', '制氮机#1', 'WC-008', 75.0, '制氮机', '["重点","动力"]'),
    ('DEV-017', '制氧机#1', 'WC-008', 75.0, '制氧机', '["重点","动力"]'),
    ('DEV-018', '真空泵#1', 'WC-009', 22.0, '真空泵', '["辅助"]'),
    ('DEV-019', '真空泵#2', 'WC-009', 22.0, '真空泵', '["辅助"]'),
    ('DEV-020', '无油涡旋空压机#1', 'WC-010', 45.0, '涡旋空压机', '["中压","低噪"]'),
    ('DEV-021', '无油涡旋空压机#2', 'WC-010', 45.0, '涡旋空压机', '["中压","低噪"]'),
]

for dc, dn, wcc, rp, dt, tags in devices_data:
    wcid = wc_map.get(wcc)
    c.execute("INSERT INTO devices (device_code, device_name, work_center_id, rated_power, device_type, tags, status) VALUES (?,?,?,?,?,?,?)",
              (dc, dn, wcid, rp, dt, tags, 'active' if random.random() > 0.1 else 'maintenance'))

print(f"✅ 设备: {len(devices_data)} 台（含独立ID和标签）")

# ====== 第六步：将 device_energy 关联到设备（按平均分配到组内设备） ======
c.execute("SELECT COUNT(*) FROM device_energy")
count_de = c.fetchone()[0]
if count_de > 0:
    # 获取设备分组
    wc_devices = {}
    for d in c.execute("SELECT id, work_center_id FROM devices").fetchall():
        wc_devices.setdefault(d['work_center_id'], []).append(d['id'])
    
    # 按 work_center_name 映射到 work_center_id
    name_to_wc = {}
    for wc in c.execute("SELECT id, name FROM work_centers WHERE code LIKE 'WC-%'").fetchall():
        name_to_wc[wc['name']] = wc['id']
    
    # 逐行更新 device_energy
    rows = c.execute("SELECT id, device_name FROM device_energy WHERE device_id IS NULL").fetchall()
    updated = 0
    for row in rows:
        wc_id = name_to_wc.get(row['device_name'])
        if wc_id and wc_id in wc_devices:
            dev_ids = wc_devices[wc_id]
            if dev_ids:
                # 轮询分配给组内设备
                dev_id = dev_ids[updated % len(dev_ids)]
                c.execute("UPDATE device_energy SET device_id=? WHERE id=?", (dev_id, row['id']))
                updated += 1
    conn.commit()
    print(f"✅ device_energy: {updated}/{len(rows)} 条已关联设备ID")
else:
    print("ℹ️  device_energy 无数据，跳过关联")

conn.commit()
conn.close()
print("\n" + "=" * 50)
print("✅ 设备体系迁移完成")
print("   工作中心: 4车间 + 10产线组")
print(f"   设备: {len(devices_data)} 台")
print("   device_energy: 已关联 device_id")
print("=" * 50)
