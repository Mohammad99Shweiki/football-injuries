import type { ReactNode } from 'react'

/** Secondary content, folded away so each section shows one main view. */
export function More({ label, children, open = false }: { label: string; children: ReactNode; open?: boolean }) {
  return (
    <details className="analysis-more" open={open}>
      <summary>{label}</summary>
      <div className="analysis-more-body">{children}</div>
    </details>
  )
}
