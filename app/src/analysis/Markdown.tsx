import type { ReactNode } from 'react'

/** Inline markdown: **bold**, *italic*, `code`, [links](url), images rewritten to the figures API. */
function inline(text: string, key = 0): ReactNode[] {
  const out: ReactNode[] = []
  const re = /(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`|!?\[[^\]]*\]\([^)]+\))/g
  let last = 0
  let m: RegExpExecArray | null
  let i = 0
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(text.slice(last, m.index))
    const t = m[0]
    const k = `${key}-${i++}`
    if (t.startsWith('**')) out.push(<strong key={k}>{inline(t.slice(2, -2), i)}</strong>)
    else if (t.startsWith('`')) out.push(<code key={k}>{t.slice(1, -1)}</code>)
    else if (t.startsWith('*')) out.push(<em key={k}>{inline(t.slice(1, -1), i)}</em>)
    else {
      const [, label, href] = /!?\[([^\]]*)\]\(([^)]+)\)/.exec(t)!
      const figure = href.match(/figures\/([\w.-]+\.png)$/)
      if (t.startsWith('!'))
        out.push(<img key={k} className="analysis-figure" alt={label} loading="lazy" src={figure ? `/api/analysis/figures/${figure[1]}` : href} />)
      else out.push(<a key={k} href={href} target={href.startsWith('http') ? '_blank' : undefined} rel="noreferrer">{label}</a>)
    }
    last = m.index + t.length
  }
  if (last < text.length) out.push(text.slice(last))
  return out
}

const cells = (line: string) => line.trim().replace(/^\||\|$/g, '').split(/(?<!\\)\|/).map((c) => c.trim().replace(/\\\|/g, '|'))

/** Block markdown as used in the phase notes and reports: headings, paragraphs, lists, tables, code, rules. */
export function Markdown({ text, className = '' }: { text: string; className?: string }) {
  const lines = text.replace(/\r/g, '').split('\n')
  const blocks: ReactNode[] = []
  let i = 0
  while (i < lines.length) {
    const line = lines[i]
    const k = blocks.length
    if (!line.trim()) { i++; continue }
    if (line.startsWith('```')) {
      const body: string[] = []
      for (i++; i < lines.length && !lines[i].startsWith('```'); i++) body.push(lines[i])
      i++
      blocks.push(<pre key={k}>{body.join('\n')}</pre>)
    } else if (/^#{1,6} /.test(line)) {
      const level = Math.min(6, line.match(/^#+/)![0].length + 1)
      const H = `h${level}` as 'h2'
      blocks.push(<H key={k}>{inline(line.replace(/^#+ /, ''))}</H>)
      i++
    } else if (line.trim().startsWith('|') && lines[i + 1]?.trim().match(/^\|?[\s:|-]+\|?$/)) {
      const head = cells(line)
      const body: string[][] = []
      for (i += 2; i < lines.length && lines[i].trim().startsWith('|'); i++) body.push(cells(lines[i]))
      blocks.push(
        <div key={k} className="table-scroll" tabIndex={0} role="region" aria-label="Table">
          <table className="analysis-table">
            <thead><tr>{head.map((h, j) => <th key={j}>{inline(h)}</th>)}</tr></thead>
            <tbody>{body.map((r, n) => <tr key={n}>{r.map((c, j) => <td key={j}>{inline(c)}</td>)}</tr>)}</tbody>
          </table>
        </div>,
      )
    } else if (/^\s*([-*]|\d+\.) /.test(line)) {
      const ordered = /^\s*\d+\. /.test(line)
      const items: string[] = []
      for (; i < lines.length && (/^\s*([-*]|\d+\.) /.test(lines[i]) || (/^\s{2,}\S/.test(lines[i]) && items.length)); i++) {
        if (/^\s*([-*]|\d+\.) /.test(lines[i])) items.push(lines[i].replace(/^\s*([-*]|\d+\.) /, ''))
        else items[items.length - 1] += ' ' + lines[i].trim()
      }
      const L = ordered ? 'ol' : 'ul'
      blocks.push(<L key={k}>{items.map((it, j) => <li key={j}>{inline(it)}</li>)}</L>)
    } else if (/^---+$/.test(line.trim())) {
      blocks.push(<hr key={k} />)
      i++
    } else {
      const para: string[] = []
      for (; i < lines.length && lines[i].trim() && !/^(#{1,6} |```|\s*([-*]|\d+\.) |\|)/.test(lines[i]); i++) para.push(lines[i].trim())
      if (!para.length) { para.push(lines[i].trim()); i++ }
      blocks.push(<p key={k}>{inline(para.join(' '))}</p>)
    }
  }
  return <div className={`markdown ${className}`}>{blocks}</div>
}
