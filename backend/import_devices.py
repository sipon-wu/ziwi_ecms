"""
以固定资产盘点表识别结果为准，重建设备主数据为 114 台生产用能设备。
- 为每个「使用部门」建一个顶层工作中心 work_center（保留原有 239-252 不动）
- 清空旧设备，按 devices_114.json 插入新设备（含 rated_power / utilization / work_center_id）
- 若 devices 表缺 utilization 列则自动添加

用法: python3 import_devices.py
"""
import sqlite3, json, os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "energy_data.db")
JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "devices_114.json")

with open(JSON_PATH, encoding="utf-8") as f:
    devices = json.load(f)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# 1. 缺列则加 utilization
try:
    c.execute("ALTER TABLE devices ADD COLUMN utilization REAL")
    print("  [+] added column utilization")
except sqlite3.OperationalError:
    print("  [=] utilization column exists")

# 2. 为每个部门建工作中心（顶层 level=1），已存在则复用
depts = sorted({d.get("dept") or "未分类" for d in devices})
wc_id = {}
seq = 1
for dep in depts:
    row = c.execute("SELECT id FROM work_centers WHERE name=?", (dep,)).fetchone()
    if row:
        wc_id[dep] = row["id"]
    else:
        c.execute("INSERT INTO work_centers (code,name,level) VALUES (?,?,1)",
                  (f"WC-DEPT-{seq:02d}", dep))
        wc_id[dep] = c.lastrowid
        seq += 1
        print(f"  [+] work_center '{dep}' -> id={wc_id[dep]}")
print(f"  部门工作中心数: {len(depts)}")

# 3. 清空旧设备
old = c.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
c.execute("DELETE FROM devices")
print(f"  [-] 删除旧设备 {old} 台")

# 4. 插入 114 台
ins = ("INSERT INTO devices (device_code,device_name,work_center_id,rated_power,"
       "device_type,tags,status,notes,utilization) VALUES (?,?,?,?,?,?,?,?,?)")
n_ok = 0
for d in devices:
    dep = d.get("dept") or "未分类"
    tags = json.dumps([d["device_type"]], ensure_ascii=False)
    c.execute(ins, (d["device_code"], d["device_name"], wc_id[dep],
                    d["rated_power"], d["device_type"], tags, d["status"],
                    d["notes"], d["utilization"]))
    n_ok += 1

conn.commit()
n = c.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
rated = c.execute("SELECT COUNT(*) FROM devices WHERE rated_power>0").fetchone()[0]
print(f"  [+] 插入设备 {n} 台（其中含额定功率 {rated} 台）")

print("  各部门设备数:")
for r in c.execute(
    "SELECT wc.name AS name, COUNT(*) AS cnt FROM devices d "
    "JOIN work_centers wc ON wc.id=d.work_center_id GROUP BY wc.name ORDER BY cnt DESC"
):
    print(f"    {r['name']}: {r['cnt']}")
rel = c.execute("SELECT ROUND(SUM(rated_power*COALESCE(utilization,0.4)),1) FROM devices").fetchone()[0]
print(f"  相对功耗合计(权重口径): {rel} kW")
conn.close()
print("[✅] 设备主数据已重建")
