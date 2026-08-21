"""
知微能碳 — 历史能耗回填（季节变量规则 + 产量联动 + 相对功耗权重 + 作息制度）

能源模型（双变量规则）：
  月度能耗 = 月产量 × 基准单耗(BASE_PER_UNIT) × 季节系数(SEASONAL_FACTOR)
    - 季节系数：冬季无空调制冷→负荷低(0.90~0.93)，夏季空调高峰→负荷高(1.05~1.10)
    - 产量联动：月产量少→总能耗按比例少（解决仿真能耗与产量脱钩问题）
  单耗(单位产品能耗) = 基准单耗 × 季节系数 → 冬季低、夏季高，且各月量级一致

设备能耗分摊（2026-08-21 升级）：
  - 权重 = 额定功率(rated_power) × 稼动率(utilization)  → 相对功耗
  - 即每台设备当月能耗 = 当月总能耗 × (该设备相对功耗 / 全厂相对功耗合计)
  - 取代原先的随机负载 0.4~0.85，使设备面板/下钻/监控总功率同口径
  - 监控「当前总功率」卡片 = 各设备功率之和（在 monitoring.py 中汇总）

作息制度（用户 2026-08-21 指定）：
  - 每日 8:00-17:00 班次，午休 12:00-13:00 停机/低载 → 设备能耗仅在该时段生成
  - 每周 6 天（周一~周六），周日仅保留基础负荷（基础公用工况）

无产量数据的月份（如 8 月）回退为：日均基准(DAY_BASE) × 季节系数。

用法：
  python3 backfill_seasonal.py                               # 默认 2026-01-01 ~ 今天
  python3 backfill_seasonal.py --start 2026-01-01 --end 2026-08-21
  python3 backfill_seasonal.py --dry-run                     # 只打印各月目标，不写库
"""
import sqlite3, random, os, argparse
from datetime import datetime, timedelta

