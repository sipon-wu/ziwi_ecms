import os
"""检查云服务器数据状态"""
import paramiko, json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get("SERVER_HOST", ""), username='root', password=os.environ.get("SERVER_PASS", ""), timeout=15)

# 先把检查脚本写到服务器再执行
check_script = '''#!/bin/bash
echo "=== RESET LOG ==="
tail -5 /var/www/demo/ecms-backend/reset_demo.log 2>/dev/null || echo "(no log)"

echo ""
echo "=== DB ROWS ==="
python3 << 'PYEOF'
import sqlite3
conn = sqlite3.connect("/var/www/demo/ecms-backend/energy_data.db")
c = conn.cursor()
for t in ["energy_records","device_energy","production_data","daily_energy","operation_logs"]:
    try:
        cnt = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {cnt}")
    except:
        print(f"  {t}: (not found)")
r = c.execute("SELECT MAX(timestamp) FROM energy_records").fetchone()[0]
print(f"  latest energy_records: {r}")
r = c.execute("SELECT COUNT(*) FROM energy_records WHERE timestamp LIKE '2026-06-11%'").fetchone()[0]
print(f"  today (6-11): {r}")
conn.close()
PYEOF

echo ""
echo "=== API ==="
curl -s http://localhost:8088/api/dashboard/summary 2>/dev/null | python3 -c "import sys,json;d=json.load(sys.stdin)['data'];print(f'  today_kwh={d[\"today_kwh\"]}')"
'''

stdin, stdout, stderr = ssh.exec_command(check_script)
out = stdout.read().decode()
err = stderr.read().decode()
print(out)
if err:
    print("STDERR:", err[:500])

ssh.close()
