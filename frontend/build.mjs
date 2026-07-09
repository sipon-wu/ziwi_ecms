import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const require = createRequire(import.meta.url);

// 用 require 加载 vite CJS bundle
const { build } = require('D:/工业元/数云_新质力/ziwi_project_dna/frontend/node_modules/vite/dist/node/index.cjs');

const path = require('node:path');
const fs = require('node:fs');

// 确认 index.html 存在
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
