import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { getDoctorPatients } from '../../api/client'
import AlertBadge from '../../components/AlertBadge'
import type { Doctor, PatientWithSummary, Priority } from '../../types'

const URGENT: Priority[] = ['CRITICAL', 'HIGH']

interface Props {
  doctor: Doctor
  onSelectPatient: (id: string) => void
}

export default function Alerts({ doctor, onSelectPatient }: Props) {
  const [patients, setPatients] = useState<PatientWithSummary[]>([])
  const [loading, setLoading]   = useState(true)

  useEffect(() => {
    getDoctorPatients(doctor.doctor_id)
      .then(data => setPatients(data.filter(p => URGENT.includes(p.latest_summary?.priority as Priority))))
      .finally(() => setLoading(false))
  }, [doctor.doctor_id])

  return (
    <div>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <p style={{ color: '#ef4444', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.18em', textTransform: 'uppercase', margin: '0 0 4px' }}>Requires Attention</p>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f1f1f1', margin: '0 0 0.25rem', letterSpacing: '-0.02em' }}>Active Alerts</h1>
        <p style={{ color: '#6b7280', fontSize: '0.9rem', margin: 0 }}>
          {loading ? 'Loading…' : `${patients.length} patient${patients.length !== 1 ? 's' : ''} requiring urgent attention`}
        </p>
      </motion.div>

      {!loading && patients.length === 0 && (
        <motion.div className="glass" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
          style={{ marginTop: '1.5rem', padding: '3rem', textAlign: 'center' }}
        >
          <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>✅</div>
          <p style={{ color: '#22c55e', fontWeight: 600, fontSize: '1rem', margin: 0 }}>All patients are on track</p>
          <p style={{ color: '#4b5563', fontSize: '0.85rem', margin: '0.5rem 0 0' }}>No critical or high-priority alerts at this time.</p>
        </motion.div>
      )}

      <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {patients.map((p, i) => {
          const s = p.latest_summary!
          return (
            <motion.div
              key={p.patient_id}
              initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.08 }}
              className="glass glass-lift"
              onClick={() => onSelectPatient(p.patient_id)}
              style={{ padding: '1.5rem', cursor: 'pointer' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <div>
                  <p style={{ fontWeight: 700, color: '#f1f1f1', fontSize: '1rem', margin: '0 0 2px' }}>{p.name}</p>
                  <p style={{ color: '#6b7280', fontSize: '0.78rem', margin: 0 }}>Age {p.age} · POD {p.post_op_day} · {p.comorbidities.join(', ') || 'No conditions'}</p>
                </div>
                <AlertBadge priority={s.priority} size="md" />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: '1rem' }}>
                {s.alerts.map((a, j) => (
                  <div key={j} style={{
                    display: 'flex', alignItems: 'flex-start', gap: 10,
                    padding: '0.6rem 0.75rem', borderRadius: '0.5rem',
                    background: 'rgba(239,68,68,0.04)', border: '1px solid rgba(239,68,68,0.1)',
                    fontSize: '0.82rem', color: '#fca5a5',
                  }}>
                    <span>!</span>
                    {a}
                  </div>
                ))}
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <p style={{ margin: 0, fontSize: '0.75rem', color: '#4b5563' }}>Last scan: {s.scan_date}</p>
                <span style={{ fontSize: '0.78rem', color: '#a78bfa', fontWeight: 600 }}>View details →</span>
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
