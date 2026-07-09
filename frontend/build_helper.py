import subprocess, os

frontend_dir = r'D:\工业元\数云_新质力\ziwi_project_dna\frontend'

# 确认 index.html 存在
print('index.html exists:', os.path.exists(os.path.join(frontend_dir, 'index.html')))

# 用 subprocess 跑，正确传 cwd
result = subprocess.run(
    ['node', 'node_modules/vite/dist/node/cli.js', 'build'],
    cwd=frontend_dir,
    capture_output=True,
    text=True,
    timeout=120,
    encoding='utf-8',
    errors='replace',
)
print('STDOUT:', result.stdout)
print('STDERR:', result.stderr)
print('Return code:', result.returncode)
