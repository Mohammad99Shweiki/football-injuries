import { LOGO_CREDITS, PHOTO_CREDITS } from '../data/moments'
import { Eyebrow } from './Eyebrow'

/** Required attribution (CC BY-SA): photo and logo credits, on both screens (HANDOFF section 13).
 *  `compact` folds the list behind one line (analysis pages), still one click away. */
export function CreditsFooter({ compact = false }: { compact?: boolean }) {
  if (compact) {
    return (
      <footer aria-label="Photo credits" className="credits-compact">
        <details>
          <summary>Photo and logo credits (Wikimedia Commons, CC BY-SA)</summary>
          <CreditsList />
        </details>
      </footer>
    )
  }
  return (
    <footer aria-label="Photo credits" className="credits panel">
      <Eyebrow label="Photo credits — Wikimedia Commons" icon="camera" />
      <CreditsList />
    </footer>
  )
}

function CreditsList() {
  return (
    <>
      <div className="credits-list">
        {PHOTO_CREDITS.map((c) => (
          <a key={c.player} href={c.page}>{c.player}: {c.artist} ({c.license})</a>
        ))}
      </div>
      <div className="credits-list logos">
        <span>Logos (public domain, Commons):</span>
        {LOGO_CREDITS.map((c) => <a key={c.name} href={c.page}>{c.name}</a>)}
      </div>
      <div className="credits-note">
        Player portraits, not photos of the injuries themselves, toned to look like film prints. CC BY-SA images are shared
        under the same licence. Logos and names are trademarks of their owners, used here only to identify them in a
        non-commercial academic project.
      </div>
    </>
  )
}
