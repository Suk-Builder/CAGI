// ====== Core: DB + LLM + Memory ======
const sqlite3 = require('sqlite3').verbose();
const { DB_PATH, LLM_BACKENDS, LLM_MAX_CONCURRENT, LLM_TIMEOUT_MS, LLM_MAX_RETRIES } = require('./config');

// ─── DB ───
let db = null;
let writeQueue = Promise.resolve();
const enqueue = fn => { const p = writeQueue.then(fn, fn); writeQueue = p.catch(()=>{}); return p; };

function initDB() {
  return new Promise((resolve, reject) => {
    db = new sqlite3.Database(DB_PATH, err => {
      if (err) { reject(err); return; }
      console.log('[DB]', DB_PATH);
      db.serialize(() => {
        db.run('PRAGMA journal_mode=WAL');
        db.run('PRAGMA busy_timeout=10000');
        db.run('PRAGMA synchronous=NORMAL');
      });
      const sql = `
        CREATE TABLE IF NOT EXISTS debates (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, topic TEXT NOT NULL, entities TEXT, rounds INTEGER, status TEXT DEFAULT 'active', created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS speeches (id INTEGER PRIMARY KEY AUTOINCREMENT, debate_id INTEGER NOT NULL, entity_id TEXT, round INTEGER, content TEXT, summary TEXT, backend TEXT, latency_ms INTEGER, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS entity_memories (id INTEGER PRIMARY KEY AUTOINCREMENT, debate_id INTEGER NOT NULL, entity_id TEXT, topic TEXT, round INTEGER, content TEXT, summary TEXT, tags TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE INDEX IF NOT EXISTS idx_speeches_debate ON speeches(debate_id);
        CREATE INDEX IF NOT EXISTS idx_speeches_entity ON speeches(entity_id);
        CREATE INDEX IF NOT EXISTS idx_memories_debate_entity ON entity_memories(debate_id, entity_id);
      `;
      db.exec(sql, err => { if (err) reject(err); else { console.log('[DB] Tables ready'); resolve(); } });
    });
  });
}

const dbCreateDebate = (name, topic, entities, rounds) => enqueue(() => new Promise((res, rej) => {
  db.run('INSERT INTO debates (name,topic,entities,rounds,status) VALUES (?,?,?,?,?)',
    [name||topic, topic, JSON.stringify(entities), rounds, 'active'],
    function(err) { err ? rej(err) : res(this.lastID); });
}));

const dbCloseDebate = id => enqueue(() => new Promise((res, rej) => {
  db.run("UPDATE debates SET status='completed' WHERE id=?", [id], err => err?rej(err):res());
}));

const dbSaveSpeech = (debateId, entityId, round, content, summary, backend, latencyMs) => enqueue(() => new Promise((res, rej) => {
  db.run('INSERT INTO speeches (debate_id,entity_id,round,content,summary,backend,latency_ms) VALUES (?,?,?,?,?,?,?)',
    [debateId, entityId, round, content, summary, backend, latencyMs], err => err?rej(err):res());
}));

// ─── LLM: fetch + AbortController + Semaphore + 退避 ───
class Semaphore {
  constructor(max) { this.max = max; this.cur = 0; this.q = []; }
  async acquire() {
    if (this.cur < this.max) { this.cur++; return; }
    await new Promise(r => this.q.push(r)); this.cur++;
  }
  release() { this.cur--; if (this.q.length) this.q.shift()(); }
}
const sem = new Semaphore(LLM_MAX_CONCURRENT);
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function callLLM(systemPrompt, messages, maxTokens = 600, preferred = null) {
  await sem.acquire();
  try { return await _retry(systemPrompt, messages, maxTokens, preferred); }
  finally { sem.release(); }
}

async function _retry(systemPrompt, messages, maxTokens, preferred) {
  const backends = preferred
    ? [LLM_BACKENDS.find(b => b.name === preferred)].filter(Boolean)
    : [...LLM_BACKENDS];
  let lastErr = null;
  for (let attempt = 0; attempt < LLM_MAX_RETRIES; attempt++) {
    for (const b of backends) {
      try { return await _single(b, systemPrompt, messages, maxTokens); }
      catch (err) {
        lastErr = err;
        console.error(`[LLM] ${{b.name}} fail (#${{attempt+1}}): ${{err.message}}`);
        await sleep(1000 * (attempt + 1));
      }
    }
  }
  throw new Error(`All backends failed. Last: ${{lastErr?.message}}`);
}

async function _single(backend, systemPrompt, messages, maxTokens) {
  const ctrl = new AbortController();
  const tid = setTimeout(() => ctrl.abort(), LLM_TIMEOUT_MS);
  const body = {
    model: backend.model,
    messages: [{ role: 'system', content: systemPrompt },
      ...messages.map(m => ({ role: m.role==='assistant'?'assistant':'user', content: m.content }))],
    max_tokens: maxTokens, temperature: 0.85, top_p: 0.9
  };
  const headers = { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + backend.apiKey };
  if (backend.format === 'openrouter') { headers['HTTP-Referer']='https://sukaczev.com'; headers['X-Title']='Entities-150'; }
  try {
    const res = await fetch(backend.apiUrl, { method: 'POST', headers, body: JSON.stringify(body), signal: ctrl.signal });
    if (!res.ok) { const t = await res.text(); throw new Error(`HTTP ${{res.status}}: ${{t.slice(0,200)}}`); }
    const data = await res.json();
    if (data.choices?.[0]?.message?.content) return data.choices[0].message.content;
    throw new Error('Invalid: ' + JSON.stringify(data).slice(0,200));
  } finally { clearTimeout(tid); }
}

// ─── Memory ───
const MEM = {};
const MAX_MEM = 20;
function memLoad(id) { if (!MEM[id]) MEM[id] = { discoveries: [], lastTopics: {} }; return MEM[id]; }
function memSave(id, problem, content) {
  const m = memLoad(id); m.discoveries.unshift({ t: Date.now(), problem, content: content.slice(0,400) });
  if (m.discoveries.length > MAX_MEM) m.discoveries.pop(); m.lastTopics[problem] = Date.now();
}
function memPrompt(id, currentProblem) {
  const m = memLoad(id); if (!m.discoveries.length) return '';
  const rel = m.discoveries.filter(d => !currentProblem || d.problem===currentProblem || currentProblem.includes(d.problem) || d.problem.includes(currentProblem)).slice(0,5);
  const other = m.discoveries.filter(d => !rel.includes(d)).slice(0,3);
  const lines = ['\n[你的长期记忆——继续推进]'];
  [...rel, ...other].forEach((d,i) => lines.push(`${{i+1}}. [${{d.problem}}] ${{d.content.slice(0,120)}}`));
  lines.push(`\n[记录: ${{m.discoveries.length}}个]\n`); return lines.join('\n');
}
function memExtract(id, problem, response) {
  const formulas = [];
  for (const line of response.split('\n')) {
    if ((line.includes('=')||line.includes('≈')||line.includes('≤')||line.includes('≥')) && /\d/.test(line) && line.length>15 && line.length<200)
      formulas.push(line.trim());
  }
  if (formulas.length >= 2) { memSave(id, problem, formulas.slice(0,3).join('; ')); return true; }
  return false;
}

module.exports = { initDB, dbCreateDebate, dbCloseDebate, dbSaveSpeech, callLLM, memPrompt, memExtract };
