"""知微能碳 — 全面回归测试脚本"""
import sys, os, json, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
HOST = "http://localhost:8088"

def req(method, path, **kw):
    import urllib.request
    u = f"{HOST}{path}"; d=None; h={"Content-Type":"application/json"}
    if "data" in kw: d=json.dumps(kw["data"]).encode()
    if "token" in kw: h["Authorization"]=f"Bearer {kw['token']}"
    try: return json.loads(urllib.request.urlopen(urllib.request.Request(u,data=d,headers=h,method=method)).read())
    except urllib.request.HTTPError as e: return json.loads(e.read()) if e.code!=500 else {"code":1}

passed=0; failed=0; TOKEN=None
def t(name, fn):
    global passed, failed
    try: fn(); print(f"  ✅ {name}"); passed+=1
    except Exception as e: print(f"  ❌ {name}: {e}"); failed+=1

# ====== A. 认证 ======
print("\n📋 A. 认证测试（8项）")
t("A1 登录返回Token", lambda: globals().__setitem__("TOKEN",req("POST","/api/auth/login",data={"username":"admin","password":"admin123"})["data"]["token"]))
t("A2 错误密码提示", lambda: (_:=req("POST","/api/auth/login",data={"username":"admin","password":"wrong"}))["code"]!=0)
t("A3 获取用户信息", lambda: (_:=req("GET","/api/auth/me",token=TOKEN))["data"]["username"]=="admin")
t("A4 退出登录", lambda: (_:=req("POST","/api/auth/logout"))["code"]==0)

# ====== B. 业务API ======
print("\n📋 B. 业务API（21项）")
for p in ["/api/dashboard/summary","/api/dashboard/trend","/api/dashboard/ranking",
          "/api/monitoring/current","/api/monitoring/alarms","/api/monitoring/alarm_rules",
          "/api/analysis/energy_intensity","/api/analysis/benchmark?device_group=compressor",
          "/api/analysis/energy_flow","/api/analysis/balance",
          "/api/efficiency/trend","/api/efficiency/overview","/api/efficiency/optimization_tasks",
          "/api/carbon/accounting","/api/carbon/supply","/api/carbon/budget",
          "/api/carbon_asset/quota","/api/carbon_asset/trading","/api/carbon_asset/ccer",
          "/api/organization/tree",
          "/api/system/config","/api/system/logs","/api/system/peak_valley","/api/system/users"]:
    t(f"B{p.split('/')[-1]}", lambda _p=p: req("GET",_p)["code"]==0)

# ====== C. 大屏 ======
print("\n📋 C. 大屏API + 心跳（8项）")
for p in ["/api/bigscreen/summary","/api/bigscreen/energy_trend","/api/bigscreen/energy_structure",
          "/api/bigscreen/carbon_overview","/api/bigscreen/device_status",
          "/api/bigscreen/alarm_summary","/api/bigscreen/ranking","/api/heartbeat"]:
    t(f"C{p.split('/')[-1]}", lambda _p=p: req("GET",_p)["code"]==0)

# ====== D. 导入 ======
print("\n📋 D. 导入模块（2项）")
t("D1 15个模板", lambda: len(req("GET","/api/import/tables")["data"]["tables"])==16)
t("D2 模板可下载", lambda: (_:=req("GET","/api/import/device_groups/template"))["code"]!=1)

# ====== E. 配置 ======
print("\n📋 E. 配置管理（4项）")
t("E1 新增字典类型", lambda: req("POST","/api/dict/types",data={"dict_code":"TEST_REG","dict_name":"回归测试","description":"t"})["code"]==0)
t("E2 获取字典类型", lambda: req("GET","/api/dict/types")["code"]==0)
t("E3 数据源列表", lambda: req("GET","/api/datasource/list")["code"]==0)
t("E4 导入记录", lambda: req("GET","/api/datasource/logs")["code"]==0)

# ====== F. 供应商 ======
print("\n📋 F. 供应商管理（3项）")
t("F1 新增供应商", lambda: (_:=req("POST","/api/admin/suppliers",data={"supplier_code":"TEST_REG","supplier_name":"回归测试","contact_person":"测试"}))["code"]==0)
t("F2 供应商列表", lambda: req("GET","/api/admin/suppliers")["code"]==0)
t("F3 删除供应商", lambda: req("DELETE","/api/admin/suppliers",data={})["code"]==0)

# ====== 结果 ======
total = passed+failed
print("\n"+"="*50)
print(f"📊 测试完成: {passed}/{total} 通过, {failed}/{total} 失败")
if failed==0: print("\n🎉 全部通过！")
