import { useEffect, useState } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  PointElement, LineElement, Tooltip, Filler,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler)

export default function CGMChart({ userId }) {
  const [history, setHistory] = useState([])

  useEffect(() => {
    if (!userId) return
    fetch(`/api/users/${userId}/cgm?limit=7`)
      .then(r => r.json())
      .then(d => setHistory(d.history.slice().reverse()))
      .catch(console.error)
  }, [userId])

  if (!history.length) return <p style={{ fontSize:12, color:'#bbb', padding:'20px 0' }}>No data yet.</p>

  const labels   = history.map(h => h.logged_at.slice(5, 16))
  const readings = history.map(h => h.reading)
  const ptColors = readings.map(v =>
    v < 80 || v > 300 ? '#e74c3c' : v < 90 || v > 180 ? '#f39c12' : '#27ae60'
  )
  const latest = readings[readings.length - 1]

  return (
    <div>
      {latest && (
        <p style={{ fontSize:12, marginBottom:8, color: latest > 180 || latest < 90 ? '#e74c3c' : '#27ae60' }}>
          Latest: <strong>{latest} mg/dL</strong>
          {(latest < 80 || latest > 300) && ' ⚠️ Out of safe range!'}
        </p>
      )}
      <Line
        data={{
          labels,
          datasets: [{
            data: readings,
            borderColor: '#1a7a4a',
            backgroundColor: 'rgba(26,122,74,0.08)',
            pointBackgroundColor: ptColors,
            pointRadius: 5,
            tension: 0.3,
            fill: true,
          }],
        }}
        options={{
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            y: { min: 60, max: 330, grid: { color: '#f0f0f0' }, ticks: { font: { size: 10 } } },
            x: { ticks: { font: { size: 9 }, maxRotation: 45 } },
          },
        }}
        height={160}
      />
      <p style={{ fontSize:10, color:'#aaa', marginTop:4 }}>
        🟢 90–180 mg/dL (target) &nbsp; 🟡 outside target &nbsp; 🔴 critical
      </p>
    </div>
  )
}
