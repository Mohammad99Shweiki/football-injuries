import { ConsolePage } from './console/ConsolePage'
import { MascotDebug } from './debug/MascotDebug'
import { ReportPage } from './report/ReportPage'

/** Two screens, no router dependency: /validation is the report, everything else the console. */
export function App() {
  const params = new URLSearchParams(window.location.search)
  if (params.get('debug') === 'mascot') return <MascotDebug />
  if (window.location.pathname.replace(/\/$/, '') === '/validation') return <ReportPage />
  return <ConsolePage />
}
