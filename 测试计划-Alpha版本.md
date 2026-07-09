# 知微能碳管理系统 — Alpha 测试计划

> 日期：2026-06-07 | 测试范围：Alpha 版本所有功能

---

## 一、测试角色

| 角色 | 登录账号 | 权限范围 | 测试重点 |
|------|----------|----------|----------|
| **超级管理员** | admin / admin123 | 全部功能 | 系统配置、用户管理、数据导入 |
| **操作员** | (待创建) operator / oper123 | 数据查看、报警处置 | 业务页面、报警、导入 |
| **审核员** | (待创建) auditor / audi123 | 数据查看、碳核查 | 碳管理、审计 |

---

## 二、测试用例清单（按角色分组）

### 2.1 认证测试（所有角色通用）

| # | 测试项 | 预期 | 数据影响 | 清理方式 |
|---|--------|------|----------|----------|
| A1 | 访问系统未登录自动跳转登录页 | 跳转到 /login | 无 | — |
| A2 | 输入正确账号密码登录 | 返回 Token，跳转首页 | 无 | — |
| A3 | 输入错误密码 | 提示"用户名或密码错误" | 无 | — |
| A4 | 登录后刷新页面 | 保持登录状态（Cookie） | 无 | — |
| A5 | 点击退出 | 清除 Token，跳转登录页 | 无 | — |

### 2.2 超级管理员测试

#### 2.2.1 系统管理

| # | 测试项 | 预期 | 数据影响 | 清理方式 |
|---|--------|------|----------|----------|
| S1 | 查看参数配置 | 显示当前 7 项系统配置 | 无 | — |
| S2 | 编辑配置项 | 数值可修改 | 修改 system_config | 改回原值 |
| S3 | 查看操作日志 | 显示日志列表，可分页 | 无 | — |

#### 2.2.2 数据导入

| # | 测试项 | 预期 | 数据影响 | 清理方式 |
|---|--------|------|----------|----------|
| D1 | 查看可导入表列表（GET /api/import/tables） | 返回 15 个表 | 无 | — |
| D2 | 下载设备组模板（GET /api/import/device_groups/template） | 返回 xlsx 文件 | 无 | — |
| D3 | 下载供应商模板（GET /api/admin/suppliers/template） | 返回 xlsx 文件 | 无 | — |
| D4 | 导入能耗时序数据（POST） | 数据写入 energy_records | 插入新行 | DELETE FROM energy_records WHERE id IN (最后N条) |

#### 2.2.3 数据字典

| # | 测试项 | 预期 | 数据影响 | 清理方式 |
|---|--------|------|----------|----------|
| DC1 | 新增字典类型（POST /api/dict/types） | 创建成功 | 插入 data_dict_types | DELETE WHERE dict_code='test_xxx' |
| DC2 | 新增字典条目（POST /api/dict/items） | 创建成功 | 插入 data_dict_items | DELETE WHERE id=? |
| DC3 | 删除字典条目（DELETE） | 删除成功 | 删除 data_dict_items | 自动清理 |

#### 2.2.4 供应商管理

| # | 测试项 | 预期 | 数据影响 | 清理方式 |
|---|--------|------|----------|----------|
| V1 | 新增供应商（POST） | 创建成功，返回账号密码 | 插入 suppliers + supplier_users | DELETE WHERE id=? |
| V2 | 列出供应商（GET） | 返回列表 | 无 | — |
| V3 | 删除供应商（DELETE） | 删除成功 | 删除 suppliers | 自动清理 |
| V4 | 批量导入供应商（Excel） | 导入成功 | 插入多条 | DELETE WHERE supplier_code='test_%' |

### 2.3 业务功能测试（角色无关）

#### 2.3.1 驾驶舱

| # | 测试项 | 预期 | 数据影响 | 清理方式 |
|---|--------|------|----------|----------|
| B1 | 驾驶舱KPI数据 | 显示今日/月/年用电量 | 无 | — |
| B2 | 今日vs昨日趋势图 | 显示24h功率曲线 | 无 | — |
| B3 | 设备能耗排名Top5 | 按用电量降序 | 无 | — |