DB_PATH = os.environ.get("ECMS_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "energy_data.db"))

# ====== 季节变量规则：冬季无空调→系数<1；夏季空调→系数>1 ======
SEASONAL_FACTOR = {
    1: 0.93, 2: 0.90, 3: 0.96, 4: 1.00, 5: 1.00, 6: 1.05,
    7: 1.10, 8: 1.08, 9: 1.00, 10: 0.97, 11: 0.94, 12: 0.92,
}
BASE_PER_UNIT = 186    # 基准单耗 kWh/台（再乘季节系数）；对齐真实抄表约 6.25 万 kWh/月
DAY_BASE = 2000        # 无产量月份的日均基准 kWh（保持原量级）

SLOTS = [(h, m) for h in range(24) for m in range(0, 60, 5)]
# 设备生产时段：8:00-17:00（含 17:55 末点），午休 12:00-13:00 低载
WORK_SLOTS = [(h, m) for h in range(8, 18) for m in range(0, 60, 5)]
LUNCH = {(12, m) for m in range(0, 60, 5)}


def load_shape():
    """厂级负载曲线形状的归一化权重（288 点，午休更低、凌晨最低）"""
    raw = []
    for h, m in SLOTS:
        if 8 <= h < 12:
            bp = 3300
        elif 12 <= h < 13:        # 午休：厂级基础负荷（照明/部分公用工况）
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


def month_day_weights(year, month):
    """该月每个自然日的权重（周一~周六=1.0，周日=0.12 仅基础负荷）与月总权重"""
    if month == 12:
        dim = 31
    else:
        dim = (datetime(year, month + 1, 1) - datetime(year, month, 1)).days
    weights = []
    total = 0.0
    for d in range(1, dim + 1):
        wd = datetime(year, month, d).weekday()
        w = 1.0 if wd != 6 else 0.12   # 周日休息，仅基础负荷
        weights.append(w)
        total += w
    return weights, total, dim


def gen_day_energy(date_str, day_total):
    rows = []
    for i, (h, m) in enumerate(SLOTS):
        frac = SHAPE[i] * (1 + (random.random() - 0.5) * 0.04)  # 轻微抖动
        kwh = day_total * frac
        p = kwh * 12  # 5 分钟点 → kW
        pf = round(0.90 + random.random() * 0.08, 2)
        rows.append((f"{date_str} {h:02d}:{m:02d}", round(kwh, 2), round(p, 2), pf))
    return rows


def gen_day_device(date_str, day_total, devices):
    """按相对功耗权重(额定功率×稼动率)分摊日能耗到各设备；
    仅在生产时段 8:00-17:00 生成，午休 12:00-13:00 低载。"""
    weights = [d["rated_power"] * (d["utilization"] or 0.4) for d in devices]
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
                f"{date_str} {h:02d}:{m:02d}",
                d["device_name"], round(pw, 2), round(pw * 5 / 60, 2),
                round(pw / (1.732 * 0.38 * 0.9), 1),
                round(375 + random.random() * 10, 1),
                round(0.85 + random.random() * 0.12, 2),
                d["id"],
            ))
    return rows


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2026-01-01")
    ap.add_argument("--end", default=datetime.now().strftime("%Y-%m-%d"))
    ap.add_argument("--dry-run", action="store_true", help="只打印各月目标，不写库")
    args = ap.parse_args()

    start = datetime.strptime(args.start, "%Y-%m-%d")
    end = datetime.strptime(args.end, "%Y-%m-%d")
    print(f"[*] 回填范围: {start.date()} ~ {end.date()}  模型=产量联动×季节×相对功耗权重")

    conn = get_db()
    c = conn.cursor()
    devices = c.execute(
        "SELECT id, device_name, rated_power, COALESCE(utilization,0.4) AS utilization "
        "FROM devices WHERE rated_power>0"
    ).fetchall()
    month_units = dict(c.execute(
        "SELECT CAST(strftime('%m',date) AS INT) m, SUM(units_produced) FROM production_data GROUP BY m"
    ).fetchall())
    conn.close()

    print("[*] 各月目标能耗 (kWh):")
    for mo in range(1, 13):
        u = month_units.get(mo, 0)
        if u:
            tgt = u * BASE_PER_UNIT * SEASONAL_FACTOR[mo]
            print(f"    {mo:02d}月: 产量{u} × {BASE_PER_UNIT} × {SEASONAL_FACTOR[mo]} = {tgt:,.0f}")
        else:
            print(f"    {mo:02d}月: 无产量 → 日均{DAY_BASE}×{SEASONAL_FACTOR[mo]}")

    if args.dry_run:
        print("[*] dry-run 完成")
        return

    conn = get_db()
    c = conn.cursor()
    devices = c.execute(
        "SELECT id, device_name, rated_power, COALESCE(utilization,0.4) AS utilization "
        "FROM devices WHERE rated_power>0"
    ).fetchall()
    month_units = dict(c.execute(
        "SELECT CAST(strftime('%m',date) AS INT) m, SUM(units_produced) FROM production_data GROUP BY m"
    ).fetchall())

    like_start = f"{args.start} 00:00"
    like_end = f"{args.end} 23:55"
    c.execute("DELETE FROM energy_records WHERE timestamp>=? AND timestamp<=?", (like_start, like_end))
    c.execute("DELETE FROM device_energy WHERE timestamp>=? AND timestamp<=?", (like_start, like_end))
    print(f"[*] 已删除旧数据 (范围 {like_start} ~ {like_end})")

    cache = {}
    day = start
    n_days = 0
    while day <= end:
        date_str = day.strftime("%Y-%m-%d")
        mo = day.month
        seasonal = SEASONAL_FACTOR[mo]
        u = month_units.get(mo, 0)
        wd = day.weekday()
        if u:
            if (day.year, mo) not in cache:
                cache[(day.year, mo)] = month_day_weights(day.year, mo)
            weights, total_w, dim = cache[(day.year, mo)]
            month_target = u * BASE_PER_UNIT * seasonal
            dw = weights[day.day - 1]
            day_total = month_target * dw / total_w
        else:
            # 无产量月份：周日仅基础负荷
            dw = 1.0 if wd != 6 else 0.12
            day_total = DAY_BASE * seasonal * dw

        random.seed(int(day.strftime("%Y%m%d")))
        er = gen_day_energy(date_str, day_total)
        de = gen_day_device(date_str, day_total, devices)
        c.executemany(
            "INSERT INTO energy_records (timestamp,total_energy_kwh,total_active_power_kw,power_factor) VALUES (?,?,?,?)", er)
        c.executemany(
            "INSERT INTO device_energy (timestamp,device_name,power_kw,energy_kwh,current_a,voltage_v,power_factor,device_id) VALUES (?,?,?,?,?,?,?,?)", de)
        n_days += 1
        day += timedelta(days=1)

    conn.commit()
    rows = c.execute(
        """SELECT CAST(strftime('%m',timestamp) AS INT) m, ROUND(SUM(total_energy_kwh),0) k
           FROM energy_records WHERE timestamp>=? AND timestamp<=? GROUP BY m ORDER BY m""",
        (like_start, like_end)).fetchall()
    print(f"[*] 已重生成 {n_days} 天")
    print("[*] 各月能耗合计 (kWh):")
    for r in rows:
        u = month_units.get(r['m'], 0)
        pu = f"{r['k']/u:,.0f}" if u else "—"
        print(f"    {r['m']:02d}月: {r['k']:>12,.0f}   单耗={pu} kWh/台")
    de_cnt = c.execute("SELECT COUNT(DISTINCT device_id) FROM device_energy WHERE timestamp>=? AND timestamp<=?",
                       (like_start, like_end)).fetchone()[0]
    print(f"[*] 设备能耗覆盖设备数: {de_cnt}")
    conn.close()
    print("[✅] 回填完成")


if __name__ == "__main__":
    main()
