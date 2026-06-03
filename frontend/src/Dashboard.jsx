import { useState, useRef, useEffect } from 'react'
import CGMChart  from './CGMChart'
import MoodChart from './MoodChart'

const API = '/api'

const css = `
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Arial, sans-serif; background: #f0f4f8; }
  .layout { display: flex; height: 100vh; }

  .chat-panel { width: 400px; flex-shrink: 0; display: flex; flex-direction: column; background: #fff; border-right: 1px solid #ddd; }
  .chat-header { background: #1a7a4a; color: #fff; padding: 12px 16px; font-size: 15px; font-weight: bold; flex-shrink: 0; }
  .chat-header small { display: block; font-size: 11px; font-weight: normal; opacity: 0.75; margin-top: 2px; }

  .agent-tabs { display: flex; gap: 0; border-bottom: 1px solid #ddd; background: #f9f9f9; flex-shrink: 0; }
  .agent-tab { padding: 6px 11px; font-size: 11px; border: none; background: none; cursor: pointer; color: #666; border-bottom: 2px solid transparent; white-space: nowrap; }
  .agent-tab.active { color: #1a7a4a; border-bottom-color: #1a7a4a; background: #fff; font-weight: bold; }

  .messages { flex: 1; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
  .msg-user { align-self: flex-end; background: #1a7a4a; color: #fff; padding: 8px 12px; border-radius: 14px 14px 3px 14px; font-size: 13px; max-width: 80%; word-break: break-word; }
  .msg-bot { align-self: flex-start; max-width: 86%; }
  .msg-label { font-size: 10px; color: #888; margin-bottom: 2px; font-weight: bold; text-transform: uppercase; }
  .msg-bubble { background: #f0f0f0; color: #222; padding: 8px 12px; border-radius: 3px 14px 14px 14px; font-size: 13px; line-height: 1.5; white-space: pre-wrap; word-break: break-word; }
  .thinking { color: #aaa; font-style: italic; }

  .chips { padding: 7px 10px; display: flex; flex-wrap: wrap; gap: 5px; border-top: 1px solid #eee; flex-shrink: 0; }
  .chip { font-size: 11px; padding: 3px 9px; border: 1px solid #ccc; border-radius: 12px; background: #fff; cursor: pointer; color: #444; }
  .chip:hover { border-color: #1a7a4a; color: #1a7a4a; }

  .input-bar { display: flex; gap: 7px; padding: 9px 10px; border-top: 1px solid #ddd; flex-shrink: 0; }
  .input-bar input { flex: 1; padding: 8px 12px; border: 1px solid #ccc; border-radius: 8px; font-size: 13px; outline: none; }
  .input-bar input:focus { border-color: #1a7a4a; }
  .input-bar button { padding: 8px 16px; background: #1a7a4a; color: #fff; border: none; border-radius: 8px; font-size: 13px; cursor: pointer; }
  .input-bar button:disabled { background: #aaa; cursor: not-allowed; }

  .dashboard { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
  .dash-bar { background: #fff; border-bottom: 1px solid #ddd; padding: 9px 18px; display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
  .dash-bar h1 { font-size: 16px; color: #1a7a4a; font-weight: bold; }
  .dash-bar small { font-size: 11px; color: #aaa; }
  .user-badge { margin-left: auto; background: #e6f4ed; color: #1a7a4a; padding: 3px 10px; border-radius: 10px; font-size: 12px; }

  .profile-strip { background: #fff; border-bottom: 1px solid #eee; padding: 8px 18px; display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
  .avatar { width: 34px; height: 34px; border-radius: 50%; background: #1a7a4a; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 13px; flex-shrink: 0; }
  .pname { font-size: 13px; font-weight: bold; color: #222; }
  .psub  { font-size: 11px; color: #888; }
  .tag { display: inline-block; font-size: 10px; padding: 2px 7px; border-radius: 10px; margin: 1px 2px; }
  .td { background: #e6f4ed; color: #1a7a4a; }
  .tc { background: #fdecea; color: #c0392b; }

  .dash-body { flex: 1; overflow-y: auto; padding: 18px; }
  .welcome { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; color: #aaa; }
  .welcome-icon { font-size: 54px; margin-bottom: 14px; }
  .welcome h2 { font-size: 22px; color: #333; margin-bottom: 8px; }
  .welcome p { font-size: 13px; max-width: 280px; line-height: 1.7; }

  .hello-banner { font-size: 17px; font-weight: bold; color: #333; margin-bottom: 14px; }
  .hello-banner span { color: #1a7a4a; }

  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  .card { background: #fff; border-radius: 10px; border: 1px solid #e0e0e0; padding: 14px; }
  .card-full { grid-column: 1 / -1; }
  .card h3 { font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 10px; font-weight: bold; }

  .food-form { display: flex; flex-direction: column; gap: 7px; }
  .food-form textarea { padding: 8px 11px; border: 1px solid #ccc; border-radius: 7px; font-size: 13px; resize: vertical; min-height: 58px; font-family: Arial, sans-serif; }
  .food-form textarea:focus { outline: none; border-color: #1a7a4a; }
  .food-form button { padding: 8px; background: #1a7a4a; color: #fff; border: none; border-radius: 7px; font-size: 13px; cursor: pointer; }
  .food-form button:disabled { background: #aaa; cursor: not-allowed; }
  .food-status { font-size: 12px; margin-top: 3px; }

  .mp-btn { width: 100%; padding: 11px; background: #1a7a4a; color: #fff; border: none; border-radius: 8px; font-size: 14px; cursor: pointer; font-weight: bold; }
  .mp-btn:hover { background: #155e39; }
  .mp-btn:disabled { background: #aaa; cursor: not-allowed; }

  .mp-result { margin-top: 12px; }
  .mp-rationale { font-size: 12px; color: #555; line-height: 1.6; margin-bottom: 10px; padding: 8px 10px; background: #f0f9f4; border-radius: 6px; border-left: 3px solid #1a7a4a; }
  .mp-alert { font-size: 12px; color: #c0392b; background: #fdecea; padding: 7px 10px; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid #c0392b; }
  .meal-card { border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 8px; overflow: hidden; }
  .meal-card-header { background: #1a7a4a; color: #fff; padding: 7px 12px; font-size: 12px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; }
  .meal-card-header span { font-size: 11px; font-weight: normal; opacity: 0.85; }
  .meal-card-body { padding: 10px 12px; }
  .meal-name { font-size: 13px; font-weight: bold; color: #222; margin-bottom: 5px; }
  .meal-ingredients { font-size: 11px; color: #666; margin-bottom: 6px; }
  .meal-macros { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 6px; }
  .macro-pill { font-size: 10px; padding: 2px 7px; border-radius: 10px; background: #f0f4f8; color: #444; border: 1px solid #ddd; }
  .meal-reason { font-size: 11px; color: #1a7a4a; font-style: italic; line-height: 1.5; }
  .mp-hydration { font-size: 11px; color: #0369a1; margin-top: 6px; padding: 5px 8px; background: #e0f0fb; border-radius: 5px; }

  .name-input-form { display: flex; flex-direction: column; gap: 8px; padding: 12px; border-top: 1px solid #eee; flex-shrink: 0; }
  .name-input-form input { padding: 9px 12px; border: 1px solid #ccc; border-radius: 8px; font-size: 13px; outline: none; }
  .name-input-form input:focus { border-color: #1a7a4a; }
  .name-input-form button { padding: 9px; background: #1a7a4a; color: #fff; border: none; border-radius: 8px; font-size: 13px; cursor: pointer; font-weight: bold; }
  .name-input-form button:disabled { background: #aaa; cursor: not-allowed; }
`

