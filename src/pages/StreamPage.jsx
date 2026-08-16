import { useState, useEffect, useRef } from 'react'

const API_URL = 'http://43.160.209.250:7788'

const backendOptions = [
  { value: 'nvidia', label: 'NVIDIA Nemotron 3 Ultra 550B' },
  { value: 'mock', label: 'Mock（本地模拟）' },
  { value: 'siliconflow', label: 'SiliconFlow' },
]

export default function StreamPage() {
  const [topics, setTopics] = useState([])
  const [selectedTopic, setSelectedTopic] = useState('')
  const [backend, setBackend] = useState('nvidia')
  const [isRunning, setIsRunning] = useState(false)
  const [currentRound, setCurrentRound] = useState(0)
  const [consensusScore, setConsensusScore] = useState(0)
  const [speeches, setSpeeches] = useState([])
  const [logs, setLogs] = useState([])
  const [error, setError] = useState('')
  const [taskId, setTaskId] = useState(null)
  const scrollRef = useRef(null)
  const evtSourceRef = useRef(null)

  // 加载议题
  useEffect(() => {
    fetch(`${API_URL}/solvay/topics`).then(r => r.json()).then(d => {
      setTopics(d.topics || [])
      if (d.topics?.length) setSelectedTopic(d.topics[0].key)
    })
  }, [])

  // 自动滚动到底部
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [speeches])

  const addLog = (msg) => {
    setLogs(prev => [...prev.slice(-50), { time: new Date().toLocaleTimeString(), msg }])
  }

  const startStream = async () => {
    if (!selectedTopic || isRunning) return
    setIsRunning(true)
    setError('')
    setSpeeches([])
    setLogs([])
    setCurrentRound(0)
    setConsensusScore(0)

    try {
      // 1. 启动辩论
      addLog('正在启动无限流式辩论...')
      const res = await fetch(`${API_URL}/solvay/stream/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic_key: selectedTopic, backend }),
      })
      const data = await res.json()
      if (data.detail) throw new Error(data.detail)

      setTaskId(data.task_id)
      addLog(`辩论启动: ${data.task_id}`)
      addLog(`议题: ${data.message}`)

      // 2. 连接 SSE
      const evtSource = new EventSource(`${API_URL}${data.stream_url}`)
      evtSourceRef.current = evtSource

      evtSource.addEventListener('connected', (e) => {
        addLog('SSE 连接成功')
      })

      evtSource.addEventListener('round_start', (e) => {
        const d = JSON.parse(e.data)
        setCurrentRound(d.round)
        addLog(`第 ${d.round} 轮开始`)
      })

      evtSource.addEventListener('speech', (e) => {
        const d = JSON.parse(e.data)
        setSpeeches(prev => [...prev, d])
      })

      evtSource.addEventListener('consensus', (e) => {
        const d = JSON.parse(e.data)
        setConsensusScore(d.consensus_score)
        addLog(`第 ${d.round} 轮共识度: ${(d.consensus_score * 100).toFixed(0)}%`)
      })

      evtSource.addEventListener('auto_stop', (e) => {
        const d = JSON.parse(e.data)
        addLog(`自动停止: ${d.reason}`)
        setIsRunning(false)
        evtSource.close()
      })

      evtSource.addEventListener('completed', (e) => {
        const d = JSON.parse(e.data)
        addLog(`辩论结束！共 ${d.total_rounds} 轮，${d.total_speeches} 条发言`)
        setIsRunning(false)
        evtSource.close()
      })

      evtSource.addEventListener('error', (e) => {
        addLog('SSE 错误，连接断开')
        setIsRunning(false)
        setError('SSE 连接错误')
      })

      evtSource.onerror = () => {
        addLog('SSE 连接中断')
        setIsRunning(false)
        evtSource.close()
      }

    } catch (err) {
      setError(err.message)
      setIsRunning(false)
    }
  }

  const stopStream = async () => {
    if (!taskId) return
    try {
      await fetch(`${API_URL}/solvay/stream/${taskId}/stop`, { method: 'POST' })
      addLog('已发送停止信号')
      if (evtSourceRef.current) {
        evtSourceRef.current.close()
      }
      setIsRunning(false)
    } catch (e) {
      setError('停止失败')
    }
  }

  const currentTopic = topics.find(t => t.key === selectedTopic)

  // 共识度颜色
  const consensusColor = (score) => {
    if (score >= 0.7) return '#22c55e'
    if (score >= 0.4) return '#f59e0b'
    return '#ef4444'
  }

  return (
    <div>
      <h1 className="page-title">📡 无限流式辩论</h1>
      <p style={{ color: 'var(--text-dimmer)', marginBottom: 24, fontSize: 14 }}>
        12 位专家实时交锋 · SSE 流式推送 · 无限轮次
      </p>

      {/* 配置面板 */}
      <div className="card">
        <div className="row">
          <div style={{ flex: 2 }}>
            <span className="card-label">选择议题</span>
            <div className="topic-grid">
              {topics.map(t => (
                <div
                  key={t.key}
                  className={`topic-card ${selectedTopic === t.key ? 'topic-active' : ''}`}
                  onClick={() => !isRunning && setSelectedTopic(t.key)}
                >
                  <div className="topic-title">{t.title}</div>
                </div>
              ))}
            </div>
          </div>
          <div>
            <span className="card-label">后端模型</span>
            <select className="select" value={backend} onChange={e => !isRunning && setBackend(e.target.value)} disabled={isRunning}>
              {backendOptions.map(b => <option key={b.value} value={b.value}>{b.label}</option>)}
            </select>
          </div>
        </div>

        <div style={{ marginTop: 16, display: 'flex', gap: 12 }}>
          <button className="btn btn-large" onClick={startStream} disabled={isRunning || !selectedTopic}>
            {isRunning ? '🔴 辩论进行中...' : '▶️ 启动无限流式辩论'}
          </button>
          {isRunning && (
            <button className="btn btn-danger" onClick={stopStream} style={{ background: '#ef4444' }}>
              ⏹ 停止
            </button>
          )}
        </div>
      </div>

      {error && <div className="error-box">{error}</div>}

      {/* 实时仪表盘 */}
      {isRunning && (
        <div className="card">
          <div className="stream-dashboard">
            <div className="dash-item">
              <div className="dash-label">议题</div>
              <div className="dash-value">{currentTopic?.title}</div>
            </div>
            <div className="dash-item">
              <div className="dash-label">当前轮次</div>
              <div className="dash-value" style={{ fontSize: 32, color: 'var(--accent)' }}>{currentRound}</div>
            </div>
            <div className="dash-item">
              <div className="dash-label">共识度</div>
              <div className="dash-value" style={{ fontSize: 32, color: consensusColor(consensusScore) }}>
                {(consensusScore * 100).toFixed(0)}%
              </div>
            </div>
            <div className="dash-item">
              <div className="dash-label">发言数</div>
              <div className="dash-value" style={{ fontSize: 32 }}>{speeches.length}</div>
            </div>
          </div>
        </div>
      )}

      {/* 实时发言流 */}
      {speeches.length > 0 && (
        <div className="card">
          <span className="card-label">实时发言流</span>
          <div className="stream-container" ref={scrollRef}>
            {speeches.map((s, i) => (
              <div key={i} className="stream-speech">
                <div className="stream-speech-header">
                  <span className="stream-avatar">{s.expert_avatar}</span>
                  <span className="stream-name">{s.expert_name}</span>
                  <span className="stream-framework">{s.expert_framework}</span>
                  <span className="stream-round">第{s.round}轮</span>
                </div>
                <div className="stream-content">{s.content}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 系统日志 */}
      {logs.length > 0 && (
        <div className="card">
          <span className="card-label">系统日志</span>
          <div className="stream-logs">
            {logs.map((l, i) => (
              <div key={i} className="stream-log-item">
                <span className="stream-log-time">{l.time}</span>
                <span className="stream-log-msg">{l.msg}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
