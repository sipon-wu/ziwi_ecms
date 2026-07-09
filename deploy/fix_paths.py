import os
import paramiko, os, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get("SERVER_HOST", ""), username='root', password=os.environ.get("SERVER_PASS", ""), timeout=15)
sftp = ssh.open_sftp()

local_dist = r'D:\工业元\数云_新质力\ziwi_project_dna\frontend\dist'
cnt = 0
for root, dirs, files in os.walk(local_dist):
    for f in files:
        lp = os.path.join(root, f)
        rel = os.path.relpath(lp, local_dist).replace('\\', '/')
        rp = '/var/www/demo/ecms/' + rel
        remote_dir = '/var/www/demo/ecms/' + os.path.dirname(rel)
        try:
            sftp.stat(remote_dir)
        except:
            ssh.exec_command('mkdir -p ' + remote_dir)
        sftp.put(lp, rp)
        cnt += 1
print('Uploaded ' + str(cnt) + ' files')

# Verify
stdin, stdout, stderr = ssh.exec_command('ls /var/www/demo/ecms/index.html && ls /var/www/demo/ecms/assets/ | head -3')
print(stdout.read().decode())

# Test frontend
stdin, stdout, stderr = ssh.exec_command('curl -sk -o /dev/null -w "%{http_code}" https://localhost/demo/ecms/ -H "Host: ziwi.cn"')
print('HTTP: ' + stdout.read().decode())

sftp.close()
ssh.close()
