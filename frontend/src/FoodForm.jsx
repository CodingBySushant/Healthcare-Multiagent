import { useState } from 'react'

export default function FoodForm({ userId }) {
  const [desc,    setDesc]    = useState('')
  const [time,    setTime]    = useState('')
  const [status,  setStatus]  = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async () => {
    if (!desc.trim()) return
    setLoading(true)
    setStatus('')
    const msg = time ? `I ate: ${desc} at ${time}` : `I ate: ${desc}`
    try {
      const res  = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, message: msg }),
      })
      const data = await res.json()
      setStatus('✅ Logged!')
      setDesc(''); setTime('')
    } catch {
      setStatus('❌ Could not log entry.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
      <textarea
        value={desc}
        onChange={e => setDesc(e.target.value)}
        placeholder="e.g. 2 rotis with dal and sabzi..."
        rows={2}
        style={{ padding:'8px 10px', border:'1px solid #ccc', borderRadius:6,
                 fontSize:13, resize:'vertical', fontFamily:'Arial,sans-serif' }}
      />
      <input
        type="datetime-local" value={time}
        onChange={e => setTime(e.target.value)}
        style={{ padding:'6px 10px', border:'1px solid #ccc', borderRadius:6, fontSize:12 }}
      />
      <button
        onClick={submit}
        disabled={!desc.trim() || loading}
        style={{ padding:'8px', background: loading ? '#aaa' : '#1a7a4a',
                 color:'#fff', border:'none', borderRadius:6,
                 fontSize:13, cursor: loading ? 'not-allowed' : 'pointer' }}
      >
        {loading ? 'Logging…' : 'Log Meal'}
      </button>
      {status && <p style={{ fontSize:12, color: status.startsWith('✅') ? '#27ae60' : '#e74c3c' }}>{status}</p>}
    </div>
  )
}
