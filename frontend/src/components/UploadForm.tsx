import { useRef, useState, type DragEvent } from 'react'
import { formatBytes } from '../format'

const MAX_MB = 50

interface Props {
  disabled: boolean
  onSubmit: (file: File) => void
}

function validate(file: File): string | null {
  if (!file.name.toLowerCase().endsWith('.pdf')) return 'Solo se aceptan archivos .pdf.'
  if (file.size === 0) return 'El archivo está vacío.'
  if (file.size > MAX_MB * 1024 * 1024) return `El archivo supera ${MAX_MB} MB.`
  return null
}

export function UploadForm({ disabled, onSubmit }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)

  const choose = (candidate: File | undefined) => {
    if (!candidate) return
    const problem = validate(candidate)
    setError(problem)
    setFile(problem ? null : candidate)
  }

  const onDrop = (event: DragEvent) => {
    event.preventDefault()
    setDragging(false)
    if (!disabled) choose(event.dataTransfer.files[0])
  }

  return (
    <section className="card">
      <h2>Subir PDF</h2>
      <div
        className={`dropzone${dragging ? ' dragging' : ''}${disabled ? ' disabled' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && !disabled && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          hidden
          onChange={(e) => {
            choose(e.target.files?.[0])
            e.target.value = ''
          }}
        />
        {file ? (
          <p>
            <strong>{file.name}</strong>
            <span className="muted"> · {formatBytes(file.size)}</span>
          </p>
        ) : (
          <p>
            Arrastra un PDF aquí o <u>haz clic para elegirlo</u>
            <br />
            <span className="muted">Máximo {MAX_MB} MB y 200 páginas</span>
          </p>
        )}
      </div>
      {error && <p className="error">{error}</p>}
      <button
        className="primary"
        disabled={!file || disabled}
        onClick={() => {
          if (file) {
            onSubmit(file)
            setFile(null)
          }
        }}
      >
        Extraer contenido
      </button>
    </section>
  )
}
