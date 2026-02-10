const path = require('path');

process.chdir(__dirname);
process.argv = [process.argv[0], 'dev'];
console.log('CWD:', process.cwd());
console.log('Starting Next.js dev server...');

require('next/dist/bin/next');