#### 2.3.2 用能概况

| # | 测试项 | 预期 | 数据影响 | 清理方式 |
|---|--------|------|----------|----------|
| B4 | 企业总览KPI | 显示综合能耗/单位产值 | 无 | — |
| B5 | 用能结构饼图 | 各设备组占比 | 无 | — |
| B6 | 能耗趋势图 | 日/周趋势切换 | 无 | — |

#### 2.3.3 数据监控

| # | 测试项 | 预期 | 数据影响 | 清理方式 |
|---|--------|------|----------|----------|
| B7 | 实时数据页面 | 显示总功率+设备表格 | 无 | — |
| B8 | 设备监控页面 | 仪表盘+表格 | 无 | — |
| B9 | 报警管理页面 | 实时/历史报警Tab | 无 | — |

#### 2.3.4 能耗分析

| # | 测试项 | 预期 | 数据影响 | 清理方式 |
|---|--------|------|----------|----------|
| B10 | 消费量及强度 | KPI+趋势图 | 无 | — |
| B11 | 能流桑基图 | 显示购入→转换→损失 | 无 | — |
| B12 | 能效对标 | GB 19153等级评价 | 无 | — |

#### 2.3.5 碳管理

| # | 测试项 | 预期 | 数据影响 | 清理方式 |
|---|--------|------|----------|----------|
| B13 | 碳排放核算 | 碳排KPI+来源饼图 | 无 | — |
| B14 | 产品碳足迹 | 全链条碳足迹 | 无 | — |
| B15 | 供应链碳管理 | 供应商碳评分 | 无 | — |
| B16 | 碳预算管理 | 进度条+警告 | 无 | — |

### 2.4 大屏API测试

| # | 测试项 | 预期 | 数据影响 | 清理方式 |
|---|--------|------|----------|----------|
| K1 | GET /api/bigscreen/summary | 综合KPI | 无 | — |
| K2 | GET /api/bigscreen/energy_trend | 24h趋势 | 无 | — |
| K3 | GET /api/bigscreen/energy_structure | 能耗结构 | 无 | — |
| K4 | GET /api/bigscreen/carbon_overview | 碳排总览 | 无 | — |
| K5 | GET /api/bigscreen/device_status | 设备状态 | 无 | — |
| K6 | GET /api/bigscreen/alarm_summary | 报警汇总 | 无 | — |
| K7 | GET /api/bigscreen/ranking | 能耗排名 | 无 | — |
| K8 | GET /api/heartbeat | 系统心跳 | 无 | — |

---

## 三、测试执行步骤

### 3.1 数据清理规则

所有测试用例按以下 **命名空间规则** 确保可清除：

```
字典类型：测试代码以 test_ 开头
供应商代码：以 TEST_ 开头
导入数据：记录到 import_logs 表，可通过日志回溯
```

### 3.2 自动清理脚本

```python
# 测试完成后执行
def cleanup_test_data():
    conn = get_db(); c = conn.cursor()
    c.execute("DELETE FROM data_dict_types WHERE dict_code LIKE 'test_%'")
    c.execute("DELETE FROM data_dict_items WHERE id NOT IN (SELECT id FROM data_dict_types)")
    c.execute("DELETE FROM suppliers WHERE supplier_code LIKE 'TEST_%'")
    c.execute("DELETE FROM supplier_users WHERE supplier_id NOT IN (SELECT id FROM suppliers)")
    conn.commit(); conn.close()
```

---

## 四、测试结果记录表

| 测试ID | 测试项 | 角色 | 结果 | 备注 |
|--------|--------|------|------|------|
| A1 | 未登录跳转 | 所有 | ⏳ | |
| A2 | 正确登录 | 所有 | ⏳ | |
| ... | | | | |

---

## 五、测试环境

| 项目 | 配置 |
|------|------|
| 后端 | http://localhost:8089 |
| 前端 | http://localhost:5173/demo/ecms/ |
| 数据库 | SQLite: backend/energy_data.db |
| 模拟数据 | energy_simulator.py（7天，5分钟间隔） |
