import type { ControlAction, Flags, Status, Validation } from './types'

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path, { cache: 'no-store' })
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`)
  return (await response.json()) as T
}

export const fetchStatus = () => getJson<Status>('/api/status')
export const fetchValidation = () => getJson<Validation>('/api/validation')

export async function control(action: ControlAction, extra: { flags?: Flags; ids?: string[] } = {}): Promise<void> {
  const response = await fetch('/api/control', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, ...extra }),
  })
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { error?: string }
    throw new Error(body.error ?? `HTTP ${response.status}`)
  }
}
