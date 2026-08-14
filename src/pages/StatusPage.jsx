import { useState, useEffect } from 'react'

const API_URL = '/api'

const backends = [
  { key: 'nvidia', name: 'NVIDIA 550B', model: 'Nemotron 3 Ultra' },
  { key: 'mock', name: 'Mock', model: '本地模拟' },
  { key: 'glm', name: '智谱 GLM', model: 'GLM-4.7-Flash' },
  { key: 'openrouter', name: 'OpenRouter', model: 'DeepSeek-chat' },
  { key: 'modelscope', name: '魔搭', model: 'GLM-4.7-Flash' },
  { key: 'deepseek', name: 'DeepSeek', model: 'deepseek-v4-flash' },
  { key: 'siliconflow', name: 'SiliconFlow', model: 'DeepSeek-V2.5' },
  { key: 'ollama', name: 'Ollama', model: '本地模型' },
]

export default function StatusPage() {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then(r => r.json())
      .then(data => { setStatus(data); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [])

  if (loading) return <div className="loading">加载中...</div>
  if (error) return <div className="error-box">{error}</div>

  return (
    <div>
      <h1 className="page-title">后端状态</h1>

      <div className="card">
        <span className="card-label">当前默认后端</span>
        <div style={{ fontSize: 18, fontWeight: 700, color: '#fff' }}>
          {status.backend}
          <span className={`tag tag-${status.backend}`} style={{ marginLeft: 12 }}>
            {status.backend_ready ? '就绪' : '未就绪'}
          </span>
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-dimmer)', marginTop: 8 }}>
          版本: {status.version} · 可用专家: {status.n_personas} 个
        </div>
      </div>

      <div className="card">
        <span className="card-label">各后端可用性</span>
        <div className="status-grid">
          {backends.map(b => {
            const ready = status.backend_status?.[b.key]
            return (
              <div key={b.key} className={`status-item ${ready ? 'ready' : 'not-ready'}`}>
                <div className="status-name">{b.name}</div>
                <span className={`status-dot ${ready ? 'on' : 'off'}`} />
                <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>{b.model}</div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
