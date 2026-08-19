# cagi-web

CAGI 前端。React 19 + Vite 6。

## 页面

| 路由 | 组件 | 说明 |
|---|---|---|
| / | DiscussPage | 分布式讨论 |
| /history | HistoryPage | 历史记录 |
| /experts | ExpertsPage | 专家管理 |
| /status | StatusPage | 系统状态 |
| /solvay | SolvayPage | 索尔维会议 |
| /stream | StreamPage | 流式输出 |

## 代理配置

`vite.config.js`：
- dev server port: 3000
- `/api` → `http://localhost:7788`

## 构建

```bash
npm install
npm run dev      # 开发
npm run build    # 构建 → dist/
npm run preview  # 预览
```

## 部署

`dist/` → `/home/ubuntu/frontend`（nginx:80）

## 依赖

```
react ^19.0.0, react-dom ^19.0.0, react-router-dom ^7.0.0
vite ^6.0.0, @vitejs/plugin-react ^4.0.0
```
