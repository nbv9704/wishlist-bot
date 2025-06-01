const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'node_modules', 'node-easyocr', 'dist', 'easyocr.js');

if (!fs.existsSync(filePath)) {
  console.warn('⚠️ easyocr.js not found, skipping patch.');
  process.exit(0);
}

fs.readFile(filePath, 'utf8', (err, data) => {
  if (err) return console.error('❌ Read error:', err);

  if (data.includes(`this.pythonPath = 'python';`)) {
    console.log('✅ Already patched.');
    return;
  }

  const patched = data.replace(`this.pythonPath = 'python3';`, `this.pythonPath = 'python';`);

  fs.writeFile(filePath, patched, 'utf8', (err) => {
    if (err) return console.error('❌ Write error:', err);
    console.log('✅ Patched easyocr.js successfully.');
  });
});
