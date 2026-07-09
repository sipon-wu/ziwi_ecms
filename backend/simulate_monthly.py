"""
知微能碳 — 数据模拟更新引擎 v2（评审融合版）

遵循 Visio 流程图双分支逻辑 + 5位专家评审意见融合方案:

【评审融合要点】
1. 独立表 daily_energy   (一致通过)
2. 按品种独立偏移容差   (一致通过)
3. 分解曲线: 默认跟随用电, 天然气独立 (折中方案)
4. 设备分摊: 额定功率比例 + 前提条件说明 (主审采纳)
5. 索引方案: 按技术架构师修正顺序执行
6. 数据质量等级标签 (碳分析师要求)
7. CLI 增加 --natural-gas / --coal / --steam 等参数 (能源专家建议)

【流程图双分支】
分支A (新数据): 用户上传 → 采用最新月度数据 → 时间段分拆 → 按设备分摊 → 前端刷新
分支B (无新数据): 采用上月度数据 → 时间段分拆(偏移±5%) → 按设备分摊(偏移±1%) → 前端刷新

用法:
  # 模式A: 有新数据
  python simulate_monthly.py --electricity 62550 --water 1000 --diesel 4500 --gasoline 100 --month 2026-05 --mode new

  # 模式B: 无新数据（使用上月，随机偏移）
  python simulate_monthly.py --mode auto
"""
import argparse, json, random, os, sys
from datetime import datetime, timedelta

random.seed(42)

# ====== 能源类型定义 ======
ENERGY_TYPES = {
    'electricity':  {'unit': 'kWh',     'scope': 'scope2', 'source': 'purchased', 'decompose': 'follow_electricity'},
    'water':        {'unit': 'ton',     'scope': 'scope1', 'source': 'purchased', 'decompose': 'follow_electricity'},
    'natural_gas':  {'unit': 'm3',      'scope': 'scope1', 'source': 'purchased', 'decompose': 'independent'},
    'diesel':       {'unit': 'L',       'scope': 'scope1', 'source': 'purchased', 'decompose': 'follow_electricity'},
    'gasoline':     {'unit': 'L',       'scope': 'scope1', 'source': 'purchased', 'decompose': 'follow_electricity'},
    'lpg':          {'unit': 'kg',      'scope': 'scope1', 'source': 'purchased', 'decompose': 'follow_electricity'},
    'steam':        {'unit': 'ton',     'scope': 'scope2', 'source': 'purchased', 'decompose': 'independent'},
    'heat':         {'unit': 'GJ',      'scope': 'scope2', 'source': 'purchased', 'decompose': 'independent'},
    'coal':         {'unit': 'ton',     'scope': 'scope1', 'source': 'purchased', 'decompose': 'follow_electricity'},
    'compressed_air':{'unit': 'm3',     'scope': 'scope2', 'source': 'self',      'decompose': 'follow_electricity'},
}

# 按品种独立偏移容差（能源专家建议）
OFFSET_RANGES = {
    'electricity': 0.05,    # ±5%
    'water': 0.10,          # ±10%
    'natural_gas': 0.08,    # ±8%
    'diesel': 0.15,         # ±15%
    'gasoline': 0.15,       # ±15%
    'lpg': 0.10,            # ±10%
    'steam': 0.10,          # ±10%
    'heat': 0.10,           # ±10%
    'coal': 0.08,           # ±8%
    'compressed_air': 0.05, # ±5%
}

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'energy_data.db')


