import { useState } from 'react'
import Markdown, { defaultUrlTransform } from 'react-markdown'
import rehypeRaw from 'rehype-raw'
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize'
import remarkGfm from 'remark-gfm'
import type { ExtractionResult } from '../types'

const TABS = [
  ['rendered', 'Vista'],
  ['markdown', 'Markdown'],
  ['json', 'JSON estructurado'],
  ['stats', 'Estadísticas'],
] as const
type Tab = (typeof TABS)[number][0]

const BLOCK_LABELS: Record<string, string> = {
  title: 'Títulos',
  text: 'Párrafos',
  table: 'Tablas',
  image: 'Imágenes',
  equation: 'Ecuaciones',
  list: 'Listas',
  code: 'Código',
  header: 'Encabezados de página',
  footer: 'Pies de página',
  page_number: 'Números de página',
  aside_text: 'Texto lateral',
  page_footnote: 'Notas al pie',
}

// MinerU emite las tablas como HTML; se permite rowspan/colspan y se elimina lo demás.
const schema = {
  ...defaultSchema,
  attributes: { ...defaultSchema.attributes, td: ['rowSpan', 'colSpan'], th: ['rowSpan', 'colSpan'] },
}

function download(filename: string, content: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }))
  const link = Object.assign(document.createElement('a'), { href: url, download: filename })
  link.click()
  URL.revokeObjectURL(url)
}

export function ResultViewer({ result }: { result: ExtractionResult }) {
  const [tab, setTab] = useState<Tab>('rendered')
  const [comparing, setComparing] = useState(false)
  const base = result.filename.replace(/\.pdf$/i, '')
  const json = JSON.stringify(result.content_list, null, 2)
  const blockTypes = Object.entries(result.stats.blocks_by_type).sort((a, b) => b[1] - a[1])
  const maxCount = Math.max(1, ...blockTypes.map(([, count]) => count))

  // Las imágenes del Markdown son relativas (images/xxx.jpg): se resuelven contra el backend.
  const urlTransform = (url: string) =>
    defaultUrlTransform(url.startsWith('images/') ? `${result.assets_base_url}${url}` : url)

  return (
    <section className={`card result${comparing ? ' comparing' : ''}`}>
      <div className="result-header">
        <div>
          <p className="eyebrow">Resultado</p>
          <h2>{result.filename}</h2>
        </div>
        <div className="actions">
          <button aria-pressed={comparing} onClick={() => setComparing(!comparing)}>
            {comparing ? 'Ocultar PDF' : 'Comparar con el PDF'}
          </button>
          <button onClick={() => download(`${base}.md`, result.markdown, 'text/markdown')}>Descargar .md</button>
          <button onClick={() => download(`${base}.json`, json, 'application/json')}>Descargar .json</button>
        </div>
      </div>
      <div className="tabs" role="tablist" aria-label="Formato del resultado">
        {TABS.map(([id, label]) => (
          <button key={id} role="tab" aria-selected={tab === id} className={tab === id ? 'active' : ''} onClick={() => setTab(id)}>
            {label}
          </button>
        ))}
      </div>

      <div className={comparing ? 'compare' : undefined}>
        {comparing && (
          <div className="pdf-pane">
            <iframe src={`${result.pdf_url}#view=FitH&navpanes=0`} title={`PDF original: ${result.filename}`} />
            <a href={result.pdf_url} target="_blank" rel="noreferrer">
              Abrir el PDF en otra pestaña
            </a>
          </div>
        )}
        <div className="result-pane">
          {tab === 'rendered' && (
            <article className="markdown-body">
              <Markdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw, [rehypeSanitize, schema]]} urlTransform={urlTransform}>
                {result.markdown}
              </Markdown>
            </article>
          )}
          {tab === 'markdown' && <pre className="code">{result.markdown}</pre>}
          {tab === 'json' && <pre className="code">{json}</pre>}
          {tab === 'stats' && (
            <div className="stats">
              <dl>
                <div><dt>Páginas</dt><dd>{result.stats.pages}</dd></div>
                <div><dt>Bloques</dt><dd>{result.stats.blocks_total}</dd></div>
                <div><dt>Palabras</dt><dd>{result.stats.words.toLocaleString('es-MX')}</dd></div>
                <div><dt>Caracteres</dt><dd>{result.stats.characters.toLocaleString('es-MX')}</dd></div>
              </dl>
              <h3>Bloques por tipo</h3>
              <ul className="block-bars">
                {blockTypes.map(([type, count]) => (
                  <li key={type}>
                    <span className="block-label">{BLOCK_LABELS[type] ?? type}</span>
                    <span className="block-track">
                      <span style={{ width: `${(count / maxCount) * 100}%` }} />
                    </span>
                    <span className="block-count">{count}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