const AGENT_COLORS = {
  GreetingAgent:    '#1a7a4a',
  MoodTrackerAgent: '#7c3aed',
  CGMAgent:         '#0369a1',
  InterruptAgent:   '#92400e',
  System:           '#6b7280',
}

function MealPlanCard({ plan, userId, onMealSwapped }) {
  if (!plan) return null
  const { plan_reason, meals, hydration_tip, alert } = plan.plan || plan
  const [swapInputs,  setSwapInputs]  = useState({})
  const [swapLoading, setSwapLoading] = useState({})
  const [swapMsg,     setSwapMsg]     = useState({})

  const handleSwap = async (mealType) => {
    const ingredient = (swapInputs[mealType] || '').trim()
    if (!ingredient) return
    setSwapLoading(prev => ({ ...prev, [mealType]: true }))
    setSwapMsg(prev => ({ ...prev, [mealType]: '' }))
    try {
      const res = await fetch(`${API}/meal-swap`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          meal_type: mealType,
          requested_ingredient: ingredient,
          current_plan: plan.plan || plan,
        }),
      })
      const data = await res.json()
      if (data.swapped) {
        setSwapMsg(prev => ({ ...prev, [mealType]: '✅ Meal swapped!' }))
        setSwapInputs(prev => ({ ...prev, [mealType]: '' }))
        if (onMealSwapped) onMealSwapped(mealType, data.meal)
      } else {
        setSwapMsg(prev => ({ ...prev, [mealType]: '⚠️ ' + data.reason }))
      }
    } catch {
      setSwapMsg(prev => ({ ...prev, [mealType]: '❌ Could not process swap.' }))
    } finally {
      setSwapLoading(prev => ({ ...prev, [mealType]: false }))
    }
  }

  return (
    <div className="mp-result">
      {plan_reason && <div className="mp-rationale">{plan_reason}</div>}
      {alert && <div className="mp-alert">⚠️ {alert}</div>}
      {(meals || []).map((m, i) => (
        <div key={i} className="meal-card">
          <div className="meal-card-header">
            {m.meal_type}
            <span>{m.macros?.calories_kcal} kcal</span>
          </div>
          <div className="meal-card-body">
            <div className="meal-name">{m.name}</div>
            <div className="meal-ingredients">{(m.ingredients || []).join(', ')}</div>
            <div className="meal-macros">
              <span className="macro-pill">🍞 {m.macros?.carbs_g}g carbs</span>
              <span className="macro-pill">💪 {m.macros?.protein_g}g protein</span>
              <span className="macro-pill">🧈 {m.macros?.fat_g}g fat</span>
            </div>
            <div className="meal-reason">Why: {m.reason}</div>
            {/* Swap row */}
            <div style={{ display:'flex', gap:6, marginTop:8, alignItems:'center' }}>
              <input
                value={swapInputs[m.meal_type] || ''}
                onChange={e => setSwapInputs(prev => ({ ...prev, [m.meal_type]: e.target.value }))}
                onKeyDown={e => e.key === 'Enter' && handleSwap(m.meal_type)}
                placeholder={`Swap ${m.meal_type} ingredient... (e.g. mutton)`}
                style={{ flex:1, padding:'5px 9px', border:'1px solid #ccc', borderRadius:6,
                         fontSize:11, outline:'none' }}
              />
              <button
                onClick={() => handleSwap(m.meal_type)}
                disabled={swapLoading[m.meal_type] || !swapInputs[m.meal_type]?.trim()}
                style={{ padding:'5px 10px', background:'#1a7a4a', color:'#fff',
                         border:'none', borderRadius:6, fontSize:11, cursor:'pointer',
                         whiteSpace:'nowrap' }}>
                {swapLoading[m.meal_type] ? '…' : '🔄 Swap'}
              </button>
            </div>
            {swapMsg[m.meal_type] && (
              <p style={{ fontSize:11, marginTop:4,
                          color: swapMsg[m.meal_type].startsWith('✅') ? '#1a7a4a' :
                                 swapMsg[m.meal_type].startsWith('⚠️') ? '#b45309' : '#c0392b' }}>
                {swapMsg[m.meal_type]}
              </p>
            )}
          </div>
        </div>
      ))}
      {hydration_tip && <div className="mp-hydration">💧 {hydration_tip}</div>}
    </div>
  )
}

