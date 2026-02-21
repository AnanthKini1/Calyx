import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { getDoctorPatients } from '../../api/client'
import AlertBadge from '../../components/AlertBadge'
import type { Doctor, PatientWithSummary, Priority } from '../../types'

const PRIORITY_ORDER: Priority[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'OK']

interface Props {
  doctor: Doctor
  onSelectPatient: (id: string) => void
}

export default function Overview({ doctor, onSelectPatient }: Props) {
  const [patients, setPatients] = useState<PatientWithSummary[]>([])
  const [loading, setLoading]   = useState(true)

  useEffect(() => {
    getDoctorPatients(doctor.doctor_id)
      .then(data => setPatients(
        [...data].sort((a, b) => {
          const pa = a.latest_summary?.priority ?? 'OK'
          const pb = b.latest_summary?.priority ?? 'OK'
          return PRIORITY_ORDER.indexOf(pa) - PRIORITY_ORDER.indexOf(pb)
        })
      ))
      .finally(() => setLoading(false))
  }, [doctor.doctor_id])

  const counts = PRIORITY_ORDER.reduce((acc, p) => {
    acc[p] = patients.filter(pt => pt.latest_summary?.priority === p).length
    return acc
  }, {} as Record<Priority, number>)

  return (
    <div>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <p style={{ color: '#a78bfa', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.18em', textTransform: 'uppercase', margin: '0 0 4px' }}>Dashboard</p>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f1f1f1', margin: '0 0 0.25rem', letterSpacing: '-0.02em' }}>Patient Overview</h1>
        <p style={{ color: '#6b7280', fontSize: '0.9rem', margin: 0 }}>
          {patients.length} patients · sorted by clinical priority
        </p>
      </motion.div>

      {/* Priority summary */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
        style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem', flexWrap: 'wrap' }}
      >
        {(['CRITICAL','HIGH','MEDIUM','OK'] as Priority[]).map(p => (
          counts[p] > 0 && (
            <div key={p} className="glass" style={{ padding: '0.6rem 1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
              <AlertBadge priority={p} size="sm" />
              <span style={{ fontWeight: 700, color: '#f1f1f1', fontSize: '1rem' }}>{counts[p]}</span>
            </div>
          )
        ))}
      </motion.div>

      {loading ? (
        <div style={{ textAlign: 'center', color: '#4b5563', marginTop: '3rem' }}>Loading patients…</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem', marginTop: '1.5rem' }}>
          {patients.map((p, i) => (
            <PatientCard key={p.patient_id} patient={p} index={i} onClick={() => onSelectPatient(p.patient_id)} />
          ))}
        </div>
      )}
    </div>
  )
}

function PatientCard({ patient: p, index, onClick }: { patient: PatientWithSummary; index: number; onClick: () => void }) {
  const s = p.latest_summary
  const delta = s?.area_delta ?? null

  return (
    <motion.div
      custom={index}
      variants={{
        hidden: { opacity: 0, y: 20 },
        visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.07 } }),
      }}
      initial="hidden" animate="visible"
      className="glass glass-lift"
      onClick={onClick}
      style={{ padding: '1.5rem', cursor: 'pointer', position: 'relative' }}
    >
      {/* Priority badge */}
      {s?.priority && (
        <div style={{ position: 'absolute', top: '1rem', right: '1rem' }}>
          <AlertBadge priority={s.priority} size="sm" />
        </div>
      )}

      <p style={{ fontWeight: 700, color: '#f1f1f1', fontSize: '1rem', margin: '0 0 2px', paddingRight: '6rem' }}>{p.name}</p>
      <p style={{ color: '#6b7280', fontSize: '0.78rem', margin: '0 0 1rem' }}>
        Age {p.age} · POD {p.post_op_day}
        {p.comorbidities.length > 0 && ` · ${p.comorbidities.length} condition${p.comorbidities.length > 1 ? 's' : ''}`}
      </p>

      {s ? (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: '0.75rem' }}>
            <Stat label="Area" value={`${s.area_cm2.toFixed(1)} cm²`} />
            <Stat
              label="Δ Area"
              value={`${delta !== null && delta >= 0 ? '+' : ''}${(delta ?? 0).toFixed(2)} cm²`}
              color={delta !== null && delta <= 0 ? '#22c55e' : '#f59e0b'}
            />
          </div>

          {/* Mini tissue bars */}
          <div style={{ display: 'flex', gap: 4 }}>
            {[
              { label: 'R', val: s.ryb_ratios.red,    color: '#ef4444' },
              { label: 'Y', val: s.ryb_ratios.yellow, color: '#f59e0b' },
              { label: 'B', val: s.ryb_ratios.black,  color: '#6b7280' },
            ].map(({ label, val, color }) => (
              <div key={label} style={{ flex: 1 }}>
                <div style={{ height: 4, borderRadius: 999, background: 'rgba(255,255,255,0.05)', overflow: 'hidden' }}>
                  <div style={{ width: `${val}%`, height: '100%', background: color, borderRadius: 999 }} />
                </div>
                <p style={{ margin: '3px 0 0', fontSize: '0.65rem', color: '#4b5563', textAlign: 'center' }}>{label} {val.toFixed(0)}%</p>
              </div>
            ))}
          </div>

          {s.scan_date && (
            <p style={{ margin: '0.75rem 0 0', fontSize: '0.72rem', color: '#374151' }}>Last scan: {s.scan_date}</p>
          )}
        </>
      ) : (
        <p style={{ color: '#4b5563', fontSize: '0.82rem' }}>No scans yet</p>
      )}
    </motion.div>
  )
}

function Stat({ label, value, color = '#f1f1f1' }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <p style={{ margin: 0, fontSize: '0.65rem', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</p>
      <p style={{ margin: '2px 0 0', fontWeight: 700, color, fontSize: '0.9rem' }}>{value}</p>
    </div>
  )
}
