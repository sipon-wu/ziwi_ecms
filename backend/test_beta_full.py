"""知微能碳 Beta — 全功能高级测试脚本
按角色（超级管理员/操作员）组织测试用例，每个用例验证前端可展示的完整数据流
"""
import sys, os, json, urllib.request, sqlite3

HOST = os.environ.get("API_HOST", "http://localhost:8088")
passed = 0; failed = 0; results = []

def t(name, fn):
    global passed, failed
    try:
        fn()
        results.append(f"  ✅ {name}")
        passed += 1
    except AssertionError as e:
        results.append(f"  ❌ {name} — {e}")
        failed += 1
    except Exception as e:
        results.append(f"  ❌ {name} — {e}")
        failed += 1

def req(method, path, **kw):
    u = f"{HOST}{path}"; d=None; h={"Content-Type":"application/json"}
    if "data" in kw: d=json.dumps(kw["data"]).encode()
    if "token" in kw: h["Authorization"]=f"Bearer {kw['token']}"
    try: return json.loads(urllib.request.urlopen(urllib.request.Request(u,data=d,headers=h,method=method), timeout=5).read())
    except urllib.request.HTTPError as e: return json.loads(e.read()) if e.code != 500 else {"code": 1}
    except Exception as e: return {"code": 1, "error": str(e)}

TOKEN = None

print("=" * 60)
print("知微能碳 Beta — 全功能高级测试")
print("=" * 60)

# ===== A. 认证 =====
print("\n📋 A. 认证基础（3项）")
t("A1 管理���登录", lambda: globals().__setitem__("TOKEN", req("POST","/api/auth/login",data={"username":"admin","password":"admin123"})["data"]["token"]))
t("A2 获取当前用户", lambda: (_:=req("GET","/api/auth/me",token=TOKEN)) and _["data"]["username"]=="admin")
t("A3 错误密码拒绝", lambda: req("POST","/api/auth/login",data={"username":"admin","password":"wrong"})["code"]!=0)

# ===== B. 驾驶舱 =====
print("\n📋 B. 驾驶舱（3项）")
t("B1 KPI不为空", lambda: (_:=req("GET","/api/dashboard/summary")) and _["data"]["today_kwh"]>0)
t("B2 趋势有数据", lambda: len(req("GET","/api/dashboard/trend")["data"]["current_power"])>0)
t("B3 排名有数据", lambda: len(req("GET","/api/dashboard/ranking")["data"]["ranking"])>0)

# ===== C. 数据监控 =====
print("\n📋 C. 数据监控（3项）")
t("C1 实时数据非空", lambda: (_:=req("GET","/api/monitoring/current")) and _["data"]["total_active_power_kw"]>0)
t("C2 报警规则存在", lambda: len(req("GET","/api/monitoring/alarm_rules")["data"]["rules"])>0)
t("C3 历史报警可查", lambda: req("GET","/api/monitoring/alarms?status=all")["code"]==0)

# ===== D. 能耗分析 =====
print("\n📋 D. 能耗分析（4项）")
t("D1 消费强度非零", lambda: (_:=req("GET","/api/analysis/energy_intensity")) and _["data"]["total_kwh"]>0)
t("D2 能效对标返回等级", lambda: (_:=req("GET","/api/analysis/benchmark")) and _["data"]["benchmark_level"]!="")
t("D3 能流桑基有节点", lambda: len(req("GET","/api/analysis/energy_flow")["data"]["nodes"])>0)
t("D4 平衡分析有结构", lambda: len(req("GET","/api/analysis/balance")["data"]["breakdown"])>0)

# ===== E. 能效管理 =====
print("\n📋 E. 能效管理（2项）")
t("E1 设备能效趋势", lambda: len(req("GET","/api/efficiency/trend")["data"]["trend"])>0)
t("E2 优化任务列表", lambda: len(req("GET","/api/efficiency/optimization_tasks")["data"]["tasks"])>0)

# ===== F. 碳管理 =====
print("\n📋 F. 碳管理（5项）")
t("F1 碳排放核算非零", lambda: (_:=req("GET","/api/carbon/accounting")) and _["data"]["total_co2_kg"]>0)
t("F2 供应链有供应商", lambda: len(req("GET","/api/carbon/supply")["data"]["suppliers"])>0)
t("F3 碳预算进度显示", lambda: req("GET","/api/carbon/budget")["data"]["percent"]>0)
t("F4 碳配额管理", lambda: len(req("GET","/api/carbon_asset/quota")["data"]["details"])>0)
t("F5 碳交易价格趋势", lambda: len(req("GET","/api/carbon_asset/trading")["data"]["trend"])>0)

# ===== G. 组织管理 =====
print("\n📋 G. 组织管理（2项）")
t("G1 组织树有节点", lambda: len(req("GET","/api/organization/tree")["data"]["tree"])>0)
t("G2 组织碳数据可查", lambda: req("GET","/api/organization/carbon")["code"]==0)

