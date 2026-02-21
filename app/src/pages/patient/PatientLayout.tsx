import { motion } from 'framer-motion'
import { Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { clearSession } from '../../api/session'
import type { Patient } from '../../types'
import Growth from './Growth'
import History from './History'
import Scan from './Scan'

const NAV = [
  { path: '/',        label: 'New Scan',        icon: '◉' },
  { path: '/history', label: 'Scan History',    icon: '≡' },
  { path: '/growth',  label: 'Healing Trend',   icon: '↗' },
]

interface Props { patient: Patient }

export default function PatientLayout({ patient }: Props) {
  const navigate  = useNavigate()
  const location  = useLocation()
  const isActive  = (p: string) => location.pathname === p

  const logout = () => { clearSession(); window.location.href = '/' }

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Sidebar */}
      <motion.aside
        initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }}
        style={{
          width: 240, flexShrink: 0, display: 'flex', flexDirection: 'column',
          background: 'rgba(255,255,255,0.02)',
          borderRight: '1px solid rgba(255,255,255,0.06)',
          padding: '1.5rem 0',
        }}
      >
        {/* Logo */}
        <div style={{ padding: '0 1.5rem', marginBottom: '2rem' }}>
          <p style={{ fontSize: '0.65rem', color: '#a78bfa', fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase', margin: 0 }}>ChroniScan</p>
          <p style={{ fontSize: '1.1rem', fontWeight: 800, color: '#f1f1f1', margin: '2px 0 0', letterSpacing: '-0.02em' }}>Patient Portal</p>
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, padding: '0 0.75rem' }}>
          {NAV.map(item => (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                padding: '0.7rem 0.75rem', borderRadius: '0.625rem',
                background: isActive(item.path) ? 'rgba(167,139,250,0.12)' : 'transparent',
                border: isActive(item.path) ? '1px solid rgba(167,139,250,0.2)' : '1px solid transparent',
                color: isActive(item.path) ? '#c4b5fd' : '#6b7280',
                fontFamily: 'inherit', fontSize: '0.875rem', fontWeight: 500,
                cursor: 'pointer', transition: 'all 0.15s', marginBottom: 4,
                textAlign: 'left',
              }}
            >
              <span style={{ fontSize: '1rem', width: 20, textAlign: 'center' }}>{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        {/* User */}
        <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
          <div style={{
            background: 'rgba(167,139,250,0.08)', borderRadius: '0.75rem',
            padding: '0.75rem', marginBottom: '0.75rem',
          }}>
            <p style={{ margin: 0, fontWeight: 700, color: '#f1f1f1', fontSize: '0.85rem' }}>{patient.name}</p>
            <p style={{ margin: '2px 0 0', color: '#6b7280', fontSize: '0.75rem' }}>
              POD {patient.post_op_day} · Age {patient.age}
            </p>
          </div>
          <button onClick={logout} style={{
            width: '100%', background: 'rgba(239,68,68,0.06)',
            border: '1px solid rgba(239,68,68,0.15)', borderRadius: '0.625rem',
            padding: '0.5rem', color: '#f87171', fontSize: '0.8rem',
            fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit',
          }}>
            Sign Out
          </button>
        </div>
      </motion.aside>

      {/* Main */}
      <main style={{ flex: 1, overflowY: 'auto', padding: '2rem 2.5rem' }}>
        <Routes>
          <Route path="/"        element={<Scan patient={patient} />} />
          <Route path="/history" element={<History patient={patient} />} />
          <Route path="/growth"  element={<Growth patient={patient} />} />
        </Routes>
      </main>
    </div>
  )
}