export default function Dashboard({ userId, user, onUserSet }) {
  const [messages,    setMessages]    = useState([])
  const [input,       setInput]       = useState('')
  const [loading,     setLoading]     = useState(false)
  const [nameInput,   setNameInput]   = useState('')
  const [nameLoading, setNameLoading] = useState(false)
  const [foodDesc,    setFoodDesc]    = useState('')
  const [foodStatus,  setFoodStatus]  = useState('')
  const [foodLoading, setFoodLoading] = useState(false)
  const [mealData,    setMealData]    = useState(null)
  const [mealLoading, setMealLoading] = useState(false)
  const [mealPhase,   setMealPhase]   = useState('idle')
  const [prefInput,   setPrefInput]   = useState('')
  const [meal2Data,   setMeal2Data]   = useState(null)
  const [meal2Loading,setMeal2Loading]= useState(false)
  const [cgmRefresh,  setCgmRefresh]  = useState(0)
  const [moodRefresh, setMoodRefresh] = useState(0)
  const bottomRef = useRef(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, loading])

  // ID login
  const handleLogin = async () => {
    const uid = parseInt(nameInput.trim())
    if (!uid || uid < 1 || uid > 100) {
      setMessages([{ role: 'bot', agent: 'System', text: 'Please enter a valid User ID between 1 and 100.' }])
      return
    }
    setNameLoading(true)
    try {
      const res  = await fetch(`${API}/login-id`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: uid }),
      })
      const data = await res.json()
      if (data.valid) {
        onUserSet(data.user.id, data.user)
        setMessages([{ role: 'bot', agent: 'GreetingAgent', text: data.message }])
        setNameInput('')
      } else {
        setMessages([{ role: 'bot', agent: 'System', text: data.message }])
      }
    } catch {
      setMessages([{ role: 'bot', agent: 'System', text: '⚠️ Could not reach backend.' }])
    } finally {
      setNameLoading(false)
    }
  }

  // Chat send (mood / cgm / interrupt only)
  const sendMsg = async (text) => {
    const msg = text || input.trim()
    if (!msg || loading || !userId) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: msg }])
    setLoading(true)
    try {
      const res  = await fetch(`${API}/chat`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, message: msg }),
      })
      const data = await res.json()
      setMessages(prev => [...prev, { role: 'bot', agent: data.agent, text: data.message }])
      if (data.agent === 'CGMAgent')         setCgmRefresh(v => v + 1)
      if (data.agent === 'MoodTrackerAgent') setMoodRefresh(v => v + 1)
    } catch {
      setMessages(prev => [...prev, { role: 'bot', agent: 'System', text: '⚠️ Error.' }])
    } finally {
      setLoading(false)
    }
  }

  // Food log
  const logFood = async () => {
    if (!foodDesc.trim() || !userId) return
    setFoodLoading(true)
    setFoodStatus('')
    try {
      const res  = await fetch(`${API}/food-log`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, message: `I ate: ${foodDesc}` }),
      })
      const data = await res.json()
      setFoodStatus('✅ ' + data.message)
      setFoodDesc('')
    } catch {
      setFoodStatus('❌ Failed to log.')
    } finally {
      setFoodLoading(false)
    }
  }

  // Meal plan — phase 1
  const getMealPlan = async () => {
    if (!userId) {
      setMealData({ error: '❌ Please log in first.' })
      return
    }
    setMealLoading(true)
    setMealData(null)
    setMeal2Data(null)
    setMealPhase('idle')
    setPrefInput('')
    try {
      const res = await fetch(`${API}/meal-plan`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, message: 'generate' }),
      })
      const data = await res.json()
      if (!res.ok) {
        setMealData({ error: '❌ ' + (data.detail || 'Could not generate meal plan.') })
        setMealPhase('idle')
        return
      }
      setMealData(data)
      setMealPhase('asking')
    } catch (e) {
      setMealData({ error: '❌ Network error: ' + e.message })
      setMealPhase('idle')
    } finally {
      setMealLoading(false)
    }
  }

  // Meal plan — phase 2 (custom preference)
  const getMealPlan2 = async () => {
    if (!userId || !prefInput.trim()) return
    const pref = prefInput.trim()
    setMeal2Loading(true)
    setMealData(null)
    setMeal2Data(null)
    setPrefInput('')
    try {
      const res = await fetch(`${API}/meal-plan`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, message: pref }),
      })
      if (!res.ok) throw new Error()
      const data = await res.json()
      data._pref_label = pref
      setMeal2Data(data)
      setMealPhase('asking')
    } catch {
      setMeal2Data({ error: '❌ Could not generate plan.' })
    } finally {
      setMeal2Loading(false)
    }
  }

  const visibleMsgs = messages

  const CHIPS = userId ? [
    "I'm feeling happy 😊",
    "I'm feeling tired 😴",
    "My glucose is 140 📊",
    "My glucose is 240 ⚠️",
    "What is HbA1c? ❓",
    "What is the normal blood sugar range? ❓",
  ] : []

  const initials = user ? `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}` : '?'

  return (
    <>
      <style>{css}</style>
      <div className="layout">

        {/* ── Left: Chat Panel ── */}
        <div className="chat-panel">
          <div className="chat-header">
            🩺 HealthPulse Assistant
            <small>Agno · CopilotKit AG-UI · Groq LLaMA 3.3</small>
          </div>

          {/* Messages */}
          <div className="messages">
            {!userId && messages.length === 0 && (
              <div className="msg-bot">
                <div className="msg-label" style={{ color: '#6b7280' }}>System</div>
                <div className="msg-bubble">
                  👋 Welcome! Enter your first name below to get started.
                </div>
              </div>
            )}
            {visibleMsgs.map((m, i) => (
              m.role === 'user'
                ? <div key={i} className="msg-user">{m.text}</div>
                : <div key={i} className="msg-bot">
                    <div className="msg-label"
                         style={{ color: AGENT_COLORS[m.agent] || '#888' }}>
                      {m.agent}
                    </div>
                    <div className="msg-bubble">{m.text}</div>
                  </div>
            ))}
            {loading && (
              <div className="msg-bot">
                <div className="msg-label">Assistant</div>
                <div className="msg-bubble thinking">Thinking…</div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Quick chips */}
          {userId && CHIPS.length > 0 && messages.length <= 2 && (
            <div className="chips">
              {CHIPS.map(c => (
                <button key={c} className="chip" onClick={() => sendMsg(c)}>{c}</button>
              ))}
            </div>
          )}

          {/* Name login form (before login) */}
          {!userId ? (
            <div className="name-input-form">
              <input
                value={nameInput}
                onChange={e => setNameInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleLogin()}
                placeholder="Enter your User ID (1–100)..."
                type="number"
                min="1"
                max="100"
              />
              <button onClick={handleLogin} disabled={nameLoading || !nameInput.trim()}>
                {nameLoading ? 'Looking up…' : 'Get Started'}
              </button>
            </div>
          ) : (
            /* Chat input (after login) */
            <div className="input-bar">
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && sendMsg()}
                placeholder="Log mood, glucose, or ask a question..."
              />
              <button onClick={() => sendMsg()} disabled={loading}>Send</button>
            </div>
          )}
        </div>

        {/* ── Right: Dashboard ── */}
        <div className="dashboard">
          <div className="dash-bar">
            <h1>🩺 HealthPulse</h1>
            <small>Personal Health Dashboard</small>
            {userId && <div className="user-badge">User #{userId}</div>}
          </div>

          {user && (
            <div className="profile-strip">
              <div className="avatar">{initials}</div>
              <div>
                <div className="pname">{user.first_name} {user.last_name}</div>
                <div className="psub">📍 {user.city}</div>
              </div>
              <div style={{ marginLeft: 8 }}>
                <span className="tag td">{user.dietary_pref}</span>
                {(user.conditions || []).filter(c => c !== 'None').map(c => (
                  <span key={c} className="tag tc">{c}</span>
                ))}
              </div>
            </div>
          )}

          <div className="dash-body">
            {!userId ? (
              <div className="welcome">
                <div className="welcome-icon">🩺</div>
                <h2>Welcome to HealthPulse</h2>
                <p>
                  Your personal AI health assistant.<br />
                  Enter your <strong>User ID (1–100)</strong> in the chat panel on the left to get started.
                </p>
              </div>
            ) : (
              <>
                <div className="hello-banner">
                  Hello, <span>{user?.first_name}!</span> How can I assist you today?
                </div>
                <div className="grid">
                  <div className="card">
                    <h3>📈 CGM readings — past week</h3>
                    <CGMChart userId={userId} key={`cgm-${cgmRefresh}`} />
                  </div>
                  <div className="card">
                    <h3>😊 Mood scores — past week</h3>
                    <MoodChart userId={userId} key={`mood-${moodRefresh}`} />
                  </div>
                  <div className="card">
                    <h3>🥗 Log Food</h3>
                    <div className="food-form">
                      <textarea
                        value={foodDesc}
                        onChange={e => setFoodDesc(e.target.value)}
                        placeholder="Describe what you ate, e.g. 2 rotis with dal and sabzi..."
                        rows={2}
                      />
                      <button onClick={logFood} disabled={!foodDesc.trim() || foodLoading}>
                        {foodLoading ? 'Logging…' : 'Submit Food Entry'}
                      </button>
                      {foodStatus && <div className="food-status">{foodStatus}</div>}
                    </div>
                  </div>
                  <div className="card">
                    <h3>🍽️ Generate Meal Plan</h3>
                    <p style={{ fontSize: 12, color: '#888', marginBottom: 8, lineHeight: 1.5 }}>
                      Personalised 3-meal plan based on your medical conditions,
                      dietary preference, and latest glucose — with a reason for each meal.
                    </p>
                    <button className="mp-btn" onClick={getMealPlan} disabled={mealLoading}>
                      {mealLoading ? 'Generating…' : '🍽️ Generate Meal Plan'}
                    </button>

                    {/* Active plan — whichever is latest */}
                    {(meal2Loading || mealLoading) && (
                      <p style={{ fontSize: 12, color: '#888', marginTop: 10 }}>Generating plan…</p>
                    )}

                    {(meal2Data || mealData) && !(meal2Data?.error || mealData?.error) && (
                      <>
                        {meal2Data?._pref_label && (
                          <p style={{ fontSize: 11, color: '#555', fontWeight: 'bold', marginTop: 10, marginBottom: 4 }}>
                            Plan based on "{meal2Data._pref_label}":
                          </p>
                        )}
                        <MealPlanCard
                          plan={meal2Data || mealData}
                          userId={userId}
                          onMealSwapped={(mealType, newMeal) => {
                            const active = meal2Data || mealData
                            const updated = JSON.parse(JSON.stringify(active))
                            const planObj = updated.plan || updated
                            planObj.meals = planObj.meals.map(m =>
                              m.meal_type === mealType ? newMeal : m
                            )
                            if (meal2Data) setMeal2Data(updated)
                            else setMealData(updated)
                          }}
                        />

                        {/* Always-visible preference follow-up */}
                        {mealPhase === 'asking' && (
                          <div style={{ marginTop: 12, padding: '10px 12px', background: '#f0f9f4', borderRadius: 8, border: '1px solid #b2dfcb' }}>
                            <p style={{ fontSize: 12, color: '#1a7a4a', fontWeight: 'bold', marginBottom: 4 }}>
                              Would you like a plan with a different preference?
                            </p>
                            <p style={{ fontSize: 11, color: '#555', marginBottom: 7 }}>
                              e.g. high protein, low carb, keto, vegan, no dairy…
                            </p>
                            <div style={{ display: 'flex', gap: 6 }}>
                              <input
                                value={prefInput}
                                onChange={e => setPrefInput(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && getMealPlan2()}
                                placeholder="Enter preference…"
                                style={{ flex: 1, padding: '7px 10px', border: '1px solid #ccc', borderRadius: 6, fontSize: 12, outline: 'none' }}
                              />
                              <button
                                onClick={getMealPlan2}
                                disabled={meal2Loading || !prefInput.trim()}
                                style={{ padding: '7px 12px', background: '#1a7a4a', color: '#fff', border: 'none', borderRadius: 6, fontSize: 12, cursor: 'pointer', whiteSpace: 'nowrap' }}>
                                {meal2Loading ? '…' : 'Suggest'}
                              </button>
                            </div>
                          </div>
                        )}
                      </>
                    )}

                    {(mealData?.error || meal2Data?.error) && (
                      <div className="mp-alert" style={{ marginTop: 10 }}>
                        {mealData?.error || meal2Data?.error}
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
