import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { getPatient, getPatientAnalysis } from '../../api/client'
import AlertBadge from '../../components/AlertBadge'
import ReasoningBox from '../../components/ReasoningBox'
import RiskNode from '../../components/RiskNode'
import TissueBar from '../../components/TissueBar'
import type { AnalysisResult, Patient } from '../../types'

interface Props {
  patientId: string
  onBack: () => void
}

export default function PatientDetail({ patientId, onBack }: Props) {
  const [patient,  setPatient]  = useState<Patient | null>(null)
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [loading,  setLoading]  = useState(true)

  useEffect(() => {
    Promise.all([getPatient(patientId), getPatientAnalysis(patientId)])
      .then(([p, a]) => { setPatient(p); setAnalysis(a) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [patientId])

  if (loading) return <div style={{ color: '#4b5563', padding: '3rem', textAlign: 'center' }}>Loading patient…</div>
  if (!patient) return <div style={{ color: '#ef4444', padding: '2rem' }}>Patient not found.</div>

  const history = patient.wound_history ?? []
  const chartData = history.map(s => ({
    date: s.date.slice(5),
    area: parseFloat(s.area_cm2.toFixed(2)),
  }))

  const tooltipStyle = {
    background: 'rgba(15,15,20,0.95)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '0.5rem',
    color: '#f1f1f1',
    fontSize: '0.8rem',
  }

  return (
    <div>
      {/* Back + header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <button onClick={onBack} style={{
          background: 'none', border: 'none', color: '#6b7280', fontSize: '0.85rem',
          cursor: 'pointer', fontFamily: 'inherit', padding: 0, marginBottom: '1rem',
          display: 'flex', alignItems: 'center', gap: 4,
        }}>
          ← Back to Overview
        </button>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <p style={{ color: '#a78bfa', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.18em', textTransform: 'uppercase', margin: '0 0 4px' }}>Patient Record</p>
            <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f1f1f1', margin: '0 0 0.25rem', letterSpacing: '-0.02em' }}>{patient.name}</h1>
            <p style={{ color: '#6b7280', fontSize: '0.9rem', margin: 0 }}>Age {patient.age} · Post-Op Day {patient.post_op_day}</p>
          </div>
          {analysis && <AlertBadge priority={analysis.priority} size="lg" />}
        </div>
      </motion.div>

      {/* Three-column grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr 1fr', gap: '1.25rem', marginTop: '1.5rem' }}>

        {/* Left: profile */}
        <motion.div className="glass" style={{ padding: '1.5rem' }}
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
        >
          <p style={{ fontSize: '0.68rem', color: '#6b7280', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '1rem' }}>Clinical Profile</p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: '1.2rem' }}>
            {[
              { label: 'Glucose',  value: `${patient.blood_glucose} mg/dL`, alert: patient.blood_glucose > 180 },
              { label: 'Albumin',  value: `${patient.serum_albumin} g/dL`,  alert: patient.serum_albumin < 3 },
              { label: 'Mobility', value: `${patient.mobility_score}/10`,    alert: patient.mobility_score < 4 },
              { label: 'Scans',    value: `${history.length} total` },
            ].map(({ label, value, alert }) => (
              <div key={label} className="glass" style={{ padding: '0.6rem 0.75rem' }}>
                <p style={{ margin: 0, fontSize: '0.65rem', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</p>
                <p style={{ margin: '2px 0 0', fontSize: '0.82rem', fontWeight: 700, color: alert ? '#f59e0b' : '#f1f1f1' }}>{value}</p>
              </div>
            ))}
          </div>

          {patient.comorbidities.length > 0 && (
            <>
              <p style={{ fontSize: '0.68rem', color: '#6b7280', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Conditions</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: '1.2rem' }}>
                {patient.comorbidities.map(c => (
                  <span key={c} style={{
                    background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 999, padding: '3px 10px', fontSize: '0.75rem', color: '#9ca3af',
                  }}>{c}</span>
                ))}
              </div>
            </>
          )}

          {analysis?.active_risk_factors && analysis.active_risk_factors.length > 0 && (
            <>
              <p style={{ fontSize: '0.68rem', color: '#6b7280', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '0.6rem' }}>Knowledge Graph — Active Risk Nodes</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {analysis.active_risk_factors.map((rf, i) => <RiskNode key={rf} label={rf} index={i} />)}
              </div>
            </>
          )}
        </motion.div>

        {/* Center: trend + tissue */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
          style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}
        >
          <div className="glass" style={{ padding: '1.25rem' }}>
            <p style={{ fontSize: '0.68rem', color: '#6b7280', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '1rem' }}>Wound Area Trend (cm²)</p>
            {chartData.length >= 2 ? (
              <ResponsiveContainer width="100%" height={160}>
                <AreaChart data={chartData} margin={{ top: 5, right: 5, bottom: 0, left: -20 }}>
                  <defs>
                    <linearGradient id="areaGrad2" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#a78bfa" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#a78bfa" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="date" tick={{ fill: '#4b5563', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#4b5563', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Area type="monotone" dataKey="area" stroke="#a78bfa" strokeWidth={2}
                    fill="url(#areaGrad2)" dot={{ fill: '#a78bfa', r: 3 }} name="Area (cm²)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <p style={{ color: '#4b5563', fontSize: '0.82rem', textAlign: 'center', padding: '1rem 0' }}>Need ≥2 scans for trend</p>
            )}
          </div>

          {analysis && (
            <div className="glass" style={{ padding: '1.25rem' }}>
              <p style={{ fontSize: '0.68rem', color: '#6b7280', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '1rem' }}>Latest Tissue Composition</p>
              <TissueBar label="Granulation (Red)" value={analysis.ryb_ratios.red}    color="#ef4444" bgColor="#7f1d1d" />
              <TissueBar label="Slough (Yellow)"   value={analysis.ryb_ratios.yellow} color="#f59e0b" bgColor="#78350f" />
              <TissueBar label="Eschar (Black)"    value={analysis.ryb_ratios.black}  color="#6b7280" bgColor="#111827" />
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                <div>
                  <p style={{ margin: 0, fontSize: '0.68rem', color: '#4b5563' }}>Area</p>
                  <p style={{ margin: 0, fontWeight: 700, fontSize: '1rem', color: '#f1f1f1' }}>{analysis.area_cm2.toFixed(2)} cm²</p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <p style={{ margin: 0, fontSize: '0.68rem', color: '#4b5563' }}>Δ</p>
                  <p style={{ margin: 0, fontWeight: 700, fontSize: '1rem', color: analysis.area_delta <= 0 ? '#22c55e' : '#f59e0b' }}>
                    {analysis.area_delta >= 0 ? '+' : ''}{analysis.area_delta.toFixed(2)} cm²
                  </p>
                </div>
              </div>
            </div>
          )}
        </motion.div>

        {/* Right: alerts + reasoning */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}
        >
          {analysis && (
            <>
              <div className="glass" style={{ padding: '1.5rem' }}>
                <p style={{ fontSize: '0.68rem', color: '#6b7280', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '0.75rem' }}>Clinical Alerts</p>
                {analysis.alerts.map((a, i) => (
                  <div key={i} style={{
                    padding: '0.5rem 0.75rem', borderRadius: '0.5rem', marginBottom: 6,
                    background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)',
                    fontSize: '0.8rem', color: '#9ca3af',
                  }}>
                    ! {a}
                  </div>
                ))}
              </div>

              <div className="glass" style={{ padding: '1.5rem' }}>
                <p style={{ fontSize: '0.68rem', color: '#6b7280', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Action Required</p>
                <p style={{ fontSize: '0.85rem', color: '#f1f1f1', fontWeight: 600, margin: 0 }}>{analysis.recommended_action}</p>
              </div>

              <div className="glass" style={{ padding: '1.5rem', flex: 1 }}>
                <p style={{ fontSize: '0.68rem', color: '#6b7280', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '0.75rem' }}>AI Reasoning</p>
                <ReasoningBox text={analysis.reasoning} />
              </div>
            </>
          )}
        </motion.div>
      </div>
    </div>
  )
}
