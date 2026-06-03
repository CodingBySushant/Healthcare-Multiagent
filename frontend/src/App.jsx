import { useState } from 'react'
import Dashboard from './Dashboard'

export default function App() {
  const [userId, setUserId] = useState(null)
  const [user,   setUser]   = useState(null)

  return (
    <Dashboard
      userId={userId}
      user={user}
      onUserSet={(id, profile) => { setUserId(id); setUser(profile) }}
    />
  )
}
