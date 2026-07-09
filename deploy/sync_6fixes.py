import os
import paramiko, os, time, json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get("SERVER_HOST", ""), username='root', password=os.environ.get("SERVER_PASS", ""), timeout=15)
sftp = ssh.open_sftp()

# Stop
ssh.exec_command('pkill -f "uvicorn main:app" 2>/dev/null; fuser -k 8088/tcp 2>/dev/null; sleep 1')
print('stopped')

BASE = r'D:\工业元\数云_新质力\ziwi_project_dna'

# Upload backend files
for f in ['daily_refresh.py', 'monthly_guest_cleanup.py']:
    sftp.put(os.path.join(BASE, 'backend', f), '/var/www/demo/ecms-backend/' + f)
    print('  OK ' + f)

# Routers
for f in os.listdir(os.path.join(BASE, 'backend', 'routers')):
    if f.endswith('.py'):
        sftp.put(os.path.join(BASE, 'backend', 'routers', f), '/var/www/demo/ecms-backend/routers/' + f)
print('  OK routers')

# Database
sftp.put(os.path.join(BASE, 'backend', 'energy_data.db'), '/var/www/demo/ecms-backend/energy_data.db')
print('  OK database')

# Frontend dist
local_dist = os.path.join(BASE, 'frontend', 'dist')
cnt = 0
for root, dirs, files in os.walk(local_dist):
    for f in files:
        lp = os.path.join(root, f)
        rp = '/var/www/demo/ecms/' + os.path.relpath(lp, local_dist)
        try:
            sftp.stat(os.path.dirname(rp))
        except:
            ssh.exec_command('mkdir -p ' + os.path.dirname(rp))
        sftp.put(lp, rp)
        cnt += 1
print('  OK frontend ' + str(cnt) + ' files')

# Start
ssh.exec_command('cd /var/www/demo/ecms-backend && nohup python3 -m uvicorn main:app --host 127.0.0.1 --port 8088 > backend.log 2>&1 &')
time.sleep(3)

# Verify
tests = [
    ('trend', '/api/dashboard/trend',
     lambda d: f"today={len(d['current_power'])}yest={len(d['yesterday_power'])}"),
    ('monitoring', '/api/monitoring/current',
     lambda d: f"view={d['view']} groups={len(d['devices'])}"),
    ('supply', '/api/carbon/supply',
     lambda d: f"suppliers={len(d['suppliers'])}"),
    ('quota', '/api/carbon_asset/quota',
     lambda d: f"details={len(d['details'])}"),
    ('heartbeat', '/api/heartbeat',
     lambda d: 'OK'),
]
for name, path, check in tests:
    stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8088' + path)
    d = json.loads(stdout.read().decode())['data']
    print('  ' + name + ': ' + check(d))

sftp.close()
ssh.close()
print('Done')
