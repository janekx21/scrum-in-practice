import { mande } from 'mande'
import type { ScanMetadata } from '@/model'

// Change this to exactly '/api'
const api = mande('/api') 

export async function fetchScanMetadata(scanId: string): Promise<ScanMetadata> {
  return await api.get<ScanMetadata>(`/scan/${scanId}`)
}