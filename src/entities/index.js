// ====== 实体模块入口 ======
const { ENTITIES_150 } = require('./data');
const { TOPICS } = require('./topics');

const fs = require('fs');
const path = require('path');

// 拓扑坐标
let TOPOLOGY = {};
const topologyPath = path.join(__dirname, 'topology.json');
try {
  const topoData = fs.readFileSync(topologyPath, 'utf8');
  TOPOLOGY = JSON.parse(topoData);
  console.log(`[Topology] Loaded ${Object.keys(TOPOLOGY).length} agent coordinates`);
} catch (e) {
  console.warn('[Topology] topology.json not found or invalid:', e.message);
}

function getTopologyContext(entityId) {
  const coords = TOPOLOGY[entityId];
  if (!coords) return '';
  const lines = Object.entries(coords).map(([k, v]) => `${k}=${v.toFixed(2)}`).join(', ');
  return `\n[你的无限维坐标] ${lines}`;
}

function getFallback(entity, type, topic) {
  const fallbacks = {
    opening: `我是${entity.nameCn}。关于${topic.titleCn}，我的立场是：${entity.tagline}`,
    response: `我是${entity.nameCn}。我坚持我的立场：${entity.tagline}`
  };
  return fallbacks[type] || fallbacks.response;
}

function listEntities() {
  return Object.values(ENTITIES_150).map(e => ({
    id: e.id,
    name: e.name,
    nameCn: e.nameCn,
    bdiAi: e.bdiAi,
    tagline: e.tagline,
    essence: e.essence,
    field: e.field || ''
  }));
}

module.exports = {
  ENTITIES_150,
  TOPICS,
  TOPOLOGY,
  getTopologyContext,
  getFallback,
  listEntities
};
