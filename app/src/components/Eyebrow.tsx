import { EyebrowSvg, type EyebrowIcon } from './Icons'

/** Section eyebrow: "03 — The play" in mono caps with a stroke icon (HANDOFF section 7). */
export function Eyebrow({ number, label, icon }: { number?: string; label: string; icon: EyebrowIcon }) {
  return (
    <div className="eyebrow">
      <EyebrowSvg name={icon} />
      <span>{number ? `${number} — ${label}` : label}</span>
    </div>
  )
}
