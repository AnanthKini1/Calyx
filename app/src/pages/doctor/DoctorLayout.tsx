import { motion } from 'framer-motion'
import { useState } from 'react'
import { clearSession } from '../../api/session'
import type { Doctor } from '../../types'
import Alerts from './Alerts'
import Overview from './Overview'
import PatientDetail from './PatientDetail'

const NAV = [
  { key: 'overview', label: 'Patient Overview', icon: '◈' },
  { key: 'alerts',   label: 'Active Alerts',    icon: '⚡' },
]

interface Props { doctor: Doctor }

export default function DoctorLayout({ doctor }: Props) {
  const [page, setPage]             = useState('overview')
  const [selectedPid, setSelectedPid] = useState<string | null>(null)

  const logout = () => { clearSession(); window.location.href = '/' }

  const isActive = (k: string) => page === k && !selectedPid

  const goToPatient = (pid: string) => { setSelectedPid(pid); setPage('detail') }
  const goBack      = () => { setSelectedPid(null); setPage('overview') }

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
        <div style={{ padding: '0 1.5rem', marginBottom: '2rem' }}>
          <p style={{ fontSize: '0.65rem', color: '#a78bfa', fontWeight: 700, letterSpacing: '0.2em', textTransform: 'uppercase', margin: 0 }}>ChroniScan</p>
          <p style={{ fontSize: '1.1rem', fontWeight: 800, color: '#f1f1f1', margin: '2px 0 0', letterSpacing: '-0.02em' }}>Clinical Dashboard</p>
        </div>

        <nav style={{ flex: 1, padding: '0 0.75rem' }}>
          {NAV.map(item => (
            <button key={item.key} onClick={() => { setPage(item.key); setSelectedPid(null) }}
              style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                padding: '0.7rem 0.75rem', borderRadius: '0.625rem', marginBottom: 4,
                background: isActive(item.key) ? 'rgba(167,139,250,0.12)' : 'transparent',
                border: isActive(item.key) ? '1px solid rgba(167,139,250,0.2)' : '1px solid transparent',
                color: isActive(item.key) ? '#c4b5fd' : '#6b7280',
                fontFamily: 'inherit', fontSize: '0.875rem', fontWeight: 500,
                cursor: 'pointer', transition: 'all 0.15s', textAlign: 'left',
              }}
            >
              <span style={{ fontSize: '1rem', width: 20, textAlign: 'center' }}>{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
          <div style={{
            background: 'rgba(167,139,250,0.08)', borderRadius: '0.75rem',
            padding: '0.75rem', marginBottom: '0.75rem',
          }}>
            <p style={{ margin: 0, fontWeight: 700, color: '#f1f1f1', fontSize: '0.85rem' }}>{doctor.name}</p>
            <p style={{ margin: '2px 0 0', color: '#6b7280', fontSize: '0.75rem' }}>{doctor.specialty}</p>
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
        {page === 'detail' && selectedPid
          ? <PatientDetail patientId={selectedPid} onBack={goBack} />
          : page === 'alerts'
          ? <Alerts doctor={doctor} onSelectPatient={goToPatient} />
          : <Overview doctor={doctor} onSelectPatient={goToPatient} />
        }
      </main>
    </div>
  )
}
