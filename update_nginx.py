import os
import paramiko, os

HOST = os.environ.get("SERVER_HOST", "")
USER = 'root'
PASS = os.environ.get("SERVER_PASS", "")
LOCAL_CONF = r'D:\工业元\数云_新质力\ziwi_project_dna\ziwi.cn.nginx.new.conf'
REMOTE_CONF = '/etc/nginx/sites-enabled/ziwi.cn'

def ssh_cmd(ssh, cmd, desc=''):
    print(f'[SSH] {desc or cmd}')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print('  OUT:', out[:300])
    if err: print('  ERR:', err[:300])
    return out, err

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS, timeout=15, allow_agent=False, key_filename=None)
    sftp = ssh.open_sftp()

    # 1. Backup existing config
    ssh_cmd(ssh, f'cp {REMOTE_CONF} {REMOTE_CONF}.bak', 'Backup existing config')

    # 2. Upload new config
    print('\n[SFTP] Uploading new nginx config...')
    sftp.put(LOCAL_CONF, REMOTE_CONF)
    ssh_cmd(ssh, f'cat {REMOTE_CONF} | head -20', 'Verify uploaded config')

    # 3. Test nginx config
    ssh_cmd(ssh, 'nginx -t', 'Test nginx config')

    # 4. Reload nginx
    ssh_cmd(ssh, 'systemctl reload nginx || nginx -s reload', 'Reload nginx')

    # 5. Verify demo/ecms is accessible
    ssh_cmd(ssh, 'curl -sk -o /dev/null -w "%{http_code}" https://localhost/demo/ecms/ -H "Host: ziwi.cn"', 'Verify /demo/ecms/')

    sftp.close()
    ssh.close()
    print('\n✅ Nginx config updated and reloaded!')

if __name__ == '__main__':
    main()
