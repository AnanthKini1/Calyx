import { AnimatePresence, motion } from 'framer-motion'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getDoctors, registerDoctor, registerPatient } from '../api/client'
import { setSession } from '../api/session'
import type { Doctor, User } from '../types'

const COMORBIDITIES = [
  'Type 2 Diabetes', 'Obesity', 'Hypertension',
  'Peripheral Artery Disease', 'Malnutrition',
]

const SPECIALTIES = [
  'Wound Care & Surgery', 'General Surgery', 'Plastic Surgery',
  'Vascular Surgery', 'Internal Medicine', 'Endocrinology', 'Orthopedics', 'Other',
]

type Role = 'patient' | 'doctor' | null

export default function CreateProfile() {
  const [role, setRole]           = useState<Role>(null)
  const [error, setError]         = useState('')
  const [loading, setLoading]     = useState(false)
  const navigate = useNavigate()

  const finish = (user: User) => {
    setSession(user)
    window.location.href = '/'
  }

  return (
    <div style={{
      minHeight: '100vh', background: '#0a0a0f',
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', padding: '2rem',
    }}>
      <motion.button
        whileHover={{ x: -3 }}
        onClick={() => role ? setRole(null) : navigate('/')}
        style={{
          position: 'absolute', top: '1.5rem', left: '1.5rem',
          background: 'none', border: 'none', color: '#6b7280',
          fontSize: '0.85rem', cursor: 'pointer', fontFamily: 'inherit',
          display: 'flex', alignItems: 'center', gap: 4,
        }}
      >
        ← {role ? 'Change Role' : 'Back to Sign In'}
      </motion.button>

      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        style={{ textAlign: 'center', marginBottom: '2rem' }}
      >
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f1f1f1', marginBottom: '0.4rem' }}>
          Create Your Profile
        </h1>
        <p style={{ color: '#6b7280', fontSize: '0.9rem' }}>
          {role ? `Setting up your ${role} account` : 'Choose your role to get started'}
        </p>
      </motion.div>

      <motion.div
        className="glass"
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
        style={{ width: '100%', maxWidth: 480, padding: '2rem' }}
      >
        <AnimatePresence mode="wait">
          {!role && (
            <motion.div key="role"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            >
              <p style={{ color: '#6b7280', textAlign: 'center', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
                I am a…
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                {[
                  { r: 'patient' as Role, icon: '🩺', label: 'Patient', desc: 'Track wound healing & view scans' },
                  { r: 'doctor' as Role, icon: '👨‍⚕️', label: 'Doctor', desc: 'Monitor patients & review alerts' },
                ].map(({ r, icon, label, desc }) => (
                  <motion.button key={r} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                    onClick={() => setRole(r)}
                    style={{
                      background: 'rgba(167,139,250,0.06)', border: '1px solid rgba(167,139,250,0.2)',
                      borderRadius: '1rem', padding: '1.5rem 1rem', cursor: 'pointer',
                      textAlign: 'center', color: '#f1f1f1', fontFamily: 'inherit',
                    }}
                  >
                    <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{icon}</div>
                    <div style={{ fontWeight: 700, marginBottom: '0.25rem' }}>{label}</div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>{desc}</div>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}

          {role === 'patient' && (
            <PatientForm
              key="patient" error={error} setError={setError}
              loading={loading} setLoading={setLoading} onSuccess={finish}
            />
          )}

          {role === 'doctor' && (
            <DoctorForm
              key="doctor" error={error} setError={setError}
              loading={loading} setLoading={setLoading} onSuccess={finish}
            />
          )}
        </AnimatePresence>

        <AnimatePresence>
          {error && (
            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              style={{
                color: '#ef4444', fontSize: '0.82rem', marginTop: '1rem',
                background: 'rgba(239,68,68,0.08)', borderRadius: '0.5rem',
                padding: '0.6rem 0.8rem', border: '1px solid rgba(239,68,68,0.2)',
              }}
            >
              {error}
            </motion.p>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  )
}

// ── Patient form ──────────────────────────────────────────────────────────────
function PatientForm({ error: _e, setError, loading, setLoading, onSuccess }: FormProps) {
  const [name, setName]         = useState('')
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [age, setAge]           = useState(45)
  const [glucose, setGlucose]   = useState(110)
  const [albumin, setAlbumin]   = useState(3.8)
  const [mobility, setMobility] = useState(7)
  const [podDay, setPodDay]     = useState(7)
  const [selected, setSelected] = useState<string[]>([])
  const [doctors, setDoctors]   = useState<Doctor[]>([])
  const [doctorId, setDoctorId] = useState<string>('')

  useState(() => {
    getDoctors().then(setDoctors).catch(() => {})
  })

  const toggleComorb = (c: string) =>
    setSelected(prev => prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name || !email || !password) { setError('Name, email, and password are required.'); return }
    setLoading(true); setError('')
    try {
      const user = await registerPatient({
        name, email, password, age, comorbidities: selected,
        blood_glucose: glucose, serum_albumin: albumin,
        mobility_score: mobility, post_op_day: podDay,
        doctor_id: doctorId || undefined,
      })
      onSuccess(user)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? 'Registration failed.')
    } finally { setLoading(false) }
  }

  return (
    <motion.form onSubmit={submit} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <SectionLabel>Personal</SectionLabel>
      <Row>
        <FormField label="Full Name">
          <input className="input" value={name} onChange={e => setName(e.target.value)} placeholder="Your name" />
        </FormField>
        <FormField label="Age" small>
          <input className="input" type="number" min={1} max={120} value={age}
            onChange={e => setAge(Number(e.target.value))} />
        </FormField>
      </Row>

      <SectionLabel>Account</SectionLabel>
      <FormField label="Email">
        <input className="input" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" />
      </FormField>
      <FormField label="Password">
        <input className="input" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" />
      </FormField>

      <SectionLabel>Clinical (optional)</SectionLabel>
      <Row>
        <FormField label="Blood Glucose (mg/dL)">
          <input className="input" type="number" value={glucose} onChange={e => setGlucose(Number(e.target.value))} />
        </FormField>
        <FormField label="Serum Albumin (g/dL)">
          <input className="input" type="number" step="0.1" value={albumin} onChange={e => setAlbumin(Number(e.target.value))} />
        </FormField>
      </Row>
      <Row>
        <FormField label={`Mobility: ${mobility}/10`}>
          <input type="range" min={0} max={10} value={mobility} onChange={e => setMobility(Number(e.target.value))}
            style={{ width: '100%', accentColor: '#a78bfa' }} />
        </FormField>
        <FormField label="Days Since Surgery">
          <input className="input" type="number" value={podDay} onChange={e => setPodDay(Number(e.target.value))} />
        </FormField>
      </Row>

      <SectionLabel>Conditions (optional)</SectionLabel>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: '1.2rem' }}>
        {COMORBIDITIES.map(c => (
          <button key={c} type="button" onClick={() => toggleComorb(c)}
            style={{
              background: selected.includes(c) ? 'rgba(167,139,250,0.2)' : 'rgba(255,255,255,0.05)',
              border: `1px solid ${selected.includes(c) ? 'rgba(167,139,250,0.5)' : 'rgba(255,255,255,0.1)'}`,
              color: selected.includes(c) ? '#c4b5fd' : '#6b7280',
              borderRadius: 999, padding: '4px 12px', fontSize: '0.75rem',
              cursor: 'pointer', fontFamily: 'inherit', transition: 'all 0.15s',
            }}
          >{c}</button>
        ))}
      </div>

      {doctors.length > 0 && (
        <>
          <SectionLabel>Your Doctor (optional)</SectionLabel>
          <select className="input" value={doctorId} onChange={e => setDoctorId(e.target.value)}
            style={{ marginBottom: '1.2rem', cursor: 'pointer' }}
          >
            <option value="">— None —</option>
            {doctors.map(d => <option key={d.doctor_id} value={d.doctor_id}>{d.name}</option>)}
          </select>
        </>
      )}

      <button className="btn-primary" type="submit" disabled={loading}>
        {loading ? 'Creating…' : 'Create Patient Profile →'}
      </button>
    </motion.form>
  )
}

// ── Doctor form ───────────────────────────────────────────────────────────────
function DoctorForm({ error: _e, setError, loading, setLoading, onSuccess }: FormProps) {
  const [name, setName]         = useState('')
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [specialty, setSpecialty] = useState(SPECIALTIES[0])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name || !email || !password) { setError('All fields are required.'); return }
    setLoading(true); setError('')
    try {
      const user = await registerDoctor({ name, email, password, specialty })
      onSuccess(user)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? 'Registration failed.')
    } finally { setLoading(false) }
  }

  return (
    <motion.form onSubmit={submit} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <SectionLabel>Professional</SectionLabel>
      <FormField label="Full Name (include Dr.)">
        <input className="input" value={name} onChange={e => setName(e.target.value)} placeholder="Dr. Jane Smith" />
      </FormField>
      <FormField label="Specialty">
        <select className="input" value={specialty} onChange={e => setSpecialty(e.target.value)}>
          {SPECIALTIES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </FormField>

      <SectionLabel>Account</SectionLabel>
      <FormField label="Email">
        <input className="input" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@hospital.com" />
      </FormField>
      <FormField label="Password">
        <input className="input" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" />
      </FormField>

      <div style={{ marginTop: '1.2rem' }}>
        <button className="btn-primary" type="submit" disabled={loading}>
          {loading ? 'Creating…' : 'Create Doctor Profile →'}
        </button>
      </div>
    </motion.form>
  )
}

// ── Helpers ───────────────────────────────────────────────────────────────────
interface FormProps {
  error: string; setError: (e: string) => void
  loading: boolean; setLoading: (l: boolean) => void
  onSuccess: (u: User) => void
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#4b5563', marginBottom: 10 }}>
      {children}
    </p>
  )
}

function FormField({ label, children, small }: { label: string; children: React.ReactNode; small?: boolean }) {
  return (
    <div style={{ flex: small ? '0 0 80px' : 1, marginBottom: '1rem' }}>
      <label style={{ display: 'block', fontSize: '0.78rem', color: '#9ca3af', fontWeight: 500, marginBottom: 6 }}>
        {label}
      </label>
      {children}
    </div>
  )
}

function Row({ children }: { children: React.ReactNode }) {
  return <div style={{ display: 'flex', gap: '1rem' }}>{children}</div>
}
