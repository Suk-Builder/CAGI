// ====== Entities-150 v2.0 入口 ======
const http = require('http');
const url = require('url');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });

const { initDB } = require('./core');
const { handleRoutes } = require('./routes');
const { PORT } = require('./config');

const server = http.createServer(async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') { res.writeHead(200); res.end(); return; }

  try {
    const parsed = url.parse(req.url, true);
    const handled = await handleRoutes(req, res, parsed);
    if (!handled) {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, message: 'Not found' }));
    }
  } catch (e) {
    console.error('[Server]', e.message);
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ success: false, message: e.message }));
  }
});

initDB().then(() => {
  server.listen(PORT, () => console.log(`[Server] v2.0 on port ${PORT}`));
}).catch(e => { console.error('[DB]', e.message); process.exit(1); });
