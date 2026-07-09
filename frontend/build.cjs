const { build } = require('D:/工业元/数云_新质力/ziwi_project_dna/frontend/node_modules/vite/dist/node/index.cjs');
const path = require('node:path');
const fs = require('node:fs');

const root = 'D:/工业元/数云_新质力/ziwi_project_dna/frontend';
console.log('Building from:', root);
console.log('index.html exists:', fs.existsSync(path.join(root, 'index.html')));

build({
  root,
  build: {
    outDir: path.join(root, 'dist'),
  }
}).then(() => {
  console.log('✅ Build complete!');
}).catch(err => {
  console.error('❌ Build failed:', err.message);
  process.exit(1);
});
