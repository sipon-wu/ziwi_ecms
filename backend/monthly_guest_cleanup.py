"""
知微能碳 — 每月1日 guest 账号数据清理
每月1日 0:00 cron 执行：
1. 清除 guest 操作日志（operation_logs）
2. 回归干净的演示数据状态
3. admin 操作数据不受影响
"""

import sqlite3, os
from datetime import datetime

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "energy_data.db")
now = datetime.now().strftime("%Y-%m-%d %H:%M")

print(f"[{now}] 每月 guest 数据清理开始...")

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# 清除 guest 操作日志
deleted = c.execute("DELETE FROM operation_logs WHERE username='guest'").rowcount
print(f"  [1] 清除 guest 操作记录: {deleted} 条")

conn.commit()
conn.close()

print(f"[{now}] guest 数据清理完成")
