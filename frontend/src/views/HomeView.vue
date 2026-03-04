<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { uploadScan, fetchAllScans } from '@/api/threeApi'
import type { ScanRecord } from '@/model'

const fileInput = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)
const previousScans = ref<ScanRecord[]>([])

// Function to fetch data from backend
const loadScans = async () => {
  try {
    previousScans.value = await fetchAllScans()
  } catch (err) {
    console.error("Failed to load scans:", err)
  }
}

// Fetch scans when component mounts
onMounted(() => {
  loadScans()
})

const triggerUpload = () => {
  fileInput.value?.click()
}

const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return

  const file = target.files[0]
  if (!file.name.endsWith('.zip')) {
    alert('Please upload only .zip files.')
    return
  }

  const name = prompt("Please enter a name for this scan:")
  if (!name) {
    alert("Name is mandatory for upload.")
    return
  }

  try {
    isUploading.value = true
    await uploadScan(name, file)
    alert("Upload successful!")
    
    // DYNAMIC UPDATE: Re-fetch the list after successful upload
    await loadScans() 
    
  } catch (err: any) {
    alert("Error: " + err.message)
  } finally {
    isUploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}
</script>

<template>
  <main class="container py-5">
    <!-- Hero Section -->
    <div class="row align-items-center justify-content-center mb-5">
      <div class="col-md-8 text-center">
        <h1 class="display-3 fw-bold mb-3">EVOK</h1>
        <p class="lead mb-4 text-muted">
          High-precision 3D Building Scanner & Real-time Visualization.
        </p>
        
        <div class="d-grid gap-3 d-sm-flex justify-content-sm-center">
          <RouterLink to="/livestreaming" class="btn btn-warning btn-lg px-4 fw-bold">
            Connect to Live Stream
          </RouterLink>
          
          <button @click="triggerUpload" class="btn btn-outline-success btn-lg px-4" :disabled="isUploading">
            {{ isUploading ? 'Uploading...' : 'Upload New ZIP' }}
          </button>

          <input type="file" ref="fileInput" style="display: none" accept=".zip" @change="handleFileChange" />
        </div>
      </div>
    </div>

    <!-- PREVIOUS SCANS LIST -->
    <div class="row justify-content-center">
      <div class="col-md-10">
        <div class="card shadow-sm">
          <div class="card-header bg-white">
            <h5 class="mb-0">EVOK Scan History</h5>
          </div>
          <div class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-hover mb-0">
                <thead class="table-light">
                  <tr>
                    <th>Name</th>
                    <th>Date</th>
                    <th>Timestamp</th>
                    <th>Filename</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="scan in previousScans" :key="scan.id">
                    <td class="fw-bold">{{ scan.name }}</td>
                    <td>{{ scan.upload_date }}</td>
                    <td>{{ scan.upload_timestamp }}</td>
                    <td class="text-muted small">{{ scan.zip_file }}</td>
                  </tr>
                  <tr v-if="previousScans.length === 0">
                    <td colspan="4" class="text-center py-4 text-muted">
                      No scans uploaded yet.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>