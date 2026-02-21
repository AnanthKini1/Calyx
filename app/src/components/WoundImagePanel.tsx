import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'

interface Props {
  src: string   // base64 data URI or URL
  alt?: string
}

export default function WoundImagePanel({ src, alt = 'Wound scan' }: Props) {
  const [scanning, setScanning] = useState(true)

  useEffect(() => {
    setScanning(true)
    const t = setTimeout(() => setScanning(false), 1600)
    return () => clearTimeout(t)
  }, [src])

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      style={{
        position: 'relative',
        borderRadius: '1rem',
        overflow: 'hidden',
        border: '1px solid rgba(255,255,255,0.1)',
        boxShadow: '0 0 40px rgba(167,139,250,0.08)',
        background: '#111',
      }}
    >
      <img
        src={src}
        alt={alt}
        style={{ width: '100%', display: 'block', maxHeight: 360, objectFit: 'contain' }}
      />
      {scanning && <div className="scan-line" />}
    </motion.div>
  )
}
