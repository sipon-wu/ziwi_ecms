import paramiko
import os

# 连接服务器（只读检查）
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get("SERVER_HOST", ""), username='root', password=os.environ.get("SERVER_PASS", ""), timeout=15, allow_agent=False, key_filename=None)
sftp = ssh.open_sftp()

print("=" * 60)
print("  只读检查服务器现状（不修改任何数据）")
print("=" * 60)

# 1. 检查 nginx 配置文件列表
print("\n[1] /etc/nginx/sites-enabled/ 文件列表：")
stdin, stdout, stderr = ssh.exec_command('ls -la /etc/nginx/sites-enabled/')
print(stdout.read().decode('utf-8', errors='replace'))

# 2. 读取 nginx 配置内容
print("[2] /etc/nginx/sites-enabled/ziwi.cn 内容：")
try:
    with sftp.open('/etc/nginx/sites-enabled/ziwi.cn', 'r') as f:
        conf = f.read().decode('utf-8')
    print(conf)
except Exception as e:
    print(f"  读取失败: {e}")

# 3. 检查前端文件
print("\n[3] /var/www/demo/ecms/ 目录：")
stdin, stdout, stderr = ssh.exec_command('ls -la /var/www/demo/ecms/')
print(stdout.read().decode('utf-8', errors='replace'))

# 4. 检查后端状态
print("[4] 后端端口 8088 状态：")
stdin, stdout, stderr = ssh.exec_command('curl -sk -o /dev/null -w "%{http_code}" http://localhost:8088/docs')
code = stdout.read().decode().strip()
print(f"  http://localhost:8088/docs -> HTTP {code}")

# 5. 检查 nginx 进程状态
print("\n[5] nginx 进程状态：")
stdin, stdout, stderr = ssh.exec_command('systemctl status nginx 2>/dev/null | head -5')
print(stdout.read().decode('utf-8', errors='replace'))

# 6. 验证访问
print("\n[6] 验证 https://ziwi.cn/demo/ecms/ ：")
stdin, stdout, stderr = ssh.exec_command('curl -sk -o /dev/null -w "%{http_code}" https://localhost/demo/ecms/ -H "Host: ziwi.cn"')
code = stdout.read().decode().strip()
print(f"  https://ziwi.cn/demo/ecms/ -> HTTP {code}")

# 7. 检查后端进程
print("\n[7] 后端 uvicorn 进程：")
stdin, stdout, stderr = ssh.exec_command('ps aux | grep uvicorn | grep -v grep')
print(stdout.read().decode('utf-8', errors='replace'))

# 8. 将云端 nginx 配置保存到本地（同步回来）
print("\n[8] 同步 nginx 配置到本地...")
local_path = r'D:\工业元\数云_新质力\ziwi_project_dna\deploy\nginx-ziwi.cn.conf'
try:
    with sftp.open('/etc/nginx/sites-enabled/ziwi.cn', 'r') as f:
        conf = f.read().decode('utf-8')
    with open(local_path, 'w', encoding='utf-8') as f:
        f.write(conf)
    print(f"  ✅ 已同步到: {local_path}")
except Exception as e:
    print(f"  ❌ 同步失败: {e}")

# 9. 将前端 dist 目录结构保存下来（用于记忆）
print("\n[9] 前端文件结构：")
stdin, stdout, stderr = ssh.exec_command('find /var/www/demo/ecms/ -type f | sort')
files = stdout.read().decode('utf-8', errors='replace').strip()
print(f"  共 {len(files.split(chr(10)) if files else 0} 个文件")
if files:
    print("  文件列表（前20个）：")
    for f in files.split(chr(10))[:20]:
        print(f"    {f}")

sftp.close()
ssh.close()

print("\n" + "=" * 60)
print("  检查完成，未修改云端任何数据")
print("=" * 60)
