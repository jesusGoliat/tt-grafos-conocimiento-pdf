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
  const base = result.filename.replace(/\.pdf$/i, '')
  const json = JSON.stringify(result.content_list, null, 2)

  // Las imágenes del Markdown son relativas (images/xxx.jpg): se resuelven contra el backend.
  const urlTransform = (url: string) =>
    defaultUrlTransform(url.startsWith('images/') ? `${result.assets_base_url}${url}` : url)

  return (
    <section className="card result">
      <div className="result-header">
        <h2>Resultado · {result.filename}</h2>
        <div className="actions">
          <button onClick={() => download(`${base}.md`, result.markdown, 'text/markdown')}>Descargar .md</button>
          <button onClick={() => download(`${base}.json`, json, 'application/json')}>Descargar .json</button>
        </div>
      </div>
      <div className="tabs" role="tablist">
        {TABS.map(([id, label]) => (
          <button key={id} role="tab" aria-selected={tab === id} className={tab === id ? 'active' : ''} onClick={() => setTab(id)}>
            {label}
          </button>
        ))}
      </div>

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
          <table>
            <thead>
              <tr><th>Tipo de bloque</th><th>Cantidad</th></tr>
            </thead>
            <tbody>
              {Object.entries(result.stats.blocks_by_type).map(([type, count]) => (
                <tr key={type}>
                  <td>{BLOCK_LABELS[type] ?? type}</td>
                  <td>{count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