def get_db():
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def check_data_source():
    """检查是否有当月新数据（通过检查 daily_energy 中的最新月份）"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_energy'")
    if not c.fetchone():
        conn.close()
        return False
    row = c.execute("SELECT MAX(date) as max_date FROM daily_energy").fetchone()
    conn.close()
    if not row or not row['max_date']:
        return False
    max_date = str(row['max_date'])
    # 如果最新数据距现在超过2个月，认为无新数据
    return (datetime.now() - datetime.strptime(max_date[:10], '%Y-%m-%d')).days < 60


def get_last_month_data(month):
    """获取上月的 daily_energy 数据作为基准"""
    conn = get_db()
    c = conn.cursor()
    year, m = month.split('-')
    prev_m = int(m) - 1
    prev_year = year
    if prev_m == 0:
        prev_m = 12
        prev_year = str(int(year) - 1)
    prev_month = f"{prev_year}-{prev_m:02d}"
    
    rows = c.execute("""
        SELECT energy_type, AVG(value) as avg_daily, SUM(value) as total
        FROM daily_energy
        WHERE date LIKE ? || '%'
        GROUP BY energy_type
    """, (prev_month,)).fetchall()
    conn.close()
    return {r['energy_type']: {'avg_daily': r['avg_daily'], 'total': r['total']} for r in rows}


def decompose_month(total, energy_type, month, is_new_data=True):
    """
    月总量 → 日值（工作日/周末模式）
    分支A (new): 直接分解，不偏移
    分支B (old): 分解 + 按品种独立偏移
    """
    year = int(month[:4])
    month_num = int(month[5:7])
    if month_num == 12:
        days_in_month = 31
    else:
        start = datetime(year, month_num, 1)
        next_m = datetime(year, month_num + 1, 1)
        days_in_month = (next_m - start).days

    daily_values = []
    for day in range(1, days_in_month + 1):
        dt = datetime(year, month_num, day)
        wd = dt.weekday()
        # 工作日权重1.0，周末权重0.5
        factor = 1.0 if wd < 5 else 0.5
        daily_values.append(factor)

    # 归一化
    total_factor = sum(daily_values)
    daily_values = [v / total_factor * total for v in daily_values]

    # 分支B: 按品种独立偏移
    if not is_new_data:
        offset_range = OFFSET_RANGES.get(energy_type, 0.05)
        dv = []
        for v in daily_values:
            offset = 1.0 + random.uniform(-offset_range, offset_range)
            dv.append(v * offset)
        # 总量守恒
        scale = total / sum(dv)
        daily_values = [v * scale for v in dv]

    return daily_values, days_in_month


def allocate_to_devices(daily_values, month):
    """
    设备分摊：按额定功率比例 + 1%随机偏移
    对每天的总量按21台设备的额定功率比例分摊
    """
    conn = get_db()
    c = conn.cursor()
    # 获取所有设备及其额定功率
    devices = c.execute("""
        SELECT d.id, d.device_code, d.device_name, d.rated_power, wc.name as wc_name
        FROM devices d
        JOIN work_centers wc ON wc.id = d.work_center_id
        WHERE d.rated_power > 0 AND d.status = 'active'
        ORDER BY wc.id, d.id
    """).fetchall()
    conn.close()

    if not devices:
        return []

    total_rated = sum(d['rated_power'] for d in devices if d['rated_power'])
    ratios = [(d['rated_power'] or 0) / total_rated for d in devices]

    year = int(month[:4])
    month_num = int(month[5:7])

    device_data = []
    for day_idx, day_total in enumerate(daily_values):
        day = day_idx + 1
        date_str = f"{month}-{day:02d}"
        for dev_idx, dev in enumerate(devices):
            ratio = ratios[dev_idx]
            # 1%随机偏移
            offset = 1.0 + random.uniform(-0.01, 0.01)
            dev_daily = round(day_total * ratio * offset, 2)
            device_data.append({
                'date': date_str,
                'device_id': dev['id'],
                'device_code': dev['device_code'],
                'device_name': dev['device_name'],
                'work_center': dev['wc_name'],
                'daily_kwh': dev_daily,
                'ratio': round(ratio * 100, 2),
            })

    return device_data


def gen_hourly_from_daily(daily_value, date_str, energy_type='electricity', is_weekend=False):
    """
    日值 → 24小时分解
    跟随用电曲线: 工作日高峰/午休/晚班模式
    独立曲线: 天然气/蒸汽用热惯性模式
    """
    is_independent = ENERGY_TYPES.get(energy_type, {}).get('decompose') == 'independent'
    hours = []
    for h in range(24):
        if is_independent:
            # 独立曲线：热惯性，全天较均匀，白天略高
            if 6 <= h <= 22:
                hf = 1.0 / 24 * 1.1 + random.random() * 0.02
            else:
                hf = 1.0 / 24 * 0.8 + random.random() * 0.02
        else:
            # 跟随用电曲线
            if is_weekend:
                if 9 <= h <= 17:
                    hf = 1.0 / 24 * 1.2 + random.random() * 0.02
                else:
                    hf = 1.0 / 24 * 0.7 + random.random() * 0.02
            else:
                if 8 <= h < 12:
                    hf = 1.0 / 24 * 1.8 + random.random() * 0.02
                elif 12 <= h < 13:
                    hf = 1.0 / 24 * 1.1 + random.random() * 0.02
                elif 13 <= h < 18:
                    hf = 1.0 / 24 * 1.7 + random.random() * 0.02
                elif 18 <= h < 22:
                    hf = 1.0 / 24 * 1.2 + random.random() * 0.02
                else:
                    hf = 1.0 / 24 * 0.5 + random.random() * 0.02
        hours.append({
            'hour': h,
            'value': round(daily_value * hf, 2),
            'ratio_pct': round(hf * 100, 2),
        })
    # 总量守恒
    total = sum(h['value'] for h in hours)
    if total > 0:
        scale = daily_value / total
        for h in hours:
            h['value'] = round(h['value'] * scale, 2)
    return hours


def write_to_db(daily_data, device_data, hour_data, generation_method='decomposed'):
    """写入 daily_energy + device_energy"""
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 写入 daily_energy
    written = 0
    for item in daily_data:
        etype = item['energy_type']
        info = ENERGY_TYPES.get(etype, {})
        c.execute("""
            INSERT OR REPLACE INTO daily_energy 
            (date, energy_type, value, unit, scope, source_type, 
             generation_method, decomposition_method, quality_flag, data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item['date'], etype, item['value'], info.get('unit', ''),
            info.get('scope', 'scope2'), info.get('source', 'purchased'),
            generation_method,
            info.get('decompose', 'follow_electricity'),
            'simulated' if generation_method == 'simulated' else 'estimated',
            'simulate_monthly'
        ))
        written += 1
    conn.commit()

    # 写入 device_energy（仅电力走设备链路）
    for dh in hour_data:
        if dh['device_id'] is None:
            continue
        ts = f"{dh['date']} {dh['hour']:02d}:00:00"
        c.execute("""
            INSERT INTO device_energy (timestamp, device_name, power_kw, energy_kwh, device_id)
            VALUES (?, ?, ?, ?, ?)
        """, (ts, dh['device_code'], round(dh['value'] * 1000 / 24, 2), dh['value'], dh['device_id']))

    conn.commit()
    conn.close()
    return written


