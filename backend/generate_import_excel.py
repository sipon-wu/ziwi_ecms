"""知微能碳 — 全量Excel用例数据生成器 v2
按实际模板列结构填充数据，从模板第4行开始写，导入后验证全站页面
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_import import generate_template_excel, import_excel, db
from datetime import datetime, timedelta

random.seed(42)
IMPORT_DIR = os.path.join(os.path.dirname(__file__), 'import_data')
os.makedirs(IMPORT_DIR, exist_ok=True)

WORK_CENTERS = [
    ('001-喷油螺杆大机组','production_unit',250,'1号厂房'),
    ('002-无油螺杆组','production_unit',180,'2号厂房'),
    ('003-喷油螺杆小机组','production_unit',120,'2号厂房'),
    ('004-移动大机组','production_unit',80,'3号厂房'),
    ('005-移动小机组','production_unit',60,'3号厂房'),
    ('006-离心机组','production_unit',200,'1号厂房'),
    ('007-活塞机组','production_unit',75,'2号厂房'),
    ('008-制氮制氧机组','aux_unit',150,'空压站'),
    ('009-真空泵机组','aux_unit',45,'3号厂房'),
    ('010-无油涡旋机组','production_unit',90,'2号厂房'),
]
TN = datetime.now()

def clean():
    conn = db(); c = conn.cursor()
    for t in ['energy_records','device_energy','production_data','alarms','alarm_rules',
              'supplier_carbon_data','suppliers','supplier_users','carbon_quotas',
              'carbon_trade_prices','ccer_projects',
              'optimization_tasks','emission_factors','org_structure',
              'device_groups','system_config','data_sources']:
        try: c.execute(f'DELETE FROM {t}')
        except: pass
    conn.commit(); conn.close()
    print('✅ 数据库已清空')

def do(name, data):
    wb = generate_template_excel(name)
    if not wb: return print(f'  ❌ {name}: 模板生成失败')
    ws = wb.active
    for i, row in enumerate(data, start=5):
        for j, v in enumerate(row, start=1):
            cell = ws.cell(row=i, column=j)
            try: cell.value = v
            except: pass
    fp = os.path.join(IMPORT_DIR, f'用例_{name}.xlsx')
    wb.save(fp)
    r, e = import_excel(fp, name)
    status = f'导入{r.get("imported","?")}行' if not e else f'失败: {e}'
    print(f'  {"✅" if not e else "❌"} {name}: {status}')

print('='*50)
print('生成完整用例数据（按实际模板列结构）')
clean()

# ===== 1. 基础配置 =====
print('\n📋 第1批：基础配置')
do('device_groups', [[n, t, '', r, l, f'{n} - {t}'] for n,t,r,l in WORK_CENTERS])
do('org_structure', [
    ['总装车间','',1],['一车间','总装车间',2],['二车间','总装车间',2],
    ['三车间','总装车间',2],['空压站','总装车间',2],['制造中心','',1],['质量部','',1]])
do('emission_factors', [
    ['电力排放因子',0.5566,'生态环境部2024','2026'],
    ['天然气排放因子',2.16,'IPCC 2024','2026'],
    ['蒸汽排放因子',276.0,'行业平均','2026'],
    ['柴油排放因子',2.63,'IPCC 2024','2026'],
    ['汽油排放因子',2.30,'IPCC 2024','2026'],
    ['煤炭排放因子',2060.0,'IPCC 2024','2026']])
do('alarm_rules', [
    ['001-喷油螺杆大机组','功率',240,'gt','warning','功率接近满载',1],
    ['002-无油螺杆组','功率',170,'gt','warning','功率接近满载',1],
    ['008-制氮制氧机组','电流',280,'gt','error','电流异常升高',1],
    ['009-真空泵机组','功率',40,'gt','warning','真空泵负载偏高',1]])
print('\n📋 系统配置（直接插入）')
sys_cfgs = [
    ('peak_start','08:00','峰时开始'),('peak_end','20:00','峰时结束'),
    ('emission_factor','0.5566','电网排放因子(kgCO2/kWh)'),
    ('carbon_budget_monthly','350','月度碳预算(吨)'),
    ('refresh_interval','10','实时刷新间隔(秒)'),
    ('page_size','20','默认分页大小'),
    ('alarm_retention_days','90','告警保留天数')]
conn = db(); c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS system_config (id INTEGER PRIMARY KEY AUTOINCREMENT, config_key VARCHAR(100) UNIQUE, config_value TEXT, description TEXT)")
c.execute("DELETE FROM system_config")
for k,v,d in sys_cfgs:
    c.execute("INSERT OR IGNORE INTO system_config (config_key, config_value, description) VALUES (?,?,?)", (k,v,d))
conn.commit(); conn.close()
print(f'  ✅ system_config: {len(sys_cfgs)} 条')

do('data_sources', [
    ['peak_start','08:00','峰时开始','',''],
    ['peak_end','20:00','峰时结束','',''],
    ['emission_factor','0.5566','电网排放因子(kgCO2/kWh)','',''],
    ['carbon_budget_monthly','350','月度碳预算(吨)','',''],
    ['refresh_interval','10','实时刷新间隔(秒)','',''],
    ['page_size','20','默认分页大小','',''],
    ['alarm_retention_days','90','告警保留天数','','']])
do('data_sources', [
    ['本地Excel导入','excel','{}','active','手动上传Excel文件'],
    ['生产系统API','http','{}','active','自动从MES系统同步'],
    ['手工录入','manual','{}','active','临时手工录入数据']])

# ===== 2. 业务数据 =====
print('\n📋 第2批：业务数据')
pr_data = []
for d in range(29,-1,-1):
    dt = (TN - timedelta(days=d)).strftime('%Y-%m-%d')
    u = random.randint(80,200)
    pr_data.append([dt, u, round(u*0.35+random.random()*2,2), '正常生产'])
do('production_data', pr_data)

# 能耗时序：近8天5分钟间隔（含今天）
er_data = []
for d in range(8,-1,-1):
    dt = (TN - timedelta(days=d))
    wd = dt.weekday() >= 5
    dt = dt.strftime('%Y-%m-%d')
    for h in range(24):
        for m in range(0,60,5):
            ts = f'{dt} {h:02d}:{m:02d}'
            if wd: bp=1800+random.random()*300
            elif 8<=h<12: bp=3200+random.random()*500
            elif 12<=h<13: bp=2500+random.random()*300
            elif 13<=h<18: bp=3400+random.random()*600
            elif 18<=h<22: bp=2200+random.random()*400
            else: bp=1800+random.random()*300
            p = round(bp+(random.random()-0.5)*200,2)
            pf = round(0.90+random.random()*0.08,2)
            er_data.append([ts, round(p*5/60,2), p, pf, round(49.8+random.random()*0.4,2)])
do('energy_records', er_data)

# 设备能耗：近7天8-18点
de_data = []
for d in range(7,0,-1):
    dt = (TN - timedelta(days=d))
    wd = dt.weekday() >= 5
    dt = dt.strftime('%Y-%m-%d')
    for h in range(8,18):
        if wd and random.random()<0.6: continue
        for m in range(0,60,5):
            ts = f'{dt} {h:02d}:{m:02d}'
            for n,_,rt,_ in WORK_CENTERS:
                ld = 0.4+random.random()*0.45 if not wd else 0.15+random.random()*0.2
                pw = round(rt*ld,2)
                de_data.append([ts, n, pw, round(pw*5/60,2), round(pw/(1.732*0.38*0.9),1),
                                round(375+random.random()*10,1), round(0.85+random.random()*0.12,2)])
do('device_energy', de_data)

do('carbon_quotas', [[oid, y, random.randint(5000,30000), round(random.randint(5000,30000)*random.random(),2)] for oid in range(1,5) for y in [2025,2026]])
do('optimization_tasks', [
    ['空压机群控优化','001-喷油螺杆大机组',185000,'执行中'],
    ['无油螺杆效率提升','002-无油螺杆组',96000,'待执行'],
    ['离心机组变频改造','006-离心机组',220000,'执行中'],
    ['车间照明LED改造','总装车间',42000,'已完成'],
    ['制氮机余热回收','008-制氮制氧机组',150000,'待执行'],
    ['真空泵待机节能','009-真空泵机组',35000,'待执行']])

# ===== 3. 碳业务 =====
print('\n📋 第3批：碳业务')
price_data = []
bp = 55
for d in range(1,16):
    price_data.append([f'2026-06-{d:02d}', round(bp+random.random()*8,2), random.randint(20000,50000)])
do('carbon_trade_prices', price_data)
do('ccer_projects', [
    ['屋顶光伏项目','可再生能源','已备案',850,75],
    ['空压机余热回收','节能增效','开发中',420,40],
    ['厂区绿化碳汇','碳汇','已核证',180,100],
    ['制氮机节能改造','节能增效','已备案',310,60]])
do('energy_flow_config', [
    ['购入电力','空压机组','28%'],['购入电力','机加工设备','55%'],
    ['购入电力','测试台','8%'],['购入电力','辅助及照明','9%'],
    ['空压机组','有效压缩空气','80%'],['空压机组','散热损失','20%'],
    ['机加工设备','有效加工动能','70%'],['机加工设备','摩擦损失','30%']])

# ===== 4. 供应商 =====
print('\n📋 第4批：供应商')
do('suppliers', [
    ['上海XX钢材有限公司','SHTEEL001','张三','zhang@steel.com','华东'],
    ['江苏YY精密铸造','JSCAST002','李四','li@cast.com','华东'],
    ['浙江ZZ电机科技','ZJMOTOR003','王五','wang@motor.com','华东'],
    ['安徽WW密封件','AHSEAL004','赵六','zhao@seal.com','华东'],
    ['山东BB轴承','SDBEAR005','钱七','qian@bearing.com','华北']])
sm_data = []
for c in ['SHTEEL001','JSCAST002','ZJMOTOR003','AHSEAL004','SDBEAR005']:
    for m in range(1,6):
        sm_data.append([c, f'2026-{m:02d}', random.randint(8000,20000), round(random.uniform(80000,180000),2),
                        round(random.uniform(2000,8000),2), round(random.uniform(100,500),2),
                        round(random.uniform(1000,5000),2), round(random.uniform(500,5000),2),
                        0, 0, 0, '正常生产'])
do('supplier_monthly_data', sm_data)

print('\n' + '='*50)
print('✅ 全部完成！')
print(f'   用例Excel已保存至: {IMPORT_DIR}')
print('='*50)
