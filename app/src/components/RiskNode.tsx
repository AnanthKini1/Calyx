import { motion } from 'framer-motion'

interface Props {
  label: string
  index?: number
}

// Format node IDs to readable labels
function formatLabel(raw: string): string {
  return raw.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export default function RiskNode({ label, index = 0 }: Props) {
  return (
    <motion.span
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.08, duration: 0.4 }}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        background: 'rgba(167,139,250,0.08)',
        border: '1px solid rgba(167,139,250,0.25)',
        borderRadius: 999,
        padding: '4px 12px',
        fontSize: '0.75rem',
        color: '#c4b5fd',
        fontWeight: 500,
        boxShadow: '0 0 12px rgba(167,139,250,0.1)',
        whiteSpace: 'nowrap',
      }}
    >
      <span style={{
        width: 6, height: 6, borderRadius: '50%',
        background: '#a78bfa',
        boxShadow: '0 0 6px #a78bfa',
        flexShrink: 0,
      }} />
      {formatLabel(label)}
    </motion.span>
  )
}
