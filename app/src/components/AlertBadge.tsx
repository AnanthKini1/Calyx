import { motion } from 'framer-motion'
import type { Priority } from '../types'

const CONFIG: Record<Priority, { color: string; bg: string; label: string; pulse: boolean }> = {
  CRITICAL: { color: '#ef4444', bg: 'rgba(239,68,68,0.15)', label: '🚨 CRITICAL', pulse: true },
  HIGH:     { color: '#f59e0b', bg: 'rgba(245,158,11,0.15)', label: '⚠ HIGH',     pulse: true },
  MEDIUM:   { color: '#3b82f6', bg: 'rgba(59,130,246,0.15)', label: '● MEDIUM',   pulse: false },
  LOW:      { color: '#8b5cf6', bg: 'rgba(139,92,246,0.15)', label: '◆ LOW',      pulse: false },
  OK:       { color: '#22c55e', bg: 'rgba(34,197,94,0.15)',  label: '✓ OK',       pulse: false },
}

interface Props {
  priority: Priority
  size?: 'sm' | 'md' | 'lg'
}

export default function AlertBadge({ priority, size = 'md' }: Props) {
  const c = CONFIG[priority]
  const fontSize = size === 'sm' ? '0.7rem' : size === 'lg' ? '1rem' : '0.8rem'
  const padding  = size === 'sm' ? '3px 10px' : size === 'lg' ? '8px 20px' : '5px 14px'

  return (
    <motion.span
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 400, damping: 20 }}
      className={c.pulse ? 'pulse-ring' : ''}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        background: c.bg,
        color: c.color,
        border: `1px solid ${c.color}44`,
        borderRadius: 999,
        padding,
        fontSize,
        fontWeight: 700,
        letterSpacing: '0.04em',
        whiteSpace: 'nowrap',
      }}
    >
      {c.label}
    </motion.span>
  )
}
