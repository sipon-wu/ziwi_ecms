import os
import paramiko, os, time, json

HOST = os.environ.get("SERVER_HOST", "")
USER = 'root'
PASSWORD = os.environ.get("SERVER_PASS", "")
LOCAL_BACKEND = r'D:\工业元\数云_新质力\ziwi_project_dna\backend'
LOCAL_FRONTEND = r'D:\工业元\数云_新质力\ziwi_project_dna\frontend'
REMOTE_BACKEND = '/var/www/demo/ecms-backend/'
REMOTE_FRONTEND = '/var/www/demo/ecms/'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
sftp = ssh.open_sftp()
print('Connected to', HOST)

# 1. Kill old backend
print('\nStopping backend...')
ssh.exec_command('pkill -f "uvicorn main:app" 2>/dev/null; fuser -k 8088/tcp 2>/dev/null; sleep 1')

# 2. Upload backend core files
print('\nUploading backend...')
for f in ['main.py', 'reset_demo.py', 'generate_import_excel.py', 'simulate_monthly.py']:
    local = os.path.join(LOCAL_BACKEND, f)
    if os.path.exists(local):
        sftp.put(local, REMOTE_BACKEND + f)
        print(f'  OK {f}')

# 3. Upload routers
for f in os.listdir(os.path.join(LOCAL_BACKEND, 'routers')):
    if f.endswith('.py'):
        sftp.put(os.path.join(LOCAL_BACKEND, 'routers', f), REMOTE_BACKEND + 'routers/' + f)
print('  OK routers')

# 4. Upload database
print('\nUploading database...')
sftp.put(os.path.join(LOCAL_BACKEND, 'energy_data.db'), REMOTE_BACKEND + 'energy_data.db')
print('  OK energy_data.db')

# 5. Upload frontend dist
print('\nUploading frontend...')
local_dist = os.path.join(LOCAL_FRONTEND, 'dist')
file_count = 0
for root, dirs, files in os.walk(local_dist):
    for f in files:
        local_path = os.path.join(root, f)
        rel = os.path.relpath(local_path, local_dist)
        remote_path = (REMOTE_FRONTEND + rel).replace('\\', '/')
        remote_dir = os.path.dirname(remote_path)
        try:
            sftp.stat(remote_dir)
        except:
            ssh.exec_command('mkdir -p ' + remote_dir)
        sftp.put(local_path, remote_path)
        file_count += 1
print(f'  OK frontend {file_count} files')

# 6. Upload report
print('\nUploading report...')
sftp.put(r'D:\工业元\数云_新质力\ziwi_project_dna\知微能碳Beta-数据核查报告-20260610.md',
         REMOTE_BACKEND + '知微能碳Beta-数据核查报告-20260610.md')
print('  OK report')

# 7. Start backend
print('\nStarting backend...')
ssh.exec_command('cd ' + REMOTE_BACKEND + ' && nohup python3 -m uvicorn main:app --host 127.0.0.1 --port 8088 > backend.log 2>&1 &')
time.sleep(3)

# 8. Verify
print('\nVerifying...')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8088/api/heartbeat')
d = json.loads(stdout.read().decode())
print(f'  heartbeat: {"OK" if d.get("code")==0 else "FAIL"}')

stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8088/api/monitoring/alarms')
d = json.loads(stdout.read().decode())
total = d['data']['total']
print(f'  alarms: {total}')

stdin, stdout, stderr = ssh.exec_command(
    'curl -sk -X POST https://localhost/demo/ecms/api/auth/login '
    '-H "Host: ziwi.cn" -H "Content-Type: application/json" '
    '-d \'{"username":"guest","password":"123"}\'')
d = json.loads(stdout.read().decode())
print(f'  guest login: {"OK" if d.get("code")==0 else "FAIL"}')

sftp.close()
ssh.close()
print('\nDone! https://ziwi.cn/demo/ecms/')
