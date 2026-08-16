import { Routes, Route, NavLink } from 'react-router-dom'
import DiscussPage from './pages/DiscussPage.jsx'
import HistoryPage from './pages/HistoryPage.jsx'
import ExpertsPage from './pages/ExpertsPage.jsx'
import StatusPage from './pages/StatusPage.jsx'
import SolvayPage from './pages/SolvayPage.jsx'
import StreamPage from './pages/StreamPage.jsx'

function App() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-brand">CAGI</div>
        <div className="sidebar-sub">分布式精英民主<br/>投票制 AI</div>
        <ul className="sidebar-nav">
          <li><NavLink to="/" end>💬 发起讨论</NavLink></li>
          <li><NavLink to="/history">📜 历史记录</NavLink></li>
          <li><NavLink to="/experts">👥 专家人格</NavLink></li>
          <li><NavLink to="/status">🔌 后端状态</NavLink></li>
          <li><NavLink to="/solvay">⚛️ 索尔维会议</NavLink></li>
          <li><NavLink to="/stream">📡 无限流式</NavLink></li>
        </ul>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<DiscussPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/experts" element={<ExpertsPage />} />
          <Route path="/status" element={<StatusPage />} />
          <Route path="/solvay" element={<SolvayPage />} />
          <Route path="/stream" element={<StreamPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
