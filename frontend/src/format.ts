export const formatBytes = (bytes: number) =>
  bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(0)} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`

export const formatDate = (iso: string) =>
  new Date(iso).toLocaleString('es-MX', { dateStyle: 'short', timeStyle: 'short' })

export const STATUS_LABELS: Record<string, string> = {
  queued: 'En cola',
  uploading: 'Enviando a MinerU',
  processing: 'Extrayendo',
  done: 'Listo',
  failed: 'Error',
}
