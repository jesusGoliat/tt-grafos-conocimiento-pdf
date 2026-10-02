import { useCallback, useEffect, useState } from 'react'
import { ApiError, getDocument, getHealth, getResult, listDocuments, uploadDocument } from './api/client'
import { DocumentList } from './components/DocumentList'
import { ProgressIndicator } from './components/ProgressIndicator'
import { ResultViewer } from './components/ResultViewer'
import { UploadForm } from './components/UploadForm'
import type { DocumentStatus, ExtractionResult, Health } from './types'

const POLL_MS = 2000
const isFinished = (doc: DocumentStatus) => doc.status === 'done' || doc.status === 'failed'
const message = (err: unknown) => (err instanceof Error ? err.message : String(err))

export default function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [documents, setDocuments] = useState<DocumentStatus[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [current, setCurrent] = useState<DocumentStatus | null>(null)
  const [uploadFraction, setUploadFraction] = useState<number | null>(null)
  const [result, setResult] = useState<ExtractionResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const refreshList = useCallback(() => {
    listDocuments().then(setDocuments).catch((err) => setError(message(err)))
  }, [])

  useEffect(() => {
    getHealth().then(setHealth).catch((err) => setError(message(err)))
    refreshList()
  }, [refreshList])

  // Consulta el estado del documento seleccionado hasta que termine y entonces carga el resultado.
  useEffect(() => {
    if (!selectedId) return
    let cancelled = false
    let timer: number | undefined

    const poll = async () => {
      try {
        const doc = await getDocument(selectedId)
        if (cancelled) return
        setCurrent(doc)
        if (!isFinished(doc)) {
          timer = window.setTimeout(poll, POLL_MS)
          return
        }
        refreshList()
        if (doc.status === 'done') {
          const extraction = await getResult(selectedId)
          if (!cancelled) setResult(extraction)
        }
      } catch (err) {
        if (!cancelled) setError(message(err))
      }
    }
    poll()
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [selectedId, refreshList])

  const select = (id: string) => {
    setError(null)
    setResult(null)
    setCurrent(null)
    setSelectedId(id)
  }

  const onSubmit = async (file: File) => {
    setError(null)
    setResult(null)
    setCurrent(null)
    setSelectedId(null)
    setUploadFraction(0)
    try {
      const doc = await uploadDocument(file, setUploadFraction)
      refreshList()
      select(doc.id)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : message(err))
    } finally {
      setUploadFraction(null)
    }
  }

  const busy = uploadFraction !== null || (current !== null && !isFinished(current))
  const showProgress = uploadFraction !== null || (current !== null && current.status !== 'done')

  return (
    <div className="layout">
      <header>
        <h1>Extracción de contenido de PDF</h1>
        <p className="muted">
          Prototipo 1 · Grafos de conocimiento a partir de PDF · Motor: MinerU
          {health && ` (${health.mineru_model_version})`}
        </p>
        {health && !health.mineru_token_configured && (
          <p className="warning">
            El backend no tiene token de MinerU. Define <code>MINERU_API_TOKEN</code> en <code>backend/.env</code> y
            reinicia el servidor.
          </p>
        )}
      </header>

      <aside>
        <UploadForm disabled={busy} onSubmit={onSubmit} />
        <DocumentList documents={documents} selectedId={selectedId} onSelect={select} />
      </aside>

      <main>
        {error && <p className="error card">{error}</p>}
        {showProgress && <ProgressIndicator uploadFraction={uploadFraction} doc={current} />}
        {result && <ResultViewer result={result} />}
        {!showProgress && !result && !error && (
          <section className="card empty">
            <p className="muted">Sube un PDF o selecciona un documento para ver su contenido extraído.</p>
          </section>
        )}
      </main>
    </div>
  )
}