def run_simulation(args):
    """主流程"""
    month = args.month
    mode = args.mode

    # 构建月度总量字典
    totals = {}
    for key in ENERGY_TYPES:
        val = getattr(args, key, None)
        if val is not None:
            totals[key] = val

    if not totals:
        print('  ⚠️ 未指定任何能源数据')
        return

    is_new_data = (mode == 'new')

    daily_all = []
    device_all = []
    hour_all = []

    for energy_type, total in totals.items():
        if total is None or total == 0:
            continue
        unit = ENERGY_TYPES[energy_type]["unit"]
        print(f'\n  → {energy_type} ({unit}): 总量={total}')
        
        # 时间段分拆
        daily_vals, days = decompose_month(total, energy_type, month, is_new_data)
        print(f'    → {days}天, 日均{total/days:.1f}')
        
        # 设备分摊（仅电力）
        if energy_type == 'electricity':
            device_data = allocate_to_devices(daily_vals, month)
            device_all.extend(device_data)
            unique_devices = set(d['device_id'] for d in device_data)
            print(f'    → 分摊到 {len(unique_devices)} 台设备')
        
        # 构建 daily_energy 记录
        for day_idx, val in enumerate(daily_vals):
            day = day_idx + 1
            date_str = f"{month}-{day:02d}"
            daily_all.append({
                'date': date_str,
                'energy_type': energy_type,
                'value': round(val, 2),
                'generation_method': 'actual' if is_new_data else 'simulated',
            })
            
            # 生成小时级数据
            dt = datetime(int(month[:4]), int(month[5:7]), day)
            is_weekend = dt.weekday() >= 5
            h_data = gen_hourly_from_daily(val, date_str, energy_type, is_weekend)
            
            for h in h_data:
                hour_all.append({
                    'date': date_str,
                    'hour': h['hour'],
                    'energy_type': energy_type,
                    'value': h['value'],
                    'device_id': None,
                    'device_code': None,
                })

    # 写库
    gen_method = 'actual' if is_new_data else 'simulated'
    written = write_to_db(daily_all, device_all, hour_all, gen_method)
    
    total_val = sum(d['value'] for d in daily_all)
    print(f'\n  ✅ 写入完成: daily_energy {written}条, device_energy {len(device_all)*24}条')
    print(f'    能源总值: {total_val:.1f}')
    print(f'    模式: {"新数据" if is_new_data else "上月数据+偏移"}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="知微能碳 — 数据模拟更新引擎 v2")
    parser.add_argument('--mode', type=str, default='new', choices=['new', 'auto'],
                        help='模式: new=新数据, auto=自动(有数据走new/无数据走old)')
    parser.add_argument('--month', type=str, default=datetime.now().strftime('%Y-%m'),
                        help='目标月份 YYYY-MM')
    
    # 10种能源类型参数
    parser.add_argument('--electricity', type=float, help='电力 (kWh)')
    parser.add_argument('--water', type=float, help='水 (吨)')
    parser.add_argument('--natural-gas', type=float, default=0, help='天然气 (m³)')
    parser.add_argument('--diesel', type=float, help='柴油 (L)')
    parser.add_argument('--gasoline', type=float, help='汽油 (L)')
    parser.add_argument('--lpg', type=float, default=0, help='LPG液化气 (kg)')
    parser.add_argument('--steam', type=float, default=0, help='蒸汽 (吨)')
    parser.add_argument('--heat', type=float, default=0, help='热力 (GJ)')
    parser.add_argument('--coal', type=float, default=0, help='煤炭 (吨)')
    parser.add_argument('--compressed-air', type=float, default=0, help='压缩空气 (m³)')
    
    parser.add_argument('--output', type=str, choices=['json', 'db', 'both'], default='db',
                        help='输出方式: json/db/both')
    parser.add_argument('--quality', type=str, default='estimated',
                        choices=['actual', 'estimated', 'simulated'],
                        help='数据质量标记')
    
    args = parser.parse_args()
    
    print('=' * 50)
    print('知微能碳 — 数据模拟更新引擎 v2')
    print('=' * 50)
    
    # auto 模式判断
    if args.mode == 'auto':
        has_new = check_data_source()
        if has_new:
            print('📋 检测到新数据源 → 采用最新数据')
            # 自动获取上月数据
            last_data = get_last_month_data(args.month)
            if last_data:
                for etype, data in last_data.items():
                    setattr(args, etype, data['total'])
        else:
            print('📋 无新数据 → 使用上月数据+随机偏移')
            args.mode = 'new'  # 先按new走，但没有数据
    
    run_simulation(args)
    print('=' * 50)
