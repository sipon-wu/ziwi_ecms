"""
将月度产量拆分为每日产量写入 production_data，供概览页按日查询。
规则：
- 每月产量平均分摊到当月工作日（周一至周五）
- 周末/节假日产量为 0
- 单价 = 0.85 万元/台（单位产值能耗用）
- 1-7 月使用月销量.xlsx 数据；8 月按 7 月 305 台估算
"""
import sqlite3
import os
from datetime import date, timedelta
from calendar import monthrange

DB = os.path.join(os.path.dirname(__file__), "energy_data.db")

UNIT_PRICE_WAN = 0.85  # 万元/台


def working_days_in_month(year: int, month: int) -> int:
    """统计某月工作日数量（仅排除周六日）"""
    count = 0
    _, last_day = monthrange(year, month)
    for day in range(1, last_day + 1):
        d = date(year, month, day)
        if d.weekday() < 5:  # 0-4 周一到周五
            count += 1
    return count


# 月销量.xlsx 提供的 2026 年 1-7 月接单量
MONTHLY_UNITS = {
    1: 300,
    2: 108,
    3: 251,
    4: 301,
    5: 262,
    6: 317,
    7: 305,
}

# 8 月暂无真实订单：按 7 月产量 × (8 月工作日 / 7 月工作日) 估算，避免直接复用 7 月
# 2026-07 工作日 23 天，2026-08 工作日 21 天 → 305 * 21/23 ≈ 278.5，取整 279
MONTHLY_UNITS[8] = round(MONTHLY_UNITS[7] * working_days_in_month(2026, 8) / working_days_in_month(2026, 7))


def generate(year: int = 2026) -> list[dict]:
    records = []
    for month, total in MONTHLY_UNITS.items():
        work_days = working_days_in_month(year, month)
        if work_days == 0:
            continue
        # 产量按整数台分配到工作日，前 remainder 天多 1 台
        base = total // work_days
        remainder = total - base * work_days
        work_dates = []
        _, last_day = monthrange(year, month)
        for day in range(1, last_day + 1):
            d = date(year, month, day)
            if d.weekday() < 5:
                work_dates.append(d)
        high_dates = set(work_dates[:remainder])  # 这些工作日多 1 台
        for day in range(1, last_day + 1):
            d = date(year, month, day)
            if d.weekday() >= 5:
                units = 0
            else:
                units = base + (1 if d in high_dates else 0)
            records.append({
                "date": d.isoformat(),
                "units_produced": units,
                "daily_output_value": round(units * UNIT_PRICE_WAN, 2),
            })
    return records


def main():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # 删除 2026 年的旧月度/日度产量数据，避免重复
    c.execute("DELETE FROM production_data WHERE strftime('%Y', date) = '2026'")
    deleted = c.rowcount
    records = generate()
    c.executemany(
        "INSERT INTO production_data (date, units_produced, daily_output_value) VALUES (:date, :units_produced, :daily_output_value)",
        records,
    )
    inserted = len(records)
    conn.commit()
    conn.close()
    print(f"删除 {deleted} 条旧记录，写入 {inserted} 条日产量记录")
    print(f"覆盖月份: {sorted(MONTHLY_UNITS.keys())}")


if __name__ == "__main__":
    main()
