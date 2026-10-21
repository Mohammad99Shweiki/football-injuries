import { useCallback, useEffect, useRef, useState } from 'react'
import type { MouseEvent as ReactMouseEvent } from 'react'

export interface Pointer {
  x: number
  y: number
  width: number
  hot: boolean
}

/** Cursor position relative to the board, throttled with requestAnimationFrame (spotlight, prints, Chalky's eyes). */
export function usePointer() {
  const [pointer, setPointer] = useState<Pointer>({ x: 0, y: 0, width: 1440, hot: false })
  const frame = useRef<number | null>(null)
  const next = useRef<Pointer>(pointer)

  const onMouseMove = useCallback((event: ReactMouseEvent<HTMLElement>) => {
    const rect = event.currentTarget.getBoundingClientRect()
    next.current = { x: Math.round(event.clientX - rect.left), y: Math.round(event.clientY - rect.top), width: rect.width, hot: true }
    if (frame.current !== null) return
    frame.current = requestAnimationFrame(() => {
      frame.current = null
      setPointer(next.current)
    })
  }, [])

  const onMouseLeave = useCallback(() => setPointer((p) => ({ ...p, hot: false })), [])

  useEffect(() => () => {
    if (frame.current !== null) cancelAnimationFrame(frame.current)
  }, [])

  return { pointer, onMouseMove, onMouseLeave }
}
