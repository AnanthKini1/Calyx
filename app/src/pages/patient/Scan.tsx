import { AnimatePresence, motion } from 'framer-motion'
import { useRef, useState } from 'react'
import { runScan, saveScan } from '../../api/client'
import AlertBadge from '../../components/AlertBadge'
import ReasoningBox from '../../components/ReasoningBox'
import RiskNode from '../../components/RiskNode'
import TissueBar from '../../components/TissueBar'
import WoundImagePanel from '../../components/WoundImagePanel'
import type { AnalysisResult, Patient } from '../../types'

// Helper: staggered card motion props
const card = (i: number) => ({
  initial: { opacity: 0, y: 20 } as const,
  animate: { opacity: 1, y: 0 } as const,
  transition: { delay: i * 0.1, duration: 0.45 },
})

interface Props { patient: Patient; onScanSaved?: () => void }

export default function Scan({ patient, onScanSaved }: Props) {
  const [file, setFile]         = useState<File | null>(null)
  const [preview, setPreview]   = useState<string | null>(null)
  const [result, setResult]     = useState<AnalysisResult | null>(null)
  const [loading, setLoading]   = useState(false)
  const [saved, setSaved]       = useState(false)
  const [error, setError]       = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = (f: File) => {
    setFile(f)
    setSaved(false)
    setResult(null)
    const reader = new FileReader()
    reader.onload = e => setPreview(e.target?.result as string)
    reader.readAsDataURL(f)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const f = e.dataTransfer.files[0]
    if (f && f.type.startsWith('image/')) handleFile(f)
  }

  const runAnalysis = async (useDemo: boolean) => {
    setLoading(true); setError(''); setResult(null); setSaved(false)
    try {
      const res = await runScan(patient.patient_id, useDemo ? null : file)
      setResult(res)
      if (res.annotated_image_b64) {
        setPreview(`data:image/jpeg;base64,${res.annotated_image_b64}`)
      }
    } catch {
      setError('Analysis failed. Make sure the API server is running.')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!result) return
    try {
      await saveScan(patient.patient_id, {
        area_cm2: result.area_cm2,
        ryb_ratios: result.ryb_ratios,
      })
      setSaved(true)
      onScanSaved?.()
    } catch {
      setError('Failed to save scan.')
    }
  }

  const ryb = result?.ryb_ratios

  return (
    <div>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <p style={{ color: '#a78bfa', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.18em', textTransform: 'uppercase', margin: '0 0 4px' }}>Wound Analysis</p>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f1f1f1', margin: '0 0 0.25rem', letterSpacing: '-0.02em' }}>
          New Scan
        </h1>
        <p style={{ color: '#6b7280', fontSize: '0.9rem', margin: 0 }}>Upload a wound photo or run the demo analysis.</p>
      </motion.div>

      {/* Upload zone */}
      {!result && (
        <motion.div {...card(0)}
          className="glass" style={{ marginTop: '1.5rem', padding: '2rem', textAlign: 'center' }}
          onDrop={handleDrop} onDragOver={e => e.preventDefault()}
        >
          {preview ? (
            <img src={preview} alt="Preview" style={{ maxHeight: 240, borderRadius: '0.75rem', maxWidth: '100%' }} />
          ) : (
            <div style={{ padding: '2rem' }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📸</div>
              <p style={{ color: '#6b7280', margin: '0 0 1rem', fontSize: '0.9rem' }}>
                Drag & drop a wound photo here, or
              </p>
              <button className="btn-secondary" style={{ width: 'auto', padding: '0.6rem 1.5rem' }}
                onClick={() => inputRef.current?.click()}
              >
                Browse Files
              </button>
            </div>
          )}
          <input ref={inputRef} type="file" accept="image/*" style={{ display: 'none' }}
            onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f) }}
          />
        </motion.div>
      )}

      {/* Controls */}
      {!result && (
        <motion.div {...card(1)}
          style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}
        >
          <button className="btn-primary" style={{ flex: 1 }}
            onClick={() => runAnalysis(false)} disabled={loading || !file}
          >
            {loading ? 'Analysing…' : '▶  Run Analysis'}
          </button>
          <button className="btn-secondary" style={{ flex: 1 }}
            onClick={() => runAnalysis(true)} disabled={loading}
          >
            ✦  Demo Analysis
          </button>
        </motion.div>
      )}

      {error && (
        <p style={{ color: '#ef4444', background: 'rgba(239,68,68,0.08)', borderRadius: '0.5rem', padding: '0.75rem', marginTop: '1rem', fontSize: '0.85rem' }}>{error}</p>
      )}

      {/* Results */}
      <AnimatePresence>
        {result && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            {/* Three-column layout */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr 1fr', gap: '1.25rem', marginTop: '1.5rem' }}>

              {/* Left: Patient profile + risk nodes */}
              <motion.div {...card(0)}
                className="glass" style={{ padding: '1.5rem' }}
              >
                <p style={{ fontSize: '0.68rem', color: '#6b7280', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '1rem' }}>Patient Profile</p>
                <p style={{ fontWeight: 700, color: '#f1f1f1', fontSize: '1rem', margin: '0 0 4px' }}>{patient.name}</p>
                <p style={{ color: '#6b7280', fontSize: '0.8rem', margin: '0 0 1rem' }}>Post-Op Day {patient.post_op_day} · Age {patient.age}</p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: '1.2rem' }}>
                  {[
                    { label: 'Glucose', value: `${patient.blood_glucose} mg/dL`, alert: patient.blood_glucose > 180 },
                    { label: 'Albumin', value: `${patient.serum_albumin} g/dL`, alert: patient.serum_albumin < 3 },
                    { label: 'Mobility', value: `${patient.mobility_score}/10`, alert: patient.mobility_score < 4 },
                    { label: 'Conditions', value: patient.comorbidities.length || 'None' },
                  ].map(({ label, value, alert }) => (
                    <div key={label} className="glass" style={{ padding: '0.6rem 0.75rem' }}>
                      <p style={{ margin: 0, fontSize: '0.68rem', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</p>
                      <p style={{ margin: '2px 0 0', fontSize: '0.82rem', fontWeight: 700, color: alert ? '#f59e0b' : '#f1f1f1' }}>{value}</p>
                    </div>
                  ))}
                </div>

                {result.active_risk_factors.length > 0 && (
                  <>
                    <p style={{ fontSize: '0.68rem', color: '#6b7280', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '0.6rem' }}>Risk Factors</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {result.active_risk_factors.map((rf, i) => <RiskNode key={rf} label={rf} index={i} />)}
                    </div>
                  </>
                )}
              </motion.div>

              {/* Center: Annotated image + tissue bars */}
              <motion.div {...card(1)}>
                {preview && <WoundImagePanel src={preview} />}

                <div className="glass" style={{ padding: '1.25rem', marginTop: '1rem' }}>
                  <p style={{ fontSize: '0.68rem', color: '#6b7280', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '1rem' }}>Tissue Composition</p>
                  {ryb && (
                    <>
                      <TissueBar label="Granulation (Red)" value={ryb.red}    color="#ef4444" bgColor="#7f1d1d" />
                      <TissueBar label="Slough (Yellow)"   value={ryb.yellow} color="#f59e0b" bgColor="#78350f" />
                      <TissueBar label="Eschar (Black)"    value={ryb.black}  color="#6b7280" bgColor="#111827" />
                    </>
                  )}
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                    <div>
                      <p style={{ margin: 0, fontSize: '0.7rem', color: '#4b5563' }}>Wound Area</p>
                      <p style={{ margin: 0, fontWeight: 700, fontSize: '1.1rem', color: '#f1f1f1' }}>{result.area_cm2.toFixed(2)} cm²</p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <p style={{ margin: 0, fontSize: '0.7rem', color: '#4b5563' }}>Area Δ</p>
                      <p style={{ margin: 0, fontWeight: 700, fontSize: '1.1rem', color: result.area_delta <= 0 ? '#22c55e' : '#f59e0b' }}>
                        {result.area_delta >= 0 ? '+' : ''}{result.area_delta.toFixed(2)} cm²
                      </p>
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* Right: Alert + action + reasoning */}
              <motion.div {...card(2)}
                style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}
              >
                <div className="glass" style={{ padding: '1.5rem' }}>
                  <p style={{ fontSize: '0.68rem', color: '#6b7280', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '0.75rem' }}>Assessment</p>
                  <AlertBadge priority={result.priority} size="md" />

                  <div style={{ marginTop: '1rem' }}>
                    {result.alerts.map((a, i) => (
                      <div key={i} style={{
                        display: 'flex', alignItems: 'flex-start', gap: 8,
                        marginBottom: 8, padding: '0.5rem', borderRadius: '0.5rem',
                        background: 'rgba(255,255,255,0.03)', fontSize: '0.8rem', color: '#9ca3af',
                      }}>
                        <span style={{ color: '#6b7280', flexShrink: 0 }}>!</span>
                        {a}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="glass" style={{ padding: '1.5rem' }}>
                  <p style={{ fontSize: '0.68rem', color: '#6b7280', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Recommended Action</p>
                  <p style={{ fontSize: '0.85rem', color: '#f1f1f1', fontWeight: 600, margin: 0 }}>
                    {result.recommended_action}
                  </p>
                </div>

                <div className="glass" style={{ padding: '1.5rem', flex: 1 }}>
                  <p style={{ fontSize: '0.68rem', color: '#6b7280', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '0.75rem' }}>AI Reasoning</p>
                  <ReasoningBox text={result.reasoning} />
                </div>
              </motion.div>
            </div>

            {/* Save + Rescan */}
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1.25rem' }}>
              <button className="btn-primary" style={{ flex: 1 }}
                onClick={handleSave} disabled={saved}
              >
                {saved ? '✓ Saved to History' : 'Save Scan →'}
              </button>
              <button className="btn-secondary" style={{ flex: 1 }}
                onClick={() => { setResult(null); setPreview(null); setFile(null); setSaved(false) }}
              >
                New Scan
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
