import { useState, useEffect } from 'react'

const API_URL = '/api'

const backends = [
  { value: 'nvidia', label: 'NVIDIA Nemotron 3 Ultra 550B', tag: 'tag-nvidia' },
  { value: 'mock', label: 'Mock（本地模拟）', tag: 'tag-mock' },
  { value: 'glm', label: '智谱 GLM-4.7-Flash', tag: 'tag-glm' },
  { value: 'openrouter', label: 'OpenRouter', tag: 'tag-openrouter' },
  { value: 'modelscope', label: '魔搭 ModelScope', tag: 'tag-modelscope' },
  { value: 'deepseek', label: 'DeepSeek', tag: 'tag-deepseek' },
]

export default function DiscussPage() {
  const [question, setQuestion] = useState('1+1等于几？')
  const [groundTruth, setGroundTruth] = useState('2')
  const [backend, setBackend] = useState('nvidia')
  const [nInstances, setNInstances] = useState(3)
  const [nRounds, setNRounds] = useState(1)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [logs, setLogs] = useState([])

  const addLog = (msg) => setLogs(prev => [...prev, msg])

  const submit = async () => {
    if (!question.trim()) return
    setLoading(true)
    setResult(null)
    setError('')
    setLogs([`[系统] 正在召集 ${nInstances} 位专家...`])

    try {
      const res = await fetch(`${API_URL}/discuss`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: question.trim(),
          ground_truth: groundTruth.trim() || null,
          n_instances: parseInt(nInstances) || 3,
          n_rounds: parseInt(nRounds) || 1,
          backend,
        }),
      })
      const data = await res.json()
      if (data.detail) throw new Error(data.detail)

      setResult(data)
      addLog(`[系统] 讨论完成，投票收敛于: ${data.final_answer?.normalized_answer || data.final_answer?.answer}`)

      // 保存到历史
      const history = JSON.parse(localStorage.getItem('cagi_history') || '[]')
      history.push(data)
      localStorage.setItem('cagi_history', JSON.stringify(history))
    } catch (err) {
      setError(err.message)
      addLog(`[错误] ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="page-title">发起讨论</h1>

      <div className="card">
        <span className="card-label">问题</span>
        <textarea
          className="textarea"
          value={question}
          onChange={e => setQuestion(e.target.value)}
          placeholder="输入你的问题..."
        />
      </div>

      <div className="card">
        <div className="row">
          <div>
            <span className="card-label">正确答案（可选）</span>
            <input className="input" value={groundTruth} onChange={e => setGroundTruth(e.target.value)} placeholder="用于验证" />
          </div>
          <div>
            <span className="card-label">后端</span>
            <select className="select" value={backend} onChange={e => setBackend(e.target.value)}>
              {backends.map(b => <option key={b.value} value={b.value}>{b.label}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="row">
          <div>
            <span className="card-label">专家数量</span>
            <input className="input" type="number" min={1} max={150} value={nInstances} onChange={e => setNInstances(e.target.value)} />
          </div>
          <div>
            <span className="card-label">讨论轮数</span>
            <input className="input" type="number" min={1} max={10} value={nRounds} onChange={e => setNRounds(e.target.value)} />
          </div>
        </div>
      </div>

      <div className="card">
        <button className="btn" onClick={submit} disabled={loading}>
          {loading ? '讨论中...' : '发起讨论 + 投票'}
        </button>
      </div>

      {loading && logs.length > 0 && (
        <div className="card">
          <span className="card-label">实时日志</span>
          <div className="discussion-log">
            {logs.map((log, i) => (
              <div key={i} className="log-entry">{log}</div>
            ))}
          </div>
        </div>
      )}

      {error && <div className="error-box">{error}</div>}

      {result && (
        <div className="card">
          <div className="result-answer">
            <div className="ans-label">
              最终答案
              <span className={`tag ${backends.find(b => b.value === result.backend)?.tag || 'tag-mock'}`} style={{ marginLeft: 12 }}>
                {result.backend}
              </span>
            </div>
            <div className="ans-value">{result.final_answer?.answer}</div>
            {result.final_answer?.normalized_answer && (
              <div style={{ fontSize: 13, color: 'var(--text-dimmer)', marginTop: 8 }}>
                归一化: {result.final_answer.normalized_answer}
              </div>
            )}
          </div>

          <div className="meta-grid">
            <div className="meta-item">
              <div className="meta-label">是否正确</div>
              <div className={`meta-value ${result.is_correct === true ? 'correct' : result.is_correct === false ? 'wrong' : ''}`}>
                {result.is_correct === true ? '✓' : result.is_correct === false ? '✗' : '—'}
              </div>
            </div>
            <div className="meta-item">
              <div className="meta-label">置信度</div>
              <div className="meta-value">{(result.final_answer?.confidence * 100 || 0).toFixed(0)}%</div>
            </div>
            <div className="meta-item">
              <div className="meta-label">耗时</div>
              <div className="meta-value">{result.elapsed_seconds}s</div>
            </div>
          </div>

          <span className="card-label">投票分布</span>
          <div className="vote-list">
            {Object.entries(result.final_answer?.vote_distribution || {}).map(([ans, count]) => (
              <div key={ans} className="vote-item">
                <span className="vote-ans" title={ans}>{ans}</span>
                <span className="vote-count">{count} 票</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
