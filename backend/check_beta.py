"""知微能碳 Beta — 数据完整性检查"""
import sqlite3
conn = sqlite3.connect('D:/工业元/数云_新质力/ziwi_project_dna/backend/energy_data.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print('📊 数据库数据完整性检查')
print('='*60)
total = 0
tables = ['energy_records','device_energy','production_data','device_groups','work_centers',
          'devices','alarms','alarm_rules','emission_factors','carbon_quotas',
          'optimization_tasks','org_structure','suppliers','supplier_carbon_data',
          'carbon_trade_prices','ccer_projects']
for t in sorted(tables):
    try:
        cnt = c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        total += cnt
        print(f'  {t:30s} {cnt:>6} 行')
    except:
        print(f'  {t:30s} {"—":>6} (表不存在)')
print(f'  {"-"*40}')
print(f'  {"总计":30s} {total:>6} 行')

d = c.execute("SELECT SUM(total_energy_kwh) FROM energy_records WHERE timestamp LIKE '2026-06-09%'").fetchone()[0] or 0
print(f'\n📈 今日能耗: {d:.2f} kWh')

print(f'\n🏭 供应商碳评价:')
for r in c.execute('''SELECT s.supplier_name, sc.carbon_score, sc.carbon_level 
    FROM supplier_carbon_data sc JOIN suppliers s ON s.supplier_code=sc.supplier_code
    WHERE sc.id IN (SELECT MAX(id) FROM supplier_carbon_data GROUP BY supplier_code)
    ORDER BY sc.carbon_score DESC''').fetchall():
    print(f'  {r["supplier_name"]:20s} 评分={r["carbon_score"]} 等级={r["carbon_level"]}')

has = c.execute('SELECT COUNT(*) FROM device_energy WHERE device_id IS NOT NULL').fetchone()[0]
total_de = c.execute('SELECT COUNT(*) FROM device_energy').fetchone()[0]
print(f'\n🔗 device_energy: {has}/{total_de} 条已关联设备ID')

print(f'\n🏭 设备按工作中心分布:')
for r in c.execute('''SELECT wc.name, COUNT(d.id) as cnt FROM work_centers wc 
    LEFT JOIN devices d ON d.work_center_id = wc.id WHERE wc.code LIKE "WC-%" GROUP BY wc.id ORDER BY wc.id''').fetchall():
    print(f'  {r["name"]:20s} {r["cnt"]} 台设备')

conn.close()