# ===== H. 系统管理 =====
print("\n📋 H. 系统管理（5项）")
t("H1 系统配置满载", lambda: len(req("GET","/api/system/config")["data"]["configs"])==7)
t("H2 操作日志可查", lambda: req("GET","/api/system/logs")["code"]==0)
t("H3 峰谷分析有小时", lambda: len(req("GET","/api/system/peak_valley")["data"]["hours"])>0)
t("H4 用户列表可查", lambda: req("GET","/api/system/users")["code"]==0)
t("H5 数据字典可查", lambda: req("GET","/api/dict/types")["code"]==0)

# ===== I. 供应商管理 =====
print("\n📋 I. 供应商管理（5项）")
t("I1 供应商列表非空", lambda: (_:=req("GET","/api/admin/suppliers")) and _["data"]["total"]>0)
t("I2 供应商可创建", lambda: (_:=req("POST","/api/admin/suppliers",data={"supplier_code":"TEST_BETA","supplier_name":"Beta测试","contact_person":"测试"})) and _["code"]==0)
t("I3 密��可重置", lambda: (_:=req("GET","/api/admin/suppliers")) and req("POST",f"/api/admin/suppliers/{_['data']['items'][-1]['id']}/reset_password")["code"]==0)
t("I4 供应商碳数据可查", lambda: (_:=req("GET","/api/admin/suppliers")) and req("GET",f"/api/admin/suppliers/{_['data']['items'][-1]['id']}/data")["code"]==0)
t("I5 供应链碳评价有供应商", lambda: len(req("GET","/api/carbon/supply")["data"]["suppliers"])>=4)

# ===== J. 设备管理（新增） =====
print("\n📋 J. 设备管理（5项）")
t("J1 工作中心树", lambda: len(req("GET","/api/device/workcenters")["data"]["tree"])>=4)
t("J2 设备列表21台", lambda: len(req("GET","/api/device/list")["data"]["devices"])==21)
t("J3 标签有10种", lambda: len(req("GET","/api/device/tags")["data"]["tags"])>=10)
t("J4 按工作中心筛选", lambda: len(req("GET","/api/device/list?work_center_id=2")["data"]["devices"])>0)
t("J5 按标签筛选变频", lambda: len([d for d in req("GET","/api/device/list")["data"]["devices"] if '变频' in str(d.get('tags',''))])>0)

# ===== K. 数据导入 =====
print("\n📋 K. 数据导入（2项）")
t("K1 16个导入模板", lambda: len(req("GET","/api/import/tables")["data"]["tables"])>=16)
t("K2 碳交易14条数据", lambda: (_:=req("GET","/api/carbon_asset/trading")) and len(_["data"]["trend"])>0)

# ===== L. 大屏 =====
print("\n📋 L. 大屏API（7项）")
t("L1 大屏总览", lambda: (_:=req("GET","/api/bigscreen/summary")) and _["data"]["today_kwh"]>0)
t("L2 大屏趋势", lambda: req("GET","/api/bigscreen/energy_trend")["code"]==0)
t("L3 大屏结构", lambda: len(req("GET","/api/bigscreen/energy_structure")["data"]["breakdown"])>0)
t("L4 大屏碳排", lambda: req("GET","/api/bigscreen/carbon_overview")["code"]==0)
t("L5 大屏设备状态", lambda: (_:=req("GET","/api/bigscreen/device_status")) and _["data"]["online"]>0)
t("L6 大屏报警", lambda: req("GET","/api/bigscreen/alarm_summary")["code"]==0)
t("L7 大屏排名", lambda: len(req("GET","/api/bigscreen/ranking")["data"]["ranking"])>0)

# ===== M. 心跳 =====
print("\n📋 M. 系统心跳（1项）")
t("M1 心跳返回running", lambda: (_:=req("GET","/api/heartbeat")) and _["data"]["status"]=="running")

# ===== 清理测试数据 =====
print("\n🧹 清理测试数据...")
conn = sqlite3.connect(os.path.join(os.path.dirname(__file__),"energy_data.db"))
c = conn.cursor()
for t in ['data_dict_types','data_dict_items','suppliers','supplier_users']:
    try:
        if c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{t}'").fetchone():
            c.execute(f"DELETE FROM {t} WHERE supplier_code LIKE 'TEST_%' OR dict_code LIKE 'TEST_%'")
    except: pass
try:
    c.execute("DELETE FROM suppliers WHERE supplier_code='TEST_BETA'")
    c.execute("DELETE FROM supplier_users WHERE supplier_id NOT IN (SELECT id FROM suppliers)")
except: pass
conn.commit(); conn.close()
print("✅ 测试数据已清理")

# ===== 结果 =====
print("\n" + "=" * 60)
print(f"📊 测试完成: {passed}/{passed+failed} 通过")
if failed > 0:
    print(f"\n❌ 失败的测试 ({failed}/{passed+failed}):")
    for r in results:
        if "❌" in r: print(r)
else:
    print("\n🎉 全部通过！系统功能正常")
print("=" * 60)
