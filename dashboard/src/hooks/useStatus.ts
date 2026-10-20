import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchStatus } from '../api/client'
import type { Status } from '../api/types'

const POLL_MS = 1000
const STALE_MS = 5000

/** Polls /api/status every second. `stale` turns on after 5 s without a successful poll (data stays frozen). */
export function useStatus() {
  const [status, setStatus] = useState<Status | null>(null)
  const [stale, setStale] = useState(false)
  const lastOk = useRef(0)

  const poll = useCallback(async () => {
    try {
      setStatus(await fetchStatus())
      lastOk.current = Date.now()
      setStale(false)
    } catch {
      if (Date.now() - lastOk.current > STALE_MS) setStale(true)
    }
  }, [])

  useEffect(() => {
    lastOk.current = Date.now()
    const first = window.setTimeout(() => void poll(), 0)
    const timer = window.setInterval(() => void poll(), POLL_MS)
    return () => {
      window.clearTimeout(first)
      window.clearInterval(timer)
    }
  }, [poll])

  return { status, stale, refresh: poll }
}
