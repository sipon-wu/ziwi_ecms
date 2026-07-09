"""
知微能碳 — 每日轻量级数据刷新
每天 0:00 cron 执行：
1. 补充今日能耗时序数据（energy_records）
2. 补充今日设备能耗数据（device_energy）
3. 不触碰配置表和历史数据
（注意：guest 操作记录由每月1日的 monthly_guest_cleanup.py 统一清除）
"""

import sqlite3, random, os
from datetime import datetime

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "energy_data.db")

random.seed(99)
today = datetime.now().strftime("%Y-%m-%d")
now = datetime.now().strftime("%Y-%m-%d %H:%M")

print(f"[{now}] 每日数据刷新开始... date={today}")

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# 0. 兜底：如果 optimization_tasks 为空，插入默认任务
cnt = c.execute("SELECT COUNT(*) FROM optimization_tasks").fetchone()[0]
if cnt == 0:
    tasks = [
        ('空压机群控优化',     '001-喷油螺杆大机组', 185000,  '执行中'),
        ('无油螺杆效率提升',   '002-无油螺杆组',     96000,   '待执行'),
        ('离心机组变频改造',   '006-离心机组',       220000,  '执行中'),
        ('车间照明LED改造',    '总装车间',           42000,   '已完成'),
        ('制氮机余热回收',     '008-制氮制氧机组',   150000,  '待执行'),
        ('真空泵待机节能',     '009-真空泵机组',     35000,   '待执行'),
    ]
    c.executemany(
        "INSERT INTO optimization_tasks (title, device_group, expected_saving_kwh, status) VALUES (?,?,?,?)",
        tasks
    )
    print(f"  [0] 初始化 optimization_tasks: {len(tasks)} 条")

# 1. 补充今日能耗时序（288个5分钟点）——先查是否已有
existing = c.execute("SELECT COUNT(*) FROM energy_records WHERE timestamp LIKE ?", (f"{today}%",)).fetchone()[0]
if existing > 0:
    print(f"  [1] 今日能耗时序已存在 ({existing}条)，跳过")
else:
    for h in range(24):
        for m in range(0, 60, 5):
            ts = f"{today} {h:02d}:{m:02d}"
            if 8 <= h < 12:
                bp = 3200 + random.random() * 500
            elif 12 <= h < 13:
                bp = 2500 + random.random() * 300
            elif 13 <= h < 18:
                bp = 3400 + random.random() * 600
            elif 18 <= h < 22:
                bp = 2200 + random.random() * 400
            else:
                bp = 1800 + random.random() * 300
            p = round(bp + (random.random() - 0.5) * 200, 2)
            c.execute(
                "INSERT INTO energy_records (timestamp,total_energy_kwh,total_active_power_kw,power_factor) VALUES (?,?,?,?)",
                (ts, round(p * 5 / 60, 2), p, round(0.90 + random.random() * 0.08, 2)),
            )
    print(f"  [1] 生成今日能耗时序: 288 条")

# 2. 补充今日设备能耗（8-18点，按额定功率分摊到21台设备）
devices = c.execute(
    "SELECT id, device_code, rated_power FROM devices WHERE rated_power>0"
).fetchall()

de_existing = c.execute("SELECT COUNT(*) FROM device_energy WHERE timestamp LIKE ?", (f"{today}%",)).fetchone()[0]
if de_existing > 0:
    print(f"  [2] 今日设备能耗已存在 ({de_existing}条)，跳过")
else:
    for h in range(8, 18):
        for m in range(0, 60, 5):
            ts = f"{today} {h:02d}:{m:02d}"
            for d in devices:
                rp = d["rated_power"] or 50
                load = 0.4 + random.random() * 0.45
                pw = round(rp * load, 2)
                c.execute(
                    "INSERT INTO device_energy (timestamp,device_name,power_kw,energy_kwh,current_a,voltage_v,power_factor,device_id) VALUES (?,?,?,?,?,?,?,?)",
                    (
                        ts,
                        d["device_code"],
                        pw,
                        round(pw * 5 / 60, 2),
                        round(pw / (1.732 * 0.38 * 0.9), 1),
                        round(375 + random.random() * 10, 1),
                        round(0.85 + random.random() * 0.12, 2),
                        d["id"],
                    ),
                )
    total_de = len(devices) * 10 * 12
    print(f"  [2] 生成今日设备能耗: {total_de} 条 ({len(devices)}台设备)")

conn.commit()
conn.close()

print(f"[{now}] 每日数据刷新完成")
