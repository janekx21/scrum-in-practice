import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ScanMetadata } from '@/model'
import { fetchScanMetadata } from '@/api/threeApi'

export const useThreeStore = defineStore('threeData', () => {
  const scanInfo = ref<ScanMetadata | null>(null)
  const isLoading = ref(false)

  async function loadScan(id: string) {
    isLoading.value = true
    try {
      scanInfo.value = await fetchScanMetadata(id)
    } catch (error) {
      console.error("Failed to fetch scan metadata:", error)
    } finally {
      isLoading.value = false
    }
  }

  return { scanInfo, isLoading, loadScan }
})