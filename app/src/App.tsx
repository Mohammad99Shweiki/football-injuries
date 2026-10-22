import { ConsolePage } from './console/ConsolePage'
import { MascotDebug } from './debug/MascotDebug'
import { ReportPage } from './report/ReportPage'
import { AnalysisPage } from './analysis/AnalysisPage'
import './analysis/analysis.css'

export function App() {
  const path = window.location.pathname.replace(/\/$/, '') || '/'
  if (new URLSearchParams(window.location.search).get('debug') === 'mascot')
    return <MascotDebug />
  const analysis = path.startsWith('/analysis')
  const validation = path === '/validation' || path === '/scraping/validation'
  return (
    <>
      <a className="skip-link" href="#workspace">
        Skip to workspace
      </a>
      <nav className="app-nav" aria-label="Project navigation">
        <a className="project-brand" href="/">
          THE FOOTBALL STUDY <small>Playing style × injuries</small>
        </a>
        <div className="workflow-nav">
          <a href="/scraping" aria-current={!analysis ? 'step' : undefined}>
            <span>01</span> Scraping
          </a>
          <span className="workflow-arrow" aria-hidden="true">
            →
          </span>
          <a href="/analysis" aria-current={analysis ? 'step' : undefined}>
            <span>02</span> Analysis
          </a>
        </div>
      </nav>
      {!analysis && (
        <nav className="workspace-tabs" aria-label="Scraping pages">
          <a href="/scraping" aria-current={!validation ? 'page' : undefined}>
            Run console
          </a>
          <a
            href="/scraping/validation"
            aria-current={validation ? 'page' : undefined}
          >
            Validation report
          </a>
          <a href="/analysis">Continue to analysis →</a>
        </nav>
      )}
      <main id="workspace">
        {analysis ? (
          <AnalysisPage path={path} />
        ) : validation ? (
          <ReportPage />
        ) : (
          <ConsolePage />
        )}
      </main>
    </>
  )
}
