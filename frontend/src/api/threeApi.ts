import { mande } from 'mande'
import type { ScanMetadata } from '@/model'

// Change this to exactly '/api'
const api = mande('/api') 

export async function fetchScanMetadata(scanId: string): Promise<ScanMetadata> {
  return await api.get<ScanMetadata>(`/scan/${scanId}`)
}

export async function uploadScan(name: string, file: File) {
  const formData = new FormData()
  formData.append('name', name)
  formData.append('file', file)

  // We use native fetch here because mande handles JSON by default, 
  // but we need to send FormData for files.
  const response = await fetch('/api/upload', {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Upload failed')
  }

  return await response.json()
}