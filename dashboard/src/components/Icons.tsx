// Stroke icons used by section eyebrows and stat labels (24x24 viewBox), copied from the designs.
import type { ReactNode } from 'react'

const EYEBROW: Record<string, ReactNode> = {
  target: <><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><path d="M12 12h.01" /></>,
  tray: <><path d="M12 3v11" /><path d="M7 9l5 5 5-5" /><path d="M4 16v4h16v-4" /></>,
  play: <><circle cx="5" cy="18" r="2" /><path d="M7 17 C 10 9, 14 16, 17 8" /><path d="M14 8h3.5v3.5" /><path d="M16 17l4 4M20 17l-4 4" /></>,
  gauge: <><path d="M4 16a8 8 0 0 1 16 0" /><path d="M12 16l4.5-5" /><path d="M3 20h18" /></>,
  pitch: <><rect x="3" y="5" width="18" height="14" rx="1.5" /><path d="M12 5v14" /><circle cx="12" cy="12" r="2.5" /><path d="M3 9h3v6H3M21 9h-3v6h3" /></>,
  list: <><path d="M9 6h11M9 12h11M9 18h11" /><path d="M4 6h.01M4 12h.01M4 18h.01" /></>,
  clipboard: <><rect x="5" y="4" width="14" height="17" rx="2" /><path d="M9 3h6v3H9z" /><path d="M9 13l2 2 4-4" /></>,
  camera: <><rect x="3" y="7" width="18" height="13" rx="2" /><path d="M8 7l1.5-3h5L16 7" /><circle cx="12" cy="13.5" r="3.5" /></>,
  sheet: <><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M3 9h18M9 4v16" /></>,
  warning: <><path d="M12 3l9.5 17h-19z" /><path d="M12 10v4" /><path d="M12 17h.01" /></>,
  shield: <path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" />,
  cross: <path d="M10 4h4v6h6v4h-6v6h-4v-6H4v-4h6z" />,
  clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
}

export type EyebrowIcon = keyof typeof EYEBROW

export function EyebrowSvg({ name }: { name: EyebrowIcon }) {
  return (
    <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--annotation)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      {EYEBROW[name]}
    </svg>
  )
}

/** Small icon in the current text colour (stat labels, buttons). */
export function MiniIcon({ size = 13, width = 2.2, children }: { size?: number; width?: number; children: ReactNode }) {
  return (
    <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={width} strokeLinecap="round" strokeLinejoin="round">
      {children}
    </svg>
  )
}

export const RetryIcon = ({ size = 16 }: { size?: number }) => (
  <MiniIcon size={size}><path d="M20 11a8 8 0 1 0-2.3 5.7" /><path d="M20 4v7h-7" /></MiniIcon>
)
