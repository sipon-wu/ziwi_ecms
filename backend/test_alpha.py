"""知微能碳 Alpha 测试脚本 — 自动执行并清理"""
import sys, os, json, sqlite3, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

HOST = "http://localhost:8090"
passed = 0
failed = 0
results = []


def test(name, func):
    global passed, failed
    try:
        func()
        results.append(f"  ✅ {name}")
        passed += 1
    except AssertionError as e:
        results.append(f"  ❌ {name} — {e}")
        failed += 1
    except Exception as e:
        results.append(f"  ❌ {name} — 异常: {e}")
        failed += 1


def req(method, path, **kwargs):
    import urllib.request
    url = f"{HOST}{path}"
    data = None
    headers = {"Content-Type": "application/json"} if method in ("POST", "PUT") else {}
    if "data" in kwargs:
        data = json.dumps(kwargs["data"]).encode()
    if "token" in kwargs:
        headers["Authorization"] = f"Bearer {kwargs['token']}"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r)
        return json.loads(resp.read().decode())
    except urllib.request.HTTPError as e:
        return json.loads(e.read().decode()) if e.code != 500 else {"code": 1}


# ========== 清理函数 ==========
def cleanup():
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "energy_data.db"))
    c = conn.cursor()
    for table in ["data_dict_types", "data_dict_items", "suppliers", "supplier_users"]:
        try:
            c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if c.fetchone():
                c.execute(f"DELETE FROM {table} WHERE supplier_code LIKE 'TEST_%' OR dict_code LIKE 'TEST_%'")
        except:
            pass
    # Also cleanup test suppliers
    try:
        c.execute("DELETE FROM suppliers WHERE supplier_code LIKE 'TEST_%'")
        c.execute("DELETE FROM supplier_users WHERE supplier_id NOT IN (SELECT id FROM suppliers)")
    except:
        pass
    conn.commit()
    conn.close()
    print("  🧹 测试数据已清理")


# ========== A. 认证测试 ==========
print("\n📋 A. 认证测试")
TOKEN = None


def login_ok():
    global TOKEN
    d = req("POST", "/api/auth/login", data={"username": "admin", "password": "admin123"})
    assert d["code"] == 0, f"登录失败: {d.get('message','')}"
    assert "token" in d["data"]
    TOKEN = d["data"]["token"]


def login_bad():
    d = req("POST", "/api/auth/login", data={"username": "admin", "password": "wrong"})
    assert d["code"] != 0, "错误密码应返回非0 code"


def get_me():
    d = req("GET", "/api/auth/me", token=TOKEN)
    assert d["code"] == 0
    assert d["data"]["username"] == "admin"


test("A2 正确登录返回Token", login_ok)
test("A3 错误密码提示", login_bad)
test("A4 获取当前用户信息", get_me)


# ========== B. 驾驶舱测试 ==========
print("\n📋 B. 驾驶舱")


def dashboard_summary():
    d = req("GET", "/api/dashboard/summary")
    assert d["code"] == 0
    assert "today_kwh" in d["data"]


def dashboard_trend():
    d = req("GET", "/api/dashboard/trend")
    assert d["code"] == 0
    assert "current_power" in d["data"]


def dashboard_ranking():
    d = req("GET", "/api/dashboard/ranking")
    assert d["code"] == 0
    assert "ranking" in d["data"]


test("B1 驾驶舱KPI", dashboard_summary)
test("B2 趋势图数据", dashboard_trend)
test("B3 设备排名", dashboard_ranking)


# ========== C. 数据监控 ==========
print("\n📋 C. 数据监控")


def monitoring_current():
    d = req("GET", "/api/monitoring/current")
    assert d["code"] == 0


def monitoring_alarms():
    d = req("GET", "/api/monitoring/alarms?status=active")
    assert d["code"] == 0


def alarm_rules():
    d = req("GET", "/api/monitoring/alarm_rules")
    assert d["code"] == 0


test("C1 实时数据", monitoring_current)
test("C2 报警列表", monitoring_alarms)
test("C3 报警规则", alarm_rules)


# ========== D. 能耗分析 ==========
print("\n📋 D. 能耗分析")


def energy_intensity():
    d = req("GET", "/api/analysis/energy_intensity")
    assert d["code"] == 0


