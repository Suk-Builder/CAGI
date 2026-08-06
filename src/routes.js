// ====== 路由：实体 + 对话 + 辩论 ======
const { dbCreateDebate, dbCloseDebate, dbSaveSpeech, callLLM, memPrompt, memExtract } = require('./core');
const { ENTITIES_150, TOPICS, getTopologyContext, getFallback, listEntities } = require('./entities');
const { createSession, runLoop } = require('./debate');

// ─── 工具 ───
async function readBody(req, max = 1e6) {
  let body = '';
  return new Promise((res, rej) => {
    req.on('data', c => { body += c; if (body.length > max) { rej(new Error('too large')); req.destroy(); } });
    req.on('end', () => { try { res(body ? JSON.parse(body) : {}); } catch(e) { rej(e); } });
    req.on('error', rej);
  });
}
function json(res, code, data) {
  res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*' });
  res.end(JSON.stringify(data));
}
function sse(res, session, event, data) {
  const p = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
  for (const r of session.sseClients) { try { r.write(p); } catch(e) {} }
}

// ─── 对话 ───
async function doDialogue(body) {
  const { entityId, topicIndex = 0, history = [], customQuestion } = body;
  const entity = ENTITIES_150[entityId];
  if (!entity) throw new Error('Entity not found');
  const topic = TOPICS[topicIndex] || TOPICS[0];
  const messages = [];
  if (history.length === 0) {
    messages.push({ role: 'user', content: customQuestion || `[话题：${topic.titleCn}] ${topic.opening}` });
  } else {
    for (const h of history) {
      messages.push({ role: 'user', content: `[对话者] ${h.user}` });
      messages.push({ role: 'assistant', content: h.entity });
    }
    messages.push({ role: 'user', content: `请继续以${entity.nameCn}的身份回应。` });
  }
  const problem = customQuestion || (history.length ? history[history.length-1].user : topic.titleCn);
  const enriched = entity.systemPrompt + getTopologyContext(entityId) + memPrompt(entityId, problem);
  try {
    const content = await callLLM(enriched, messages);
    memExtract(entityId, problem, content);
    return { content, entity: { id: entity.id, name: entity.name, nameCn: entity.nameCn, bdiAi: entity.bdiAi } };
  } catch (e) {
    return { content: getFallback(entity, history.length ? 'response' : 'opening', topic), entity: { id: entity.id, name: entity.name, nameCn: entity.nameCn, bdiAi: entity.bdiAi }, fallback: true, error: e.message };
  }
}

// ─── 辩论会话池 ───
const sessions = new Map();
setInterval(() => {
  const now = Date.now();
  for (const [id, s] of sessions) {
    if ((s.status === 'done' || s.status === 'error') && now - s.lastActivity > 5 * 60 * 1000) {
      for (const r of s.sseClients) { try { r.end(); } catch(e) {} }
      sessions.delete(id);
    }
  }
}, 60000);

