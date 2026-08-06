# Entities-150 v2.0

裂缝辩论系统 — 彻底重构版。

## 快速开始

```bash
npm install
# 编辑 .env 填入 API Key
node src/index.js
```

## API

- `GET /api/entities` — 列出所有实体
- `POST /api/dialogue` — 单实体对话
- `POST /api/debate` — 同步阻塞辩论
- `POST /api/debate/stream` — 启动 SSE 流式辩论
- `GET /api/debate/sse?debateId=xxx` — SSE 订阅
- `POST /api/debate/respond` — 人类介入
- `POST /api/debate/pause` — 暂停/恢复
- `GET /api/debate/status?debateId=xxx` — 查询状态

## 客户端

```bash
python3 scripts/debate.py "素数分布的本质是什么？" -e zero,paradox,contradiction -r 3
```
