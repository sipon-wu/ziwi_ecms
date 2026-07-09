import os
import paramiko, os, time, json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get("SERVER_HOST", ""), username='root', password=os.environ.get("SERVER_PASS", ""), timeout=15)
sftp = ssh.open_sftp()

# Stop backend
ssh.exec_command('pkill -f "uvicorn main:app" 2>/dev/null; fuser -k 8088/tcp 2>/dev/null; sleep 1')
print('stopped backend')

# Upload backend files
BASE = r'D:\工业元\数云_新质力\ziwi_project_dna'
for f in ['daily_refresh.py', 'monthly_guest_cleanup.py']:
    sftp.put(os.path.join(BASE, 'backend', f), '/var/www/demo/ecms-backend/' + f)
    print('  OK ' + f)

# Upload routers
router_dir = os.path.join(BASE, 'backend', 'routers')
for f in os.listdir(router_dir):
    if f.endswith('.py'):
        sftp.put(os.path.join(router_dir, f), '/var/www/demo/ecms-backend/routers/' + f)
print('  OK routers')

# Upload database
sftp.put(os.path.join(BASE, 'backend', 'energy_data.db'), '/var/www/demo/ecms-backend/energy_data.db')
print('  OK database')

# Upload frontend dist
local_dist = os.path.join(BASE, 'frontend', 'dist')
cnt = 0
for root, dirs, files in os.walk(local_dist):
    for f in files:
        lp = os.path.join(root, f)
        rp = ('/var/www/demo/ecms/' + os.path.relpath(lp, local_dist))
        remote_dir = os.path.dirname(rp)
        try:
            sftp.stat(remote_dir)
        except:
            ssh.exec_command('mkdir -p ' + remote_dir)
        sftp.put(lp, rp)
        cnt += 1
print('  OK frontend ' + str(cnt) + ' files')

# Restart backend
ssh.exec_command('cd /var/www/demo/ecms-backend && nohup python3 -m uvicorn main:app --host 127.0.0.1 --port 8088 > backend.log 2>&1 &')
time.sleep(3)

# Verify
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8088/api/dashboard/ranking')
d = json.loads(stdout.read().decode())
grp = d['data']['ranking']
print('Verify ranking: ' + str(len(grp)) + ' groups, top=' + grp[0]['group_name'] + ' (' + str(grp[0]['load_rate_pct']) + '%)')

stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8088/api/efficiency/optimization_tasks')
d = json.loads(stdout.read().decode())
print('Verify tasks: ' + str(len(d['data']['tasks'])) + ' items')

stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8088/api/heartbeat')
print('Verify heartbeat: ' + ('OK' if json.loads(stdout.read().decode())['code'] == 0 else 'FAIL'))

sftp.close()
ssh.close()
print('Done')
