import { useEffect, useState } from 'react'

interface Props { text: string }

export default function ReasoningBox({ text }: Props) {
  const [displayed, setDisplayed] = useState('')
  const [done, setDone] = useState(false)

  useEffect(() => {
    setDisplayed('')
    setDone(false)
    let i = 0
    // Faster for longer texts
    const delay = text.length > 300 ? 8 : 15
    const timer = setInterval(() => {
      i++
      setDisplayed(text.slice(0, i))
      if (i >= text.length) {
        clearInterval(timer)
        setDone(true)
      }
    }, delay)
    return () => clearInterval(timer)
  }, [text])

  return (
    <p style={{
      fontSize: '0.83rem',
      lineHeight: 1.7,
      color: '#9ca3af',
      margin: 0,
      minHeight: '4rem',
    }}>
      {displayed}
      {!done && <span className="cursor" style={{ color: '#a78bfa' }}>▋</span>}
    </p>
  )
}
