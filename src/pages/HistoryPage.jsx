import { useState, useEffect } from 'react'

export default function HistoryPage() {
  const [history, setHistory] = useState([])
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    const data = JSON.parse(localStorage.getItem('cagi_history') || '[]')
    setHistory(data.reverse())
  }, [])

  const clear = () => {
    if (confirm('确定清空所有历史记录？')) {
      localStorage.removeItem('cagi_history')
      setHistory([])
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 className="page-title" style={{ margin: 0 }}>历史记录</h1>
        {history.length > 0 && (
          <button className="btn btn-secondary" style={{ width: 'auto', padding: '8px 20px' }} onClick={clear}>
            清空历史
          </button>
        )}
      </div>

      {history.length === 0 && (
        <div className="card" style={{ textAlign: 'center', color: 'var(--text-dim)' }}>
          暂无历史记录，去发起讨论吧
        </div>
      )}

      {history.map((item, idx) => (
        <div key={idx} className="history-item" onClick={() => setSelected(selected === idx ? null : idx)}>
          <div className="hist-q">{item.question}</div>
          <div className="hist-meta">
            <span>{item.backend}</span>
            <span>置信度 {(item.final_answer?.confidence * 100 || 0).toFixed(0)}%</span>
            <span>{item.elapsed_seconds}s</span>
            <span style={{ color: item.is_correct === true ? 'var(--success)' : item.is_correct === false ? 'var(--error)' : 'var(--text-dimmer)' }}>
              {item.is_correct === true ? '✓ 正确' : item.is_correct === false ? '✗ 错误' : '—'}
            </span>
          </div>
          {selected === idx && (
            <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
              <div style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 8 }}>
                <strong>答案:</strong> {item.final_answer?.answer}
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-dimmer)' }}>
                归一化: {item.final_answer?.normalized_answer || '—'}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
