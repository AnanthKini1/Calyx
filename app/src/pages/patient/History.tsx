import { motion } from 'framer-motion'
import AlertBadge from '../../components/AlertBadge'
import type { Patient, Priority } from '../../types'

// Derive a rough priority from the latest scan data (no live KG call here)
function guessPriority(scan: { ryb_ratios: { red: number; yellow: number; black: number } }): Priority {
  const { black, yellow } = scan.ryb_ratios
  if (black > 15) return 'CRITICAL'
  if (yellow > 10) return 'HIGH'
  if (yellow > 5)  return 'MEDIUM'
  return 'OK'
}

interface Props { patient: Patient }

export default function History({ patient }: Props) {
  const history = [...(patient.wound_history ?? [])].reverse()

  return (
    <div>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <p style={{ color: '#a78bfa', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.18em', textTransform: 'uppercase', margin: '0 0 4px' }}>Records</p>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f1f1f1', margin: '0 0 0.25rem', letterSpacing: '-0.02em' }}>Scan History</h1>
        <p style={{ color: '#6b7280', fontSize: '0.9rem', margin: 0 }}>{history.length} scan{history.length !== 1 ? 's' : ''} recorded</p>
      </motion.div>

      {history.length === 0 ? (
        <motion.div custom={0} className="glass" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          style={{ marginTop: '1.5rem', padding: '3rem', textAlign: 'center', color: '#4b5563' }}
        >
          No scans recorded yet. Run your first analysis from the Scan tab.
        </motion.div>
      ) : (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
          className="glass" style={{ marginTop: '1.5rem', overflow: 'hidden' }}
        >
          {/* Header */}
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr 2fr 1fr 1fr',
            padding: '0.75rem 1.5rem',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
            fontSize: '0.68rem', color: '#4b5563', fontWeight: 700,
            letterSpacing: '0.1em', textTransform: 'uppercase',
          }}>
            <span>Date</span>
            <span>Area (cm²)</span>
            <span>Tissue Composition</span>
            <span>Status</span>
            <span style={{ textAlign: 'right' }}>Δ Area</span>
          </div>

          {history.map((scan, idx) => {
            const prev = history[idx + 1]
            const delta = prev ? scan.area_cm2 - prev.area_cm2 : null
            const priority = guessPriority(scan)
            const { red, yellow, black } = scan.ryb_ratios

            return (
              <motion.div
                key={scan.date + idx}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                style={{
                  display: 'grid', gridTemplateColumns: '1fr 1fr 2fr 1fr 1fr',
                  padding: '1rem 1.5rem', alignItems: 'center',
                  borderBottom: idx < history.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                  transition: 'background 0.15s',
                }}
                whileHover={{ background: 'rgba(255,255,255,0.02)' } as never}
              >
                <span style={{ fontSize: '0.85rem', color: '#f1f1f1', fontWeight: 500 }}>{scan.date}</span>
                <span style={{ fontSize: '0.9rem', color: '#f1f1f1', fontWeight: 700 }}>{scan.area_cm2.toFixed(2)}</span>

                {/* Mini tissue bars */}
                <div style={{ paddingRight: '1rem' }}>
                  {[
                    { label: 'R', val: red,    color: '#ef4444' },
                    { label: 'Y', val: yellow, color: '#f59e0b' },
                    { label: 'B', val: black,  color: '#6b7280' },
                  ].map(({ label, val, color }) => (
                    <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                      <span style={{ fontSize: '0.65rem', color: '#4b5563', width: 10 }}>{label}</span>
                      <div style={{ flex: 1, height: 5, borderRadius: 999, background: 'rgba(255,255,255,0.05)', overflow: 'hidden' }}>
                        <div style={{ width: `${val}%`, height: '100%', background: color, borderRadius: 999 }} />
                      </div>
                      <span style={{ fontSize: '0.7rem', color, width: 32, textAlign: 'right' }}>{val.toFixed(0)}%</span>
                    </div>
                  ))}
                </div>

                <AlertBadge priority={priority} size="sm" />

                <span style={{
                  textAlign: 'right', fontWeight: 700, fontSize: '0.9rem',
                  color: delta === null ? '#4b5563' : delta <= 0 ? '#22c55e' : '#f59e0b',
                }}>
                  {delta === null ? '—' : `${delta >= 0 ? '+' : ''}${delta.toFixed(2)}`}
                </span>
              </motion.div>
            )
          })}
        </motion.div>
      )}
    </div>
  )
}
