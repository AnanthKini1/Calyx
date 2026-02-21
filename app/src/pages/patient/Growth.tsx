import { motion } from 'framer-motion'
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Legend,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import type { Patient } from '../../types'

interface Props { patient: Patient }

export default function Growth({ patient }: Props) {
  const history = patient.wound_history ?? []

  const data = history.map((s, i) => ({
    date:   s.date.slice(5),          // MM-DD
    area:   parseFloat(s.area_cm2.toFixed(2)),
    red:    s.ryb_ratios.red,
    yellow: s.ryb_ratios.yellow,
    black:  s.ryb_ratios.black,
    index:  i,
  }))

  const latestArea = history.at(-1)?.area_cm2 ?? 0
  const firstArea  = history[0]?.area_cm2 ?? 0
  const pctChange  = firstArea > 0 ? ((latestArea - firstArea) / firstArea) * 100 : 0

  const tooltipStyle = {
    background: 'rgba(15,15,20,0.95)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '0.5rem',
    color: '#f1f1f1',
    fontSize: '0.8rem',
  }

  return (
    <div>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <p style={{ color: '#a78bfa', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.18em', textTransform: 'uppercase', margin: '0 0 4px' }}>Progress</p>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f1f1f1', margin: '0 0 0.25rem', letterSpacing: '-0.02em' }}>Healing Trend</h1>
        <p style={{ color: '#6b7280', fontSize: '0.9rem', margin: 0 }}>{history.length} data points over {history.length > 1 ? 'the scan period' : 'one scan'}</p>
      </motion.div>

      {/* Stats row */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
        style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginTop: '1.5rem' }}
      >
        {[
          { label: 'Current Area',  value: `${latestArea.toFixed(2)} cm²`, color: '#f1f1f1' },
          { label: 'Area Change',   value: `${pctChange >= 0 ? '+' : ''}${pctChange.toFixed(1)}%`, color: pctChange <= 0 ? '#22c55e' : '#f59e0b' },
          { label: 'Total Scans',   value: history.length, color: '#a78bfa' },
        ].map(({ label, value, color }) => (
          <div key={label} className="glass" style={{ padding: '1.25rem' }}>
            <p style={{ margin: 0, fontSize: '0.7rem', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.1em' }}>{label}</p>
            <p style={{ margin: '4px 0 0', fontSize: '1.5rem', fontWeight: 800, color }}>{value}</p>
          </div>
        ))}
      </motion.div>

      {history.length < 2 ? (
        <motion.div className="glass" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
          style={{ marginTop: '1.5rem', padding: '3rem', textAlign: 'center', color: '#4b5563' }}
        >
          At least 2 scans are needed to show trends.
        </motion.div>
      ) : (
        <>
          {/* Area chart */}
          <motion.div className="glass" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
            style={{ marginTop: '1.5rem', padding: '1.5rem' }}
          >
            <p style={{ fontSize: '0.75rem', color: '#6b7280', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '1.25rem' }}>Wound Area Over Time (cm²)</p>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                <defs>
                  <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#a78bfa" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#a78bfa" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" tick={{ fill: '#4b5563', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#4b5563', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Area type="monotone" dataKey="area" stroke="#a78bfa" strokeWidth={2}
                  fill="url(#areaGrad)" dot={{ fill: '#a78bfa', strokeWidth: 0, r: 4 }}
                  activeDot={{ r: 6, fill: '#c4b5fd' }} name="Area (cm²)" />
              </AreaChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Stacked tissue chart */}
          <motion.div className="glass" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
            style={{ marginTop: '1.25rem', padding: '1.5rem' }}
          >
            <p style={{ fontSize: '0.75rem', color: '#6b7280', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '1.25rem' }}>Tissue Composition Trend (%)</p>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" tick={{ fill: '#4b5563', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#4b5563', fontSize: 11 }} axisLine={false} tickLine={false} domain={[0, 100]} />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: '0.75rem', color: '#6b7280' }} />
                <Bar dataKey="red"    name="Granulation" stackId="a" fill="#ef4444" radius={[0,0,0,0]} />
                <Bar dataKey="yellow" name="Slough"      stackId="a" fill="#f59e0b" />
                <Bar dataKey="black"  name="Eschar"      stackId="a" fill="#374151" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </motion.div>
        </>
      )}
    </div>
  )
}
