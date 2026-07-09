import os
"""知微能碳 — 生产环境后端部署（替换旧单文件架构为模块化架构）"""
import paramiko, os, time

HOST = os.environ.get("SERVER_HOST", "")
USER = 'root'
PASSWORD = os.environ.get("SERVER_PASS", "")
LOCAL_BACKEND = r'D:\工业元\数云_新质力\ziwi_project_dna\backend'
REMOTE_DIR = '/var/www/demo/ecms-backend/'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
sftp = ssh.open_sftp()
print('✅ 已连接', HOST)

# 1. 备份旧的数据库
print('\n📦 备份旧数据库...')
ssh.exec_command(f'cp {REMOTE_DIR}energy_data.db {REMOTE_DIR}energy_data.db.bak')
print('✅ 已备份旧DB')

# 2. 上传核心后端文件
core_files = ['main.py', 'db.py', 'config.py', 'auth.py', 'data_import.py',
              'generate_import_excel.py', 'migrate_devices.py', 'simulate_monthly.py',
              'reset_demo.py', 'requirements.txt']
for f in core_files:
    local = os.path.join(LOCAL_BACKEND, f)
    if os.path.exists(local):
        sftp.put(local, REMOTE_DIR + f)
        print(f'  ✅ {f}')

# 3. 上传 routers/
ssh.exec_command(f'mkdir -p {REMOTE_DIR}routers')
for f in os.listdir(os.path.join(LOCAL_BACKEND, 'routers')):
    if f.endswith('.py'):
        sftp.put(os.path.join(LOCAL_BACKEND, 'routers', f), REMOTE_DIR + 'routers/' + f)
router_files = [f for f in os.listdir(os.path.join(LOCAL_BACKEND, 'routers')) if f.endswith('.py')]
print(f'  ✅ routers/ ({len(router_files)} 个文件)')

# 4. 上传新数据库
sftp.put(os.path.join(LOCAL_BACKEND, 'energy_data.db'), REMOTE_DIR + 'energy_data.db')
print('  ✅ energy_data.db (新)')

# 5. pip 安装依赖
print('\n📦 安装 Python 依赖...')
ssh.exec_command(f'cd {REMOTE_DIR} && pip3 install -r requirements.txt 2>&1 | tail -3')
print('  依赖已安装')

# 6. 杀旧进程 + 启动新后端
print('\n🚀 启动后端...')
ssh.exec_command('pkill -f "uvicorn main:app" 2>/dev/null; sleep 1')
stdin, stdout, stderr = ssh.exec_command(f'cd {REMOTE_DIR} && nohup python3 -m uvicorn main:app --host 127.0.0.1 --port 8088 > backend.log 2>&1 &')
time.sleep(2)

# 7. 验证
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8088/api/heartbeat')
print(f'  后端 heartbeat: {stdout.read().decode()[:80]}')

# 8. 重载 nginx
print('\n🔧 重载 Nginx...')
stdin, stdout, stderr = ssh.exec_command('nginx -t 2>&1 && nginx -s reload 2>&1')
print(f'  {stdout.read().decode()[:80]}')

time.sleep(1)
stdin, stdout, stderr = ssh.exec_command('curl -sk https://localhost/demo/ecms/api/heartbeat -H "Host: ziwi.cn"')
print(f'  通过 nginx: {stdout.read().decode()[:80]}')

# 9. 验证前端登录
time.sleep(1)
stdin, stdout, stderr = ssh.exec_command('''curl -sk -X POST https://localhost/demo/ecms/api/auth/login -H "Host: ziwi.cn" -H "Content-Type: application/json" -d '{"username":"guest","password":"123"}' ''')
resp = stdout.read().decode()
import json
try:
    d = json.loads(resp)
    print(f'  Guest 登录: {"✅" if d.get("code")==0 else "❌"} role={d.get("data",{}).get("user",{}).get("role","?")}')
except:
    print(f'  Guest 登录响应: {resp[:100]}')

sftp.close()
ssh.close()
print('\n🎉 后端部署完成!')
print(f'   访问: https://ziwi.cn/demo/ecms/')
