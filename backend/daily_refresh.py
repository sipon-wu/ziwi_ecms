"""
知微能碳 — 每日轻量级数据刷新
每天 0:00 cron 执行：
1. 补充今日能耗时序数据（energy_records）
2. 补充今日设备能耗数据（device_energy）
3. 不触碰配置表和历史数据
（注意：guest 操作记录由每月1日的 monthly_guest_cleanup.py 统一清除）

能源模型（与 backfill_seasonal.py 一致）：
  当日目标能耗 = 月产量 × 基准单耗(BASE_PER_UNIT) × 季节系数(SEASONAL_FACTOR) × 当日权重
  无产量月份 → 日均基准(DAY_BASE) × 季节系数
"""
import sqlite3, random, os
from datetime import datetime, timedelta

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "energy_data.db")

random.seed(int(datetime.now().strftime("%Y%m%d")))
today = datetime.now().strftime("%Y-%m-%d")
now = datetime.now().strftime("%Y-%m-%d %H:%M")

# ====== 季节变量规则：冬季无空调→系数<1；夏季空调→系数>1 ======
SEASONAL_FACTOR = {
    1: 0.93, 2: 0.90, 3: 0.96, 4: 1.00, 5: 1.00, 6: 1.05,
    7: 1.10, 8: 1.08, 9: 1.00, 10: 0.97, 11: 0.94, 12: 0.92,
}
BASE_PER_UNIT = 6800   # 基准单耗 kWh/台（再乘季节系数）
DAY_BASE = 64000       # 无产量月份的日均基准 kWh

SLOTS = [(h, m) for h in range(24) for m in range(0, 60, 5)]


def load_shape():
    raw = []
    for h, m in SLOTS:
        if 8 <= h < 12:
            bp = 3300
        elif 12 <= h < 13:        # 午休：厂级基础负荷
            bp = 1800
        elif 13 <= h < 18:
            bp = 3600
        elif 18 <= h < 22:
            bp = 2200
        else:                     # 夜间基础负荷
            bp = 1500
        raw.append(bp)
    s = sum(raw)
    return [x / s for x in raw]


SHAPE = load_shape()

_today_month = int(datetime.now().strftime("%m"))
SEASONAL = SEASONAL_FACTOR[_today_month]

# 作息制度：每日 8:00-17:00 生产，午休 12:00-13:00 低载，每周6天(周一~周六)，周日仅基础负荷
WORK_SLOTS = [(h, m) for h in range(8, 18) for m in range(0, 60, 5)]
LUNCH = {(12, m) for m in range(0, 60, 5)}

print(f"[{now}] 每日数据刷新开始... date={today} 季节系数={SEASONAL}")

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

# 计算今日目标能耗
units_this_month = c.execute(
    "SELECT SUM(units_produced) FROM production_data WHERE strftime('%Y-%m', date)=?",
    (datetime.now().strftime("%Y-%m"),)
).fetchone()[0] or 0

if units_this_month:
    y, mo = datetime.now().year, _today_month
    if mo == 12:
        dim = 31
    else:
        dim = (datetime(y, mo + 1, 1) - datetime(y, mo, 1)).days
    total_w = 0.0
    for d in range(1, dim + 1):
        total_w += 1.0 if datetime(y, mo, d).weekday() != 6 else 0.12
    dw = 1.0 if datetime.now().weekday() != 6 else 0.12
    month_target = units_this_month * BASE_PER_UNIT * SEASONAL
    day_total = month_target * dw / total_w
    print(f"  [*] 产量联动: 本月产量{units_this_month} → 今日目标 {day_total:,.0f} kWh")
else:
    dw = 1.0 if datetime.now().weekday() != 6 else 0.12
    day_total = DAY_BASE * SEASONAL * dw
    print(f"  [*] 无产量月份: 今日目标 {day_total:,.0f} kWh (日均×季节×作息)")

# 1. 补充今日能耗时序（288个5分钟点）
existing = c.execute("SELECT COUNT(*) FROM energy_records WHERE timestamp LIKE ?", (f"{today}%",)).fetchone()[0]
if existing > 0:
    print(f"  [1] 今日能耗时序已存在 ({existing}条)，跳过")
else:
    rows = []
    for i, (h, m) in enumerate(SLOTS):
        frac = SHAPE[i] * (1 + (random.random() - 0.5) * 0.04)
        kwh = day_total * frac
        p = kwh * 12
        pf = round(0.90 + random.random() * 0.08, 2)
        rows.append((f"{today} {h:02d}:{m:02d}", round(kwh, 2), round(p, 2), pf))
    c.executemany(
        "INSERT INTO energy_records (timestamp,total_energy_kwh,total_active_power_kw,power_factor) VALUES (?,?,?,?)",
        rows,
    )
    print(f"  [1] 生成今日能耗时序: {len(rows)} 条")

# 2. 补充今日设备能耗（8:00-17:00 生产时段，午休低载；按 额定功率×稼动率 权重分摊）
devices = c.execute(
    "SELECT id, device_name, rated_power, COALESCE(utilization,0.4) AS utilization "
    "FROM devices WHERE rated_power>0"
).fetchall()

de_existing = c.execute("SELECT COUNT(*) FROM device_energy WHERE timestamp LIKE ?", (f"{today}%",)).fetchone()[0]
if de_existing > 0:
    print(f"  [2] 今日设备能耗已存在 ({de_existing}条)，跳过")
else:
    weights = [d["rated_power"] * d["utilization"] for d in devices]
    total_w = sum(weights) or 1
    n_slot = len(WORK_SLOTS)
    rows = []
    for d, w in zip(devices, weights):
        d_daily = day_total * (w / total_w)
        per_slot = d_daily / n_slot
        for (h, m) in WORK_SLOTS:
            factor = 0.12 if (h, m) in LUNCH else 1.0
            pw = per_slot * 12 * factor * (1 + (random.random() - 0.5) * 0.05)
            rows.append((
                f"{today} {h:02d}:{m:02d}",
                d["device_name"], round(pw, 2), round(pw * 5 / 60, 2),
                round(pw / (1.732 * 0.38 * 0.9), 1),
                round(375 + random.random() * 10, 1),
                round(0.85 + random.random() * 0.12, 2),
                d["id"],
            ))
    c.executemany(
        "INSERT INTO device_energy (timestamp,device_name,power_kw,energy_kwh,current_a,voltage_v,power_factor,device_id) VALUES (?,?,?,?,?,?,?,?)",
        rows,
    )
    print(f"  [2] 生成今日设备能耗: {len(rows)} 条 ({len(devices)}台设备)")

conn.commit()
conn.close()

print(f"[{now}] 每日数据刷新完成")
