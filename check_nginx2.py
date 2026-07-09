import os
import paramiko, os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get("SERVER_HOST", ""), username='root', password=os.environ.get("SERVER_PASS", ""), timeout=15)

# 查看现有 nginx 配置格式
stdin, stdout, stderr = ssh.exec_command('cat /etc/nginx/sites-enabled/ziwi.cn')
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
