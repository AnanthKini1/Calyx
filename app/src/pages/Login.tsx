import { AnimatePresence, motion } from 'framer-motion'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../api/client'
import { setSession } from '../api/session'
import type { User } from '../types'

export default function Login() {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) { setError('Please enter your email and password.'); return }
    setLoading(true)
    setError('')
    try {
      const user = await login(email.trim(), password) as User
      setSession(user)
      window.location.href = '/'   // full reload so App re-reads sessionStorage
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? 'Sign-in failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#0a0a0f',
      padding: '2rem',
    }}>
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        style={{ textAlign: 'center', marginBottom: '2.5rem' }}
      >
        <p style={{
          fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.25em',
          textTransform: 'uppercase', color: '#a78bfa', marginBottom: '1rem',
        }}>
          Wound Intelligence Platform
        </p>
        <h1 style={{
          fontSize: 'clamp(2.5rem, 5vw, 3.5rem)',
          fontWeight: 800,
          color: '#f1f1f1',
          margin: '0 0 0.75rem',
          letterSpacing: '-0.03em',
        }}>
          ChroniScan
        </h1>
        <p style={{ color: '#6b7280', fontSize: '0.95rem', maxWidth: 380, lineHeight: 1.6 }}>
          Sub-visual wound analysis powered by computer vision and clinical knowledge graphs.
        </p>
      </motion.div>

      {/* Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.15 }}
        className="glass"
        style={{ width: '100%', maxWidth: 420, padding: '2.5rem' }}
      >
        <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.4rem', color: '#f1f1f1' }}>
          Sign In
        </h2>
        <p style={{ color: '#6b7280', fontSize: '0.85rem', marginBottom: '1.8rem' }}>
          Enter your email and password to continue.
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.78rem', color: '#9ca3af', fontWeight: 500, marginBottom: 6, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
              Email
            </label>
            <input
              className="input"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              autoComplete="email"
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.78rem', color: '#9ca3af', fontWeight: 500, marginBottom: 6, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
              Password
            </label>
            <input
              className="input"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>

          <AnimatePresence>
            {error && (
              <motion.p
                initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                style={{
                  color: '#ef4444', fontSize: '0.82rem', marginBottom: '1rem',
                  background: 'rgba(239,68,68,0.08)', borderRadius: '0.5rem',
                  padding: '0.6rem 0.8rem', border: '1px solid rgba(239,68,68,0.2)',
                }}
              >
                {error}
              </motion.p>
            )}
          </AnimatePresence>

          <button className="btn-primary" type="submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign In →'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '1.5rem' }}>
          <span style={{ color: '#4b5563', fontSize: '0.85rem' }}>
            Don't have an account?{' '}
          </span>
          <button
            onClick={() => navigate('/create-profile')}
            style={{
              background: 'none', border: 'none', color: '#a78bfa',
              fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer',
              padding: 0, fontFamily: 'inherit',
            }}
          >
            Create a profile
          </button>
        </div>
      </motion.div>

      {/* Demo hint */}
      <motion.p
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}
        style={{ marginTop: '2rem', color: '#374151', fontSize: '0.75rem', textAlign: 'center' }}
      >
        Demo — Patient: <code style={{ color: '#6b7280' }}>maria@chroniscan.com</code> / <code style={{ color: '#6b7280' }}>password123</code>
        <br />
        Doctor: <code style={{ color: '#6b7280' }}>priya@chroniscan.com</code> / <code style={{ color: '#6b7280' }}>doctor123</code>
      </motion.p>
    </div>
  )
}
