import { useState, useEffect, useRef } from 'react'

const API_URL = 'http://43.160.209.250:7788'

const backendOptions = [
  { value: 'nvidia', label: 'NVIDIA Nemotron 3 Ultra 550B', tag: 'tag-nvidia' },
  { value: 'mock', label: 'Mock（本地模拟）', tag: 'tag-mock' },
  { value: 'glm', label: '智谱 GLM-4.7-Flash', tag: 'tag-glm' },
  { value: 'siliconflow', label: 'SiliconFlow', tag: 'tag-siliconflow' },
]

export default function SolvayPage() {
  const [topics, setTopics] = useState([])
  const [experts, setExperts] = useState([])
  const [selectedTopic, setSelectedTopic] = useState('')
  const [nRounds, setNRounds] = useState(2)
  const [backend, setBackend] = useState('nvidia')
  const [taskId, setTaskId] = useState(null)
  const [status, setStatus] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const intervalRef = useRef(null)

  // 加载议题和专家
  useEffect(() => {
    fetch(`${API_URL}/solvay/topics`).then(r => r.json()).then(d => {
      setTopics(d.topics || [])
      if (d.topics?.length) setSelectedTopic(d.topics[0].key)
    })
    fetch(`${API_URL}/solvay/experts`).then(r => r.json()).then(d => {
      setExperts(d.experts || [])
    })
  }, [])

  // 轮询进度
  useEffect(() => {
    if (!taskId) return
    intervalRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/solvay/status/${taskId}`)
        const st = await res.json()
        setStatus(st)
        if (st.status === 'completed' || st.status === 'failed') {
          clearInterval(intervalRef.current)
          fetchResult()
        }
      } catch (e) {
        console.error(e)
      }
    }, 1500)
    return () => clearInterval(intervalRef.current)
  }, [taskId])

  const fetchResult = async () => {
    try {
      const res = await fetch(`${API_URL}/solvay/result/${taskId}`)
      const data = await res.json()
      setResult(data.result)
      setLoading(false)
    } catch (e) {
      setError('获取结果失败')
      setLoading(false)
    }
  }

  const startDebate = async () => {
    if (!selectedTopic) return
    setLoading(true)
    setError('')
    setTaskId(null)
    setStatus(null)
    setResult(null)

    try {
      const res = await fetch(`${API_URL}/solvay/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic_key: selectedTopic,
          n_rounds: parseInt(nRounds) || 2,
          backend,
        }),
      })
      const data = await res.json()
      if (data.detail) throw new Error(data.detail)
      setTaskId(data.task_id)
      setStatus({ status: 'pending', progress: { current_round: 0, total_rounds: nRounds }, debate_log_count: 0 })
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  const currentTopic = topics.find(t => t.key === selectedTopic)

  // 判断专家是否已发言
  const hasSpoken = (expertName, round) => {
    if (!status?.debate_log_count) return false
    // 从 result 或 status 推断
    if (!result?.debate_log) return false
    return result.debate_log.some(e => e.expert_name === expertName && e.round <= (status?.progress?.current_round || 0))
  }

  // 获取专家当前轮次的发言
  const getSpeech = (expertName, round) => {
    if (!result?.debate_log) return null
    return result.debate_log.find(e => e.expert_name === expertName && e.round === round)
  }

  // 共识度颜色
  const consensusColor = (score) => {
    if (score >= 0.7) return '#22c55e'
    if (score >= 0.4) return '#f59e0b'
    return '#ef4444'
  }

  return (
    <div>
      <h1 className="page-title">⚛️ 索尔维会议</h1>
      <p style={{ color: 'var(--text-dimmer)', marginBottom: 24, fontSize: 14 }}>
        1927 布鲁塞尔 · 8 位量子力学奠基人 · 多轮辩论 · 共识度分析
      </p>

      {/* 议题选择 */}
      <div className="card">
        <span className="card-label">选择议题</span>
        <div className="topic-grid">
          {topics.map(t => (
            <div
              key={t.key}
              className={`topic-card ${selectedTopic === t.key ? 'topic-active' : ''}`}
              onClick={() => setSelectedTopic(t.key)}
            >
              <div className="topic-title">{t.title}</div>
              <div className="topic-desc">{t.description}</div>
              <div className="topic-tags">
                {t.tags?.map(tag => <span key={tag} className="topic-tag">{tag}</span>)}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 配置 */}
      <div className="card">
        <div className="row">
          <div>
            <span className="card-label">讨论轮数</span>
            <input className="input" type="number" min={1} max={5} value={nRounds} onChange={e => setNRounds(e.target.value)} />
          </div>
          <div>
            <span className="card-label">后端模型</span>
            <select className="select" value={backend} onChange={e => setBackend(e.target.value)}>
              {backendOptions.map(b => <option key={b.value} value={b.value}>{b.label}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* 专家阵容 */}
      <div className="card">
        <span className="card-label">参会专家（{experts.length} 位）</span>
        <div className="expert-grid">
          {experts.map(e => (
            <div key={e.persona_id} className="expert-card">
              <div className="expert-avatar">{e.avatar}</div>
              <div className="expert-name">{e.name}</div>
              <div className="expert-domain">{e.domain}</div>
              <div className="expert-framework">{e.cognitive_framework}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 启动按钮 */}
      <div className="card">
        <button className="btn btn-large" onClick={startDebate} disabled={loading || !selectedTopic}>
          {loading ? '会议进行中...' : '🔔 敲响索尔维会议钟声'}
        </button>
      </div>

      {error && <div className="error-box">{error}</div>}

      {/* 进度面板 */}
      {loading && status && (
        <div className="card">
          <span className="card-label">会议进度</span>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{
                width: `${(status.debate_log_count / (experts.length * status.progress.total_rounds)) * 100}%`,
              }}
            />
          </div>
          <div className="progress-text">
            第 {status.progress.current_round || 0} / {status.progress.total_rounds} 轮
            · {status.debate_log_count} / {experts.length * status.progress.total_rounds} 次发言
            {status.progress.current_expert && ` · 当前: ${status.progress.current_expert}`}
          </div>

          {/* 专家发言状态 */}
          <div className="expert-status-grid">
            {experts.map(e => {
              const spoken = hasSpoken(e.name, status.progress.current_round)
              const isCurrent = status.progress.current_expert === e.name
              return (
                <div key={e.persona_id} className={`expert-status ${isCurrent ? 'speaking' : spoken ? 'done' : 'waiting'}`}>
                  <span className="expert-status-avatar">{e.avatar}</span>
                  <span className="expert-status-name">{e.name}</span>
                  <span className="expert-status-dot" />
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 结果展示 */}
      {result && (
        <>
          {/* 共识度仪表盘 */}
          <div className="card">
            <span className="card-label">会议结论</span>
            <div className="consensus-dashboard">
              <div className="consensus-gauge">
                <div className="gauge-value" style={{ color: consensusColor(result.consensus_analysis.consensus_score) }}>
                  {(result.consensus_analysis.consensus_score * 100).toFixed(0)}%
                </div>
                <div className="gauge-label">共识度</div>
                <div className="gauge-desc">
                  {result.consensus_analysis.consensus_score >= 0.7 ? '高度共识' :
                   result.consensus_analysis.consensus_score >= 0.4 ? '部分共识' : '严重分歧'}
                </div>
              </div>
              <div className="camp-chart">
                {Object.entries(result.consensus_analysis.camps).map(([camp, members]) => (
                  <div key={camp} className="camp-bar">
                    <div className="camp-label">{camp}</div>
                    <div className="camp-members">{members.join('、')}</div>
                    <div className="camp-count">{members.length} 人</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 立场光谱 */}
          <div className="card">
            <span className="card-label">立场光谱（实在论 ←→ 反实在论）</span>
            <div className="spectrum-bar">
              <div className="spectrum-track">
                {experts.map(e => {
                  const framework = e.cognitive_framework
                  const scoreMap = {
                    '形式主义': 0.3, '互补性原理': 0.2, '定域实在论': 0.9,
                    '操作主义': 0.4, '连续实在论': 0.8, '导波理论': 0.85,
                    '统计诠释': 0.5, '对称性优先': 0.6,
                  }
                  const score = scoreMap[framework] || 0.5
                  return (
                    <div
                      key={e.persona_id}
                      className="spectrum-marker"
                      style={{ left: `${score * 100}%` }}
                      title={`${e.name}: ${framework}`}
                    >
                      <span className="spectrum-avatar">{e.avatar}</span>
                      <span className="spectrum-name">{e.name}</span>
                    </div>
                  )
                })}
              </div>
              <div className="spectrum-labels">
                <span>反实在论</span>
                <span>中间</span>
                <span>强实在论</span>
              </div>
            </div>
          </div>

          {/* 辩论记录时间线 */}
          <div className="card">
            <span className="card-label">辩论记录</span>
            {Array.from({ length: result.n_rounds }, (_, ri) => ri + 1).map(round => (
              <div key={round} className="round-section">
                <div className="round-header">第 {round} 轮</div>
                <div className="timeline">
                  {result.debate_log
                    .filter(e => e.round === round)
                    .map((entry, idx) => (
                      <div key={idx} className="timeline-item">
                        <div className="timeline-avatar">{entry.expert_avatar}</div>
                        <div className="timeline-content">
                          <div className="timeline-header">
                            <span className="timeline-name">{entry.expert_name}</span>
                            <span className="timeline-framework">{entry.expert_framework}</span>
                          </div>
                          <div className="timeline-speech">{entry.content}</div>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            ))}
          </div>

          {/* 会议摘要 */}
          {result.summary && (
            <div className="card">
              <span className="card-label">{result.summary.title}</span>
              <div className="summary-meta">
                <span>📍 {result.summary.location}</span>
                <span>📅 {result.summary.date}</span>
              </div>
              <div className="summary-conclusion">{result.summary.final_consensus}</div>
              <div className="summary-speakers">
                {result.summary.most_active_speakers?.map(s => (
                  <span key={s.name} className="summary-speaker">{s.name} ({s.speeches}次)</span>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
