# Entities-150 v2.0 架构文档

## 设计原则

1. **分层解耦**: config → core → services → controllers → index
2. **超时根治**: fetch + AbortController，响应级超时（非 socket 级）
3. **并发控制**: 全局 Semaphore，默认最多 5 个并发 LLM 请求
4. **退避重试**: 指数退避 + fallback 链，避免雪崩
5. **统一配置**: 一个 `.env`，`src/config/index.js` 是唯一配置源
6. **状态机清晰**: SSE 流式辩论的状态流转用显式状态机管理
7. **笔记本系统**: 替代全量历史注入，每个实体只读最近 3 条笔记

## 目录结构

```
entities-150/
├── package.json              # 依赖
├── .env                      # 环境变量（API keys, DB path, port）
├── README.md
├── STRUCTURE.md              # 本文档
├── src/
│   ├── index.js              # 入口：加载配置 → 初始化 DB → 启动 HTTP
│   ├── config/
│   │   └── index.js          # 统一配置：从 .env 加载，校验，导出
│   ├── entities/
│   │   ├── index.js          # 导出 ENTITIES_150, TOPICS, getTopologyContext
│   │   ├── data.js           # 169 个实体定义（从原 entities.js 提取）
│   │   └── topics.js         # 7 个话题定义
│   ├── core/
│   │   ├── llm.js            # LLM 调用：fetch + AbortController + Semaphore + 退避
│   │   ├── db.js             # SQLite：WAL + 串行写队列 + 连接池
│   │   └── memory.js         # 双层记忆系统（修复后，真正被调用）
│   ├── services/
│   │   ├── dialogue.js       # 单实体对话：组装 prompt → 调 LLM → 记忆提取
│   │   ├── debate.js         # 辩论引擎：同步阻塞 + SSE 流式 + 状态机
│   │   └── notebook.js       # 笔记本系统：分发笔记 + 构建上下文
│   ├── controllers/
│   │   ├── entities.js       # GET /api/entities, /api/entities/list, /api/topics
│   │   ├── dialogue.js       # POST /api/dialogue
│   │   └── debate.js         # POST/GET /api/debate/* (全部辩论端点)
│   └── utils/
│       └── http.js           # jsonResponse, readBody, CORS 头
├── data/                     # SQLite 数据库目录
├── scripts/
│   ├── debate.py             # 客户端：命令行辩论工具
│   └── debate_launcher.py    # 客户端：自动选择实体启动辩论
└── dist/                     # 前端静态文件
```

## 状态机

```
setup → running → done
           ↓
        paused ←→ running (通过 /api/debate/pause 切换)
           ↓
        awaiting_human (mode='human' 时，每轮后等待介入)
           ↓
        error (任何异常捕获后)
```

## 并发模型

- `src/core/llm.js` 维护一个全局 `Semaphore(maxConcurrent=5)`
- 所有 LLM 调用（对话 + 辩论）都通过此 Semaphore
- 后端 fallback：siliconflow → zhipu → openrouter，每次 fallback 增加 1s 延迟

## 数据流

```
HTTP Request
    ↓
Controller (路由匹配 + 参数校验)
    ↓
Service (业务逻辑：对话/辩论/笔记本)
    ↓
Core (LLM / DB / Memory)
    ↓
External API (SiliconFlow / Zhipu / OpenRouter)
```
