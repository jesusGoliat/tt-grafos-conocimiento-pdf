import type { DocumentStatus } from '../types'
import { STATUS_LABELS, formatBytes, formatDate } from '../format'

interface Props {
  documents: DocumentStatus[]
  selectedId: string | null
  onSelect: (id: string) => void
}

export function DocumentList({ documents, selectedId, onSelect }: Props) {
  return (
    <section className="card">
      <h2>Documentos</h2>
      {documents.length === 0 ? (
        <p className="muted">Aún no hay documentos procesados.</p>
      ) : (
        <ul className="doc-list">
          {documents.map((doc) => (
            <li key={doc.id}>
              <button className={doc.id === selectedId ? 'selected' : ''} onClick={() => onSelect(doc.id)}>
                <span className="doc-name">{doc.filename}</span>
                <span className="muted">
                  {doc.pages} pág. · {formatBytes(doc.size_bytes)} · {formatDate(doc.created_at)}
                </span>
                <span className={`badge ${doc.status}`}>{STATUS_LABELS[doc.status]}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
