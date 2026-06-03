import { useEffect, useState } from 'react'
import { Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  BarElement, Tooltip,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

const MOOD_EMOJI = {
  happy:'😊', excited:'🤩', calm:'😌', neutral:'😐',
  tired:'😴', sad:'😢', anxious:'😰', irritable:'😠',
}

export default function MoodChart({ userId }) {
  const [history, setHistory] = useState([])

  useEffect(() => {
    if (!userId) return
    fetch(`/api/users/${userId}/mood?days=7`)
      .then(r => r.json())
      .then(d => setHistory(d.history.slice().reverse()))
      .catch(console.error)
  }, [userId])

  if (!history.length) return <p style={{ fontSize:12, color:'#bbb', padding:'20px 0' }}>No data yet.</p>

  const labels = history.map(h => h.logged_at.slice(5, 10))
  const scores = history.map(h => h.mood_score)
  const moods  = history.map(h => h.mood)
  const colors = scores.map(s => s >= 7 ? '#27ae60' : s >= 4 ? '#f39c12' : '#e74c3c')

  return (
    <Bar
      data={{
        labels,
        datasets: [{
          data: scores,
          backgroundColor: colors,
          borderRadius: 4,
        }],
      }}
      options={{
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => `${MOOD_EMOJI[moods[ctx.dataIndex]] || ''} ${moods[ctx.dataIndex]} (${ctx.raw}/10)`,
            },
          },
        },
        scales: {
          y: { min: 0, max: 10, grid: { color: '#f0f0f0' }, ticks: { font: { size: 10 } } },
          x: { ticks: { font: { size: 10 } } },
        },
      }}
      height={160}
    />
  )
}