// ─── 路由分发 ───
async function handleRoutes(req, res, parsed) {
  const p = parsed.pathname;

  // 实体
  if (p === '/api/entities' && req.method === 'GET') { json(res, 200, { success: true, data: listEntities() }); return true; }
  if (p === '/api/entities/list' && req.method === 'GET') { json(res, 200, { success: true, data: { entities: listEntities() } }); return true; }
  if (p === '/api/topics' && req.method === 'GET') { json(res, 200, { success: true, data: TOPICS }); return true; }

  // 对话
  if (p === '/api/dialogue' && req.method === 'POST') {
    try { json(res, 200, { success: true, data: await doDialogue(await readBody(req)) }); }
    catch (e) { json(res, 500, { success: false, message: e.message }); }
    return true;
  }

  // 同步辩论
  if (p === '/api/debate' && req.method === 'POST') {
    try {
      const b = await readBody(req);
      const { name, mode, topic, entities = [], rounds = 2 } = b;
      if (!topic) { json(res, 400, { success: false, message: 'topic required' }); return true; }
      if (!Array.isArray(entities) || !entities.length) { json(res, 400, { success: false, message: 'entities required' }); return true; }
      if (entities.length > 10) { json(res, 400, { success: false, message: 'max 10' }); return true; }
      if (rounds < 1 || rounds > 10) { json(res, 400, { success: false, message: 'rounds 1-10' }); return true; }

      const debateId = await dbCreateDebate(name, topic, entities, rounds);
      const results = [], history = [];
      const session = createSession(debateId, topic, entities, rounds, name, mode);
      await runLoop(session,
        speech => {
          history.push(speech);
          const rr = results.find(r => r.round === speech.round) || { round: speech.round, speeches: [] };
          if (!results.includes(rr)) results.push(rr);
          rr.speeches.push(speech);
        }, null, null, null
      );
      for (const s of history) await dbSaveSpeech(debateId, s.entityId, s.round, s.content, s.content.slice(0,200), 'auto', 0);
      await dbCloseDebate(debateId);
      json(res, 200, { success: true, data: { debateId, name: name||topic, mode: mode||'free', topic, rounds, results } });
    } catch (e) { json(res, 500, { success: false, message: e.message }); }
    return true;
  }

  // 流式辩论启动
  if (p === '/api/debate/stream' && req.method === 'POST') {
    try {
      const b = await readBody(req);
      const { name, mode, topic, entities = [], rounds = 2, stances = {} } = b;
      if (!topic) { json(res, 400, { success: false, message: 'topic required' }); return true; }
      if (!Array.isArray(entities) || !entities.length) { json(res, 400, { success: false, message: 'entities required' }); return true; }
      if (entities.length > 10) { json(res, 400, { success: false, message: 'max 10' }); return true; }
      if (rounds < 1 || rounds > 10) { json(res, 400, { success: false, message: 'rounds 1-10' }); return true; }

      const debateId = await dbCreateDebate(name, topic, entities, rounds);
      const session = createSession(debateId, topic, entities, rounds, name, mode, stances);
      sessions.set(debateId, session);
      runLoop(session,
        speech => { sse(res, session, 'speech', speech); dbSaveSpeech(session.debateId, speech.entityId, speech.round, speech.content, speech.content.slice(0,200), 'auto', 0).catch(()=>{}); },
        (status, msg) => sse(res, session, 'status', { status, message: msg }),
        (event, data) => sse(res, session, event, data),
        () => { dbCloseDebate(session.debateId).catch(()=>{}); sse(res, session, 'done', { debateId: session.debateId, history: session.history }); }
      ).catch(e => console.error('[Debate] crash:', e.message));
      json(res, 200, { success: true, data: { debateId, name: name||topic, mode: mode||'human', topic, rounds, message: 'connect /api/debate/sse?debateId=' + debateId } });
    } catch (e) { json(res, 500, { success: false, message: e.message }); }
    return true;
  }

  // SSE 订阅
  if (p === '/api/debate/sse' && req.method === 'GET') {
    const debateId = parseInt(parsed.query.debateId, 10);
    const session = sessions.get(debateId);
    if (!session) { json(res, 404, { success: false, message: 'not found' }); return true; }
    res.writeHead(200, { 'Content-Type': 'text/event-stream; charset=utf-8', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'X-Accel-Buffering': 'no' });
    res.write('retry: 3000\n\n');
    res.write(`event: snapshot\ndata: ${{JSON.stringify({ status: session.status, round: session.round, history: session.history, debateId })}}\n\n`);
    session.sseClients.add(res);
    const hb = setInterval(() => { try { res.write(': ping\n\n'); } catch(e) { clearInterval(hb); } }, 15000);
    req.on('close', () => { session.sseClients.delete(res); clearInterval(hb); });
    return true;
  }

  // 人类介入
  if (p === '/api/debate/respond' && req.method === 'POST') {
    try {
      const b = await readBody(req);
      const { debateId, content, name = '人类介入者' } = b;
      const session = sessions.get(parseInt(debateId, 10));
      if (!session) { json(res, 404, { success: false, message: 'not found' }); return true; }
      if (!content?.trim()) { json(res, 400, { success: false, message: 'content required' }); return true; }
      const speech = { entityId: 'human', name, bdi: null, content, role: 'human', ts: Date.now() };
      session.responseQueue.push(speech); session.lastActivity = Date.now();
      sse(res, session, 'human_queued', { name, content, queueLen: session.responseQueue.length });
      json(res, 200, { success: true, data: { queued: true, queueLen: session.responseQueue.length } });
    } catch (e) { json(res, 500, { success: false, message: e.message }); }
    return true;
  }

  // 暂停/恢复
  if (p === '/api/debate/pause' && req.method === 'POST') {
    try {
      const b = await readBody(req);
      const { debateId, pause } = b;
      const session = sessions.get(parseInt(debateId, 10));
      if (!session) { json(res, 404, { success: false, message: 'not found' }); return true; }
      if (pause) { session.pauseRequested = true; session.lastActivity = Date.now(); json(res, 200, { success: true, data: { paused: true } }); }
      else { if (session.pauseResume) { session.pauseResume(); session.pauseResume = null; } session.lastActivity = Date.now(); json(res, 200, { success: true, data: { paused: false } }); }
    } catch (e) { json(res, 500, { success: false, message: e.message }); }
    return true;
  }

  // 状态查询
  if (p === '/api/debate/status' && req.method === 'GET') {
    const debateId = parseInt(parsed.query.debateId, 10);
    const session = sessions.get(debateId);
    if (!session) { json(res, 404, { success: false, message: 'not found' }); return true; }
    json(res, 200, { success: true, data: { debateId, status: session.status, round: session.round, totalRounds: session.rounds, historyLen: session.history.length, history: session.history } });
    return true;
  }

  // 活跃列表
  if (p === '/api/debate/live' && req.method === 'GET') {
    const live = [];
    for (const [id, s] of sessions) {
      if (s.status !== 'done' && s.status !== 'error')
        live.push({ debateId: id, status: s.status, round: s.round, totalRounds: s.rounds, mode: s.mode });
    }
    json(res, 200, { success: true, data: live });
    return true;
  }

  return false;
}

module.exports = { handleRoutes };
