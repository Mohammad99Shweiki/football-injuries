import { useResource } from './api'
import type { Row } from './api'
import { Heatmap, MetricVsK } from './charts'

const METRICS: { key: string; title: string; better: 'higher' | 'lower'; kind?: string }[] = [
  { key: 'inertia', title: 'Within-cluster spread (elbow)', better: 'lower' },
  { key: 'silhouette', title: 'Silhouette', better: 'higher' },
  { key: 'davies_bouldin', title: 'Davies–Bouldin', better: 'lower' },
  { key: 'calinski_harabasz', title: 'Calinski–Harabasz', better: 'higher' },
  { key: 'stability_ari', title: 'Bootstrap stability (mean ARI)', better: 'higher' },
  { key: 'min_jaccard', title: 'Weakest cluster (bootstrap Jaccard)', better: 'higher' },
  { key: 'ward_ari', title: 'Agreement with Ward (ARI)', better: 'higher' },
  { key: 'bic', title: 'Gaussian mixture BIC', better: 'lower', kind: 'gmm' },
]
const FIGURES = ['04_k_selection.png', '04_centroids.png', '04_pca.png', '04_dendrograms.png']

/** Phase 4 at a glance: how k was chosen, what the clusters are, and how far other methods agree. */
export function Clustering() {
  const source = useResource<Record<string, Row[]>>('results-bundle')
  const rows = source.data?.clustering
  if (source.error) return <p className="analysis-alert" role="alert">{source.error}</p>
  if (!rows) return <p role="status">Loading the clustering results…</p>
  const of = (kind: string) => rows.filter((r) => r.kind === kind)
  const measures = (kind: string) => [...new Set(of(kind).map((r) => String(r.measure)))]
  return (
    <>
      <section className="analysis-panel">
        <h2>Choosing the number of styles</h2>
        <p className="analysis-muted">
          K-means for k = 2…10 per phase of play (<span className="swatch attack" /> attack, <span className="swatch defence" /> defence);
          the dashed line is the chosen k = 4. A k is usable when every cluster's bootstrap Jaccard is at least 0.6 and none is
          below 3% of team-seasons. k = 4 is an interpretive choice on a continuum: for attack it is borderline (weakest
          cluster 0.64), and silhouette and the Gaussian mixture prefer fewer clusters.
        </p>
        <div className="metric-grid">
          {METRICS.map((m) => (
            <MetricVsK key={m.key} title={m.title} better={m.better}
              rows={of(m.kind || 'k').map((r) => ({ phase: String(r.phase), k: Number(r.k), value: Number(r[m.key]) }))} />
          ))}
        </div>
      </section>
      <section className="analysis-panel">
        <h2>What each style is: cluster centres</h2>
        <p className="analysis-muted">Mean of each dimension per style (standardised; orange above the all-team average, blue below). Names follow from a fixed rule, e.g. the highest possession is Positional possession.</p>
        <div className="analysis-grid-2">
          {['attack', 'defence'].map((ph) => {
            const cen = of('centroid').filter((r) => r.phase === ph)
            return (
              <div key={ph}>
                <h3>{ph === 'attack' ? 'Attacking styles' : 'Defensive styles'}</h3>
                <Heatmap mode="z" corner="style" rows={[...new Set(cen.map((r) => String(r.style)))]} cols={[...new Set(cen.map((r) => String(r.dimension).replaceAll('_', ' ')))]}
                  cell={(s, d) => {
                    const r = cen.find((x) => x.style === s && String(x.dimension).replaceAll('_', ' ') === d)
                    return r ? { value: Number(r.value), label: Number(r.value).toFixed(2), title: `${s}: ${d} ${Number(r.value).toFixed(2)}` } : null
                  }} caption={`${ph} centroids`} />
              </div>
            )
          })}
        </div>
      </section>
      <div className="analysis-grid-2">
        <section className="analysis-panel">
          <h2>Do other methods find the same styles?</h2>
          <p className="analysis-muted">Ward and the Gaussian mixture are independent checks (moderate agreement: styles form a continuum). The consensus is built half from bootstrap K-means, so it summarises stability rather than validating.</p>
          <Heatmap mode="z" corner="measure" rows={measures('agreement')} cols={['attack', 'defence']}
            cell={(m, ph) => {
              const r = of('agreement').find((x) => x.measure === m && x.phase === ph)
              return r ? { value: 0, label: Number(r.value) > 1.5 ? Number(r.value).toFixed(0) : Number(r.value).toFixed(2) } : null
            }} caption="Agreement between clustering methods" />
        </section>
        <section className="analysis-panel">
          <h2>Sensitivity clusterings</h2>
          <p className="analysis-muted">k = 3, and K-means on dimensions centred within each league-season (style relative to the league that season). Phase 5 checks that the injury results keep their direction under both.</p>
          <Heatmap mode="z" corner="measure" rows={measures('sensitivity')} cols={['attack', 'defence']}
            cell={(m, ph) => {
              const r = of('sensitivity').find((x) => x.measure === m && x.phase === ph)
              return r ? { value: 0, label: Number(r.value).toFixed(2) } : null
            }} caption="Sensitivity clusterings" />
        </section>
      </div>
      <section className="analysis-panel">
        <h2>Figures</h2>
        <div className="figure-grid">
          {FIGURES.map((f) => (
            <a key={f} href={`/api/analysis/figures/${f}`} target="_blank" rel="noreferrer">
              <img className="analysis-figure" src={`/api/analysis/figures/${f}`} alt={f.replace('.png', '').replaceAll('_', ' ')} loading="lazy" />
              <span>{f}</span>
            </a>
          ))}
        </div>
        <p className="analysis-muted"><a href="/analysis/studio/phase-04/step-2">Every step of Phase 4 in the Studio →</a></p>
      </section>
    </>
  )
}
