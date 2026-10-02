import type { DocumentStatus, ExtractionResult, Health } from '../types'

const BASE = import.meta.env.VITE_API_URL ?? ''

export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

function toApiError(status: number, body: unknown): ApiError {
  const error = (body as { error?: { code?: string; message?: string } } | null)?.error
  return new ApiError(status, error?.code ?? 'http_error', error?.message ?? `Error HTTP ${status}`)
}

async function request<T>(path: string): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${BASE}${path}`)
  } catch {
    throw new ApiError(0, 'network', 'No se pudo conectar con el backend. ¿Está corriendo en el puerto 8000?')
  }
  const body = await response.json().catch(() => null)
  if (!response.ok) throw toApiError(response.status, body)
  return body as T
}

export const getHealth = () => request<Health>('/api/health')
export const listDocuments = () => request<DocumentStatus[]>('/api/documents')
export const getDocument = (id: string) => request<DocumentStatus>(`/api/documents/${id}`)
export const getResult = (id: string) => request<ExtractionResult>(`/api/documents/${id}/result`)

/** Sube el PDF con XMLHttpRequest para poder reportar el progreso de la subida. */
export function uploadDocument(file: File, onProgress: (fraction: number) => void): Promise<DocumentStatus> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${BASE}/api/documents`)
    xhr.responseType = 'json'
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress(event.loaded / event.total)
    }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve(xhr.response as DocumentStatus)
      else reject(toApiError(xhr.status, xhr.response))
    }
    xhr.onerror = () =>
      reject(new ApiError(0, 'network', 'No se pudo conectar con el backend. ¿Está corriendo en el puerto 8000?'))
    const form = new FormData()
    form.append('file', file)
    xhr.send(form)
  })
}