def benchmark():
    d = req("GET", "/api/analysis/benchmark?device_group=compressor")
    assert d["code"] == 0


def energy_flow():
    d = req("GET", "/api/analysis/energy_flow")
    assert d["code"] == 0


def balance():
    d = req("GET", "/api/analysis/balance")
    assert d["code"] == 0


test("D1 消费量及强度", energy_intensity)
test("D2 能效对标", benchmark)
test("D3 能流桑基图", energy_flow)
test("D4 能效平衡", balance)


# ========== E. 碳管理 ==========
print("\n📋 E. 碳管理")


def carbon_accounting():
    d = req("GET", "/api/carbon/accounting")
    assert d["code"] == 0


def carbon_supply():
    d = req("GET", "/api/carbon/supply")
    assert d["code"] == 0


def carbon_budget():
    d = req("GET", "/api/carbon/budget")
    assert d["code"] == 0


test("E1 碳排放核算", carbon_accounting)
test("E2 供应链碳管理", carbon_supply)
test("E3 碳预算管理", carbon_budget)


# ========== F. 大屏看板 ==========
print("\n📋 F. 大屏看板")


def bigscreen_summary():
    d = req("GET", "/api/bigscreen/summary")
    assert d["code"] == 0


def bigscreen_trend():
    d = req("GET", "/api/bigscreen/energy_trend")
    assert d["code"] == 0


def bigscreen_structure():
    d = req("GET", "/api/bigscreen/energy_structure")
    assert d["code"] == 0


def bigscreen_carbon():
    d = req("GET", "/api/bigscreen/carbon_overview")
    assert d["code"] == 0


def bigscreen_device():
    d = req("GET", "/api/bigscreen/device_status")
    assert d["code"] == 0


def bigscreen_alarm():
    d = req("GET", "/api/bigscreen/alarm_summary")
    assert d["code"] == 0


def bigscreen_ranking():
    d = req("GET", "/api/bigscreen/ranking")
    assert d["code"] == 0


def heartbeat():
    d = req("GET", "/api/heartbeat")
    assert d["code"] == 0
    assert d["data"]["status"] == "running"


test("F1 大屏KPI总览", bigscreen_summary)
test("F2 大屏能耗趋势", bigscreen_trend)
test("F3 大屏能耗结构", bigscreen_structure)
test("F4 大屏碳排总览", bigscreen_carbon)
test("F5 大屏设备状态", bigscreen_device)
test("F6 大屏报警汇总", bigscreen_alarm)
test("F7 大屏能耗排名", bigscreen_ranking)
test("F8 系统心跳", heartbeat)


# ========== G. 数据导入 ==========
print("\n📋 G. 数据导入")


def import_tables():
    d = req("GET", "/api/import/tables")
    assert d["code"] == 0
    assert len(d["data"]["tables"]) == 15, f"预期15个模板，实际{len(d['data']['tables'])}"


test("G1 导入模板列表(15个)", import_tables)


# ========== H. 数据字典 ==========
print("\n📋 H. 数据字典")


def create_dict_type():
    d = req("POST", "/api/dict/types", data={
        "dict_code": "TEST_UNIT_TYPE",
        "dict_name": "测试-耗能单元类型",
        "description": "测试用"
    })
    assert d["code"] == 0, f"创建失败: {d}"


test("H1 新增字典类型(可清理)", create_dict_type)


# ========== I. 供应商管理 ==========
print("\n📋 I. 供应商管理")


def create_supplier():
    d = req("POST", "/api/admin/suppliers", data={
        "supplier_code": "TEST_001",
        "supplier_name": "测试供应商",
        "contact_person": "张三",
    })
    assert d["code"] == 0
    assert "password" in d["data"]


def list_suppliers():
    d = req("GET", "/api/admin/suppliers")
    assert d["code"] == 0


test("I1 新增供应商(自动生成账号密码)", create_supplier)
test("I2 列出供应商", list_suppliers)


# ========== 结果输出 ==========
print("\n" + "=" * 50)
print(f"📊 测试完成: {passed} 通过 / {failed} 失败 / 共 {passed + failed} 项")

if failed > 0:
    print("\n❌ 失败的测试:")
    for r in results:
        if "❌" in r:
            print(r)
else:
    print("\n🎉 全部测试通过!")

print("\n🧹 正在清理测试数据...")
cleanup()
print("✅ 清理完成")
