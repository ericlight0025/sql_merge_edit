#!/usr/bin/env node
'use strict';
const fs   = require('fs');
const path = require('path');

const src = path.join(__dirname, '..', 'src', 'webview');
const dst = path.join(__dirname, '..', 'out', 'webview');

fs.mkdirSync(dst, { recursive: true });
for (const file of fs.readdirSync(src)) {
  fs.copyFileSync(path.join(src, file), path.join(dst, file));
  console.log(`copied: src/webview/${file} → out/webview/${file}`);
}
