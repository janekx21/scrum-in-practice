import { mande } from 'mande'
import type { ScanMetadata } from '@/model'

const api = mande('/api')

export async function fetchScanMetadata(scanId: string): Promise<ScanMetadata> {
  // This gets the JSON that contains the URL to the binary file
  return await api.get<ScanMetadata>(`/scan/${scanId}`)
}