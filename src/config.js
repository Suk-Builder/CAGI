// ====== 统一配置 ======
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });

function env(key, fallback) {
  const v = process.env[key];
  if (v === undefined && fallback === undefined) console.warn(`[Config] 警告: ${key} 未设置`);
  return v !== undefined ? v : fallback;
}

const PORT = parseInt(env('PORT', '3009'), 10);
const DB_PATH = env('DB_PATH', path.join(__dirname, '../data/entities.db'));

// LLM 后端（按优先级）
const LLM_BACKENDS = [];
function add(name, keyEnv, urlEnv, modelEnv, defUrl, defModel) {
  const key = env(keyEnv);
  if (!key) return;
  LLM_BACKENDS.push({
    name, apiKey: key,
    apiUrl: env(urlEnv, defUrl),
    model: env(modelEnv, defModel),
    format: name === 'openrouter' ? 'openrouter' : 'openai'
  });
}
add('siliconflow', 'SILICONFLOW_API_KEY', 'SILICONFLOW_API_URL', 'SILICONFLOW_MODEL',
  'https://api.siliconflow.cn/v1/chat/completions', 'deepseek-ai/DeepSeek-V4-Flash');
add('zhipu', 'ZHIPU_API_KEY', 'ZHIPU_API_URL', 'ZHIPU_MODEL',
  'https://open.bigmodel.cn/api/paas/v4/chat/completions', 'glm-4-flash');
add('openrouter', 'OPENROUTER_API_KEY', 'OPENROUTER_API_URL', 'OPENROUTER_MODEL',
  'https://openrouter.ai/api/v1/chat/completions', 'deepseek/deepseek-chat');
add('aliyun', 'ALIYUN_API_KEY', 'ALIYUN_API_URL', 'ALIYUN_MODEL',
  'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', 'qwen-turbo');
add('freemodel', 'FREEMODEL_API_KEY', 'FREEMODEL_API_URL', 'FREEMODEL_MODEL',
  'https://api.freemodel.com/v1/chat/completions', 'default');
add('deepseek', 'DEEPSEEK_API_KEY', 'DEEPSEEK_API_URL', 'DEEPSEEK_MODEL',
  'https://api.deepseek.com/chat/completions', 'deepseek-chat');

if (LLM_BACKENDS.length === 0) {
  console.error('[Config] 致命错误: 没有配置任何 LLM 后端');
  process.exit(1);
}

const LLM_MAX_CONCURRENT = parseInt(env('LLM_MAX_CONCURRENT', '5'), 10);
const LLM_TIMEOUT_MS = parseInt(env('LLM_TIMEOUT_MS', '60000'), 10);
const LLM_MAX_RETRIES = parseInt(env('LLM_MAX_RETRIES', '2'), 10);

console.log(`[Config] ${LLM_BACKENDS.length} 个后端: ${LLM_BACKENDS.map(b=>b.name).join(', ')}`);
console.log(`[Config] 并发=${LLM_MAX_CONCURRENT} 超时=${LLM_TIMEOUT_MS}ms 重试=${LLM_MAX_RETRIES}`);

module.exports = { PORT, DB_PATH, LLM_BACKENDS, LLM_MAX_CONCURRENT, LLM_TIMEOUT_MS, LLM_MAX_RETRIES };
