import os
"""知微能碳 — 生产部署同步脚本"""
import paramiko, os, json, time

HOST = os.environ.get("SERVER_HOST", ""); USER = 'root'; PASSWORD = os.environ.get("SERVER_PASS", "")
LOCAL_BACKEND = r'D:\工业元\数云_新质力\ziwi_project_dna\backend'
LOCAL_FRONTEND = r'D:\工业元\数云_新质力\ziwi_project_dna\frontend'
REMOTE_DIR = '/var/www/demo/ecms-backend/'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
sftp = ssh.open_sftp()
print('Connected to', HOST)

# 1. Kill old
print('\nStopping backend...')
ssh.exec_command('pkill -f "uvicorn main:app" 2>/dev/null; fuser -k 8088/tcp 2>/dev/null; sleep 1')

# 2. Upload backend
print('\nUploading backend...')
for f in ['main.py','db.py','config.py','auth.py','data_import.py',
          'generate_import_excel.py','migrate_devices.py','simulate_monthly.py',
          'reset_demo.py','requirements.txt']:
    p = os.path.join(LOCAL_BACKEND, f)
    if os.path.exists(p):
        sftp.put(p, REMOTE_DIR + f)
        print(' ', f)

ssh.exec_command('mkdir -p ' + REMOTE_DIR + 'routers')
for f in os.listdir(os.path.join(LOCAL_BACKEND, 'routers')):
    if f.endswith('.py'):
        sftp.put(os.path.join(LOCAL_BACKEND, 'routers', f), REMOTE_DIR + 'routers/' + f)
print('  routers/ done')

# 3. Upload DB
print('\nUploading database...')
sftp.put(os.path.join(LOCAL_BACKEND, 'energy_data.db'), REMOTE_DIR + 'energy_data.db')
print('  energy_data.db')

# 4. Upload frontend
print('\nUploading frontend...')
local_dist = os.path.join(LOCAL_FRONTEND, 'dist')
for root, dirs, files in os.walk(local_dist):
    for f in files:
        lp = os.path.join(root, f)
        rp = os.path.relpath(lp, local_dist).replace(os.sep, '/')
        rmt = '/var/www/demo/ecms/' + rp
        try: sftp.stat(os.path.dirname(rmt))
        except: ssh.exec_command('mkdir -p ' + os.path.dirname(rmt))
        sftp.put(lp, rmt)
total = sum(len(files) for _,_,files in os.walk(local_dist))
print(f'  {total} files uploaded')
ssh.exec_command('chmod -R 755 /var/www/demo/ecms/')

# 5. Install deps & start
print('\nInstalling deps...')
ssh.exec_command('pip3 install openpyxl fastapi uvicorn bcrypt pyjwt 2>&1 | tail -1')

print('\nStarting backend...')
ssh.exec_command('cd ' + REMOTE_DIR + ' && nohup python3 -m uvicorn main:app --host 127.0.0.1 --port 8088 > backend.log 2>&1 &')
time.sleep(3)

# 6. Verify
print('\nVerifying...')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8088/api/heartbeat')
d = json.loads(stdout.read().decode())
print(f'  heartbeat: {"OK" if d.get("code")==0 else "FAIL"}')

stdin, stdout, stderr = ssh.exec_command('curl -sk -o /dev/null -w "%{http_code}" https://localhost/demo/ecms/ -H "Host: ziwi.cn"')
print(f'  frontend: HTTP {stdout.read().decode().strip()}')

sftp.close()
ssh.close()
print('\nDone! https://ziwi.cn/demo/ecms/')
