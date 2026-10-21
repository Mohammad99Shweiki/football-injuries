/** Hand-drawn chalk arrows (SVG with the #chalk displacement filter), decorative only. */
export function DownArrow() {
  return (
    <svg aria-hidden="true" width="44" height="38" viewBox="0 0 44 38">
      <g fill="none" stroke="#E9D98B" strokeWidth="2" strokeLinecap="round" filter="url(#chalk)">
        <path d="M22 3 C 18 12, 26 22, 22 32" />
        <path d="M16 26 L 22 33 L 28 26" />
      </g>
    </svg>
  )
}

export function CurveArrow() {
  return (
    <svg aria-hidden="true" width="28" height="30" viewBox="0 0 28 30">
      <g fill="none" stroke="#E9D98B" strokeWidth="2" strokeLinecap="round" filter="url(#chalk)">
        <path d="M4 6 C 14 6, 20 12, 22 26" />
        <path d="M16 21 L 22 27 L 26 20" />
      </g>
    </svg>
  )
}
