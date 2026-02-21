import { motion } from 'framer-motion'

interface Props {
  label: string
  value: number
  color: string
  bgColor: string
}

export default function TissueBar({ label, value, color, bgColor }: Props) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontSize: '0.8rem', color: '#9ca3af', fontWeight: 500 }}>{label}</span>
        <span style={{ fontSize: '0.8rem', color, fontWeight: 700 }}>{value.toFixed(0)}%</span>
      </div>
      <div
        style={{
          height: 8,
          borderRadius: 999,
          background: 'rgba(255,255,255,0.06)',
          overflow: 'hidden',
        }}
      >
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.9, ease: 'easeOut', delay: 0.2 }}
          style={{
            height: '100%',
            borderRadius: 999,
            background: `linear-gradient(90deg, ${bgColor}, ${color})`,
            boxShadow: `0 0 8px ${color}66`,
          }}
        />
      </div>
    </div>
  )
}
