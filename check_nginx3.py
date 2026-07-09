import os
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get("SERVER_HOST", ""), username='root', password=os.environ.get("SERVER_PASS", ""), timeout=15, allow_agent=False, key_filename=None)

# 在现有 ziwi.cn server block 的 HTTPS 段里插入 /demo/ecms/ 的 location
# 先读取现有配置
stdin, stdout, stderr = ssh.exec_command('cat /etc/nginx/sites-enabled/ziwi.cn')
old_conf = stdout.read().decode('utf-8')

print('=== Current config (last 20 lines) ===')
print('\n'.join(old_conf.strip().split('\n')[-20:]))

ssh.close()
print('\nDone.')
