import { useState, useEffect } from 'react'

const API_URL = '/api'

export default function ExpertsPage() {
  const [experts, setExperts] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    fetch(`${API_URL}/personas`)
      .then(r => r.json())
      .then(data => { setExperts(data.personas || []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const filtered = experts.filter(e =>
    e.domain.toLowerCase().includes(filter.toLowerCase()) ||
    e.style.toLowerCase().includes(filter.toLowerCase())
  )

  if (loading) return <div className="loading">加载专家人格...</div>

  return (
    <div>
      <h1 className="page-title">专家人格库</h1>

      <div className="card">
        <span className="card-label">搜索</span>
        <input
          className="input"
          placeholder="搜索领域或风格..."
          value={filter}
          onChange={e => setFilter(e.target.value)}
        />
        <div style={{ fontSize: 12, color: 'var(--text-dimmer)', marginTop: 8 }}>
          共 {experts.length} 个专家人格，显示 {filtered.length} 个
        </div>
      </div>

      <div className="expert-grid">
        {filtered.map(e => (
          <div key={e.persona_id} className="expert-card">
            <div className="expert-id">#{e.persona_id}</div>
            <div className="expert-domain">{e.domain}</div>
            <div className="expert-style">{e.style}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
