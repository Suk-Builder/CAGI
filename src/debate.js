// ====== 辩论引擎 + 笔记本 + 立场系统 ======
const { callLLM } = require('./core');
const { ENTITIES_150 } = require('./entities');

const STANCE_TASKS = {
  support: '在这场辩论中你支持裂缝演算。从你的理论出发，找出裂缝演算与你思想的最深共鸣点，并攻击反对者的核心弱点。',
  neutral: '在这场辩论中你客观分析。检验裂缝演算每一步推导的严谨性，指出最危险的隐含假设。',
  copenhagen: '在这场辩论中你反对裂缝演算。从你的理论出发，找出裂缝演算与你思想的最尖锐冲突点，并攻击支持者的核心弱点。',
  ally: '在这场辩论中你认同大方向但要求严格证明。指出裂缝演算中哪一步最需要补充证据，同时捍卫整体框架的可行性。'
};
const STANCE_OPENINGS = {
  support: '这是你的开篇。第一句话必须以一个直接攻击开场——例如"玻尔说裂缝演算没有解释测量——但测量本身就是离散网格中的一个自然过程。"',
  neutral: '这是你的开篇。第一句话必须提出一个分析框架——例如"这个体系最值得检验的是M2步骤的逻辑严谨性。"',
  copenhagen: '这是你的开篇。第一句话必须以一个直接批判开场——例如"哥德尔说裂缝本体=不完备定理的物理对应——但这是范畴错误。"',
  ally: '这是你的开篇。第一句话必须先认同大方向——例如"这个体系的大方向是对的，但M2需要严格证明。"'
};
const STANCE_LABELS = { support: '支持', neutral: '中立', copenhagen: '哥本哈根', ally: '共鸣' };

// ─── 笔记本 ───
function createNotebooks(ids) { const n = {}; for (const id of ids) n[id] = []; return n; }

function buildNotebook(session, entityId) {
  const notes = session.notebooks[entityId];
  if (!notes?.length) return '';
  const recent = notes.slice(-3);
  let ctx = '\n\n【笔记本——你需要回应的观点】\n';
  for (const n of recent) ctx += `\n[${n.label} · ${n.fromName} (R${n.round})]: ${n.content}`;
  ctx += '\n\n请点名回应以上观点中最有问题的那个。不要复读——每次发言必须推进辩论。';
  session.notebooks[entityId] = [];
  return ctx;
}

function distributeNotes(session, speech) {
  const stance = session.stances[speech.entityId] || 'neutral';
  const label = STANCE_LABELS[stance] || '其他';
  const name = speech.name || speech.entityId;
  for (const id of Object.keys(session.notebooks)) {
    if (id === speech.entityId) continue;
    let s = speech.content.substring(0, 200);
    if (speech.content.length > 200) s += '…';
    session.notebooks[id].push({ from: speech.entityId, fromName: name, label, content: s, round: speech.round });
  }
}

// ─── 会话 ───
function createSession(debateId, topic, entities, rounds, name, mode, stances) {
  return {
    debateId, topic, entities, rounds, name: name || topic, mode: mode || 'human',
    status: 'setup', history: [], round: 0, stances: stances || {},
    notebooks: createNotebooks(entities), responseQueue: [],
    pauseRequested: false, pauseResume: null, sseClients: new Set(),
    createdAt: Date.now(), lastActivity: Date.now()
  };
}

async function generateSpeech(session, entityId, round) {
  const entity = ENTITIES_150[entityId];
  if (!entity) return null;
  const stance = session.stances[entityId] || 'neutral';
  const task = STANCE_TASKS[stance] || STANCE_TASKS.neutral;

  let sys = (entity.systemPrompt || '') + `\n\n【辩论任务】${task}\n\n你只以 ${entity.nameCn}（${entity.name}）的身份发言，绝不出戏。你的辩论对象是裂缝演算(Crack Calculus)。`;
  let user = `【辩论对象：裂缝演算(Crack Calculus)】\n公理: ①矛盾作为本体论 ②实践作为标准 ③哥德尔不完备作为物理定律\n本体=裂缝。连续统(ℝ⁴)是10²³密度下的宏观幻觉。空间=普朗克格距的绝对离散网格。时间=轨迹索引。\n推导链M1-M9: 元胞自动机→连续化→光速可变→麦克斯韦→引力→薛定谔→质量谱→梅森链力常数→宇宙学。\n`;
  if (round === 1) user += (STANCE_OPENINGS[stance] || '');

  const nb = buildNotebook(session, entityId);
  if (nb) user += '\n' + nb;

  const t0 = Date.now();
  let content;
  try { content = await callLLM(sys, [{ role: 'user', content: user }], 800); }
  catch (e) { content = `[错误: ${e.message}]`; }

  const speech = { entityId, name: entity.nameCn, bdi: entity.bdiAi, content, round, role: 'entity', ts: Date.now() };
  session.history.push(speech);
  session.lastActivity = Date.now();
  distributeNotes(session, speech);
  return { speech, latency: Date.now() - t0 };
}

async function runLoop(session, onSpeech, onStatus, onRound, onDone) {
  session.status = 'running';
  if (onStatus) onStatus('running');
  try {
    for (let r = 1; r <= session.rounds; r++) {
      session.round = r;
      if (onRound) onRound('round_start', { round: r, total: session.rounds });
      for (const eid of session.entities) {
        if (session.pauseRequested) {
          session.status = 'paused'; if (onStatus) onStatus('paused');
          await new Promise(res => { session.pauseResume = res; });
          session.pauseRequested = false; session.status = 'running'; if (onStatus) onStatus('running');
        }
        if (session.status === 'error') return;
        const result = await generateSpeech(session, eid, r);
        if (result && onSpeech) onSpeech(result.speech);
        if (session.mode === 'human') {
          const ws = Date.now();
          while (session.responseQueue.length === 0 && Date.now() - ws < 4000)
            await new Promise(r => setTimeout(r, 200));
        }
        while (session.responseQueue.length > 0) {
          const h = session.responseQueue.shift();
          const entry = { ...h, round: r, role: 'human', ts: Date.now() };
          session.history.push(entry);
          if (onSpeech) onSpeech(entry);
          distributeNotes(session, entry);
        }
      }
      if (onRound) onRound('round_end', { round: r });
    }
    while (session.responseQueue.length > 0) {
      const h = session.responseQueue.shift();
      const entry = { ...h, role: 'human', ts: Date.now() };
      session.history.push(entry);
      if (onSpeech) onSpeech(entry);
      distributeNotes(session, entry);
    }
    session.status = 'done'; if (onDone) onDone();
  } catch (e) {
    session.status = 'error';
    console.error('[Debate]', e.message);
    if (onStatus) onStatus('error', e.message);
  }
}

module.exports = { createSession, generateSpeech, runLoop, STANCE_LABELS };
