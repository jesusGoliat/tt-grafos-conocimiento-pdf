import type { DocumentStatus } from '../types'
import { STATUS_LABELS } from '../format'

interface Props {
  uploadFraction: number | null
  doc: DocumentStatus | null
}

const STEPS = ['upload', 'queued', 'uploading', 'processing', 'done'] as const
const STEP_LABELS: Record<(typeof STEPS)[number], string> = {
  upload: 'Subida',
  queued: 'Validado',
  uploading: 'Envío a MinerU',
  processing: 'Extracción',
  done: 'Listo',
}

const REMOTE_LABELS: Record<string, string> = {
  'waiting-file': 'esperando archivo',
  pending: 'en cola de MinerU',
  running: 'procesando',
  converting: 'generando formatos',
  done: 'terminado',
}

export function ProgressIndicator({ uploadFraction, doc }: Props) {
  const current = doc ? doc.status : 'upload'
  const failed = current === 'failed'
  const index = failed ? -1 : STEPS.indexOf(current as (typeof STEPS)[number])

  let percent = 0
  let detail = ''
  if (!doc) {
    percent = Math.round((uploadFraction ?? 0) * 100)
    detail = `Subiendo archivo… ${percent}%`
  } else if (doc.status === 'processing') {
    const { extracted_pages, total_pages, remote_state } = doc.progress
    percent = total_pages ? Math.round(((extracted_pages ?? 0) / total_pages) * 100) : 0
    detail = total_pages
      ? `Página ${extracted_pages ?? 0} de ${total_pages}`
      : `MinerU: ${REMOTE_LABELS[remote_state ?? ''] ?? remote_state ?? 'iniciando'}`
  } else if (doc.status === 'done') {
    percent = 100
  }
  const indeterminate = doc && !failed && doc.status !== 'done' && percent === 0

  return (
    <section className="card" aria-live="polite">
      <h2>
        Progreso{doc && <span className="muted"> · {doc.filename}</span>}
      </h2>
      <ol className="steps">
        {STEPS.map((step, i) => (
          <li key={step} className={i < index ? 'complete' : i === index ? 'active' : ''}>
            {STEP_LABELS[step]}
          </li>
        ))}
      </ol>
      {!failed && (
        <div className={`bar${indeterminate ? ' indeterminate' : ''}`}>
          <div style={{ width: `${indeterminate ? 30 : percent}%` }} />
        </div>
      )}
      <p className={failed ? 'error' : 'muted'}>
        {failed ? `${STATUS_LABELS.failed}: ${doc?.error}` : detail || (doc && STATUS_LABELS[doc.status])}
      </p>
    </section>
  )
}
