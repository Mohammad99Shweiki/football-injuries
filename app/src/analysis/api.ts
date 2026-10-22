import { useEffect, useState } from 'react'

export async function request<T>(path: string, body?: object): Promise<T> {
  const response = await fetch(
    `/api/analysis/${path}`,
    body
      ? {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        }
      : { cache: 'no-store' },
  )
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.error || `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

export function useResource<T>(path: string, interval = 0) {
  const [state, setState] = useState<{
    path: string
    data?: T
    error?: string
  }>({ path })
  useEffect(() => {
    let active = true
    const load = () =>
      request<T>(path).then(
        (data) => {
          if (active) setState({ path, data })
        },
        (error) => {
          if (active)
            setState((previous) => ({
              ...previous,
              path,
              error: String(error.message),
            }))
        },
      )
    void load()
    const timer = interval ? window.setInterval(load, interval) : undefined
    return () => {
      active = false
      window.clearInterval(timer)
    }
  }, [path, interval])
  return state.path === path ? state : { path }
}

export interface Phase {
  id: string
  title: string
  status: string
  stale: boolean
  stale_reasons: string[]
  finished: string | null
  duration_s: number | null
  run_id: string | null
  steps: {
    index: number
    title: string
    status: string
    checks: number
    checks_failed: number
    duration_s: number | null
  }[]
}
export interface Job {
  running: boolean
  scrape_busy: boolean
  output: string[]
  returncode?: number
  current_phase?: string
}
export type Row = Record<string, string | number | boolean | null>
export interface Table {
  columns: { name: string; type: string }[]
  rows: unknown[][]
  total: number
  offset: number
  limit: number
}
export interface Mapping {
  file: string
  path: string
  rows: number
  hash: string
  approved_current: boolean
  approval: { date: string } | null
}
export interface Step {
  title: string
  note: string
  code: string[]
  status: string
  run: null | {
    duration_s: number
    checks: { statement: string; passed: number; failed: number }[]
    log: Row[]
    stdout: string
    error: { traceback: string } | null
    outputs: { path: string; kind: string; rows?: number }[]
    previews: {
      kind: string
      columns?: string[]
      rows?: unknown[][]
      index?: unknown[]
      text?: string
    }[]
  }
}
