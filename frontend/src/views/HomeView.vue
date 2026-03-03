<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { uploadScan } from '@/api/threeApi'

const fileInput = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)

const triggerUpload = () => {
  fileInput.value?.click()
}

const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return

  const file = target.files[0]
  
  // Validation: Only ZIP
  if (!file.name.endsWith('.zip')) {
    alert('Please upload only .zip files.')
    return
  }

  // Requirement: Name is mandatory
  const name = prompt("Please enter a name for this scan:")
  if (!name) {
    alert("Name is mandatory for upload.")
    return
  }

  try {
    isUploading.value = true
    await uploadScan(name, file)
    alert("Upload successful!")
  } catch (err: any) {
    alert("Error: " + err.message)
  } finally {
    isUploading.value = false
    if (fileInput.value) fileInput.value.value = '' // Reset input
  }
}
</script>

<template>
  <main class="container">
    <div class="row align-items-center justify-content-center" style="min-height: 70vh;">
      <div class="col-md-8 text-center">
        <h1 class="display-3 fw-bold mb-3">3D Building Scanner</h1>
        <p class="lead mb-5 text-muted">
          A high-precision 3D visualization tool for building scans. 
          View, rotate, and interact with complex architectural models in real-time.
        </p>
        
        <div class="d-grid gap-3 d-sm-flex justify-content-sm-center">
          <RouterLink to="/fps" class="btn btn-primary btn-lg px-5 gap-3">
            Start Viewing
          </RouterLink>
          <button 
            @click="triggerUpload" 
            class="btn btn-outline-secondary btn-lg px-4"
            :disabled="isUploading"
          >
            {{ isUploading ? 'Uploading...' : 'Upload Scan (.zip)' }}
          </button>

          <!-- HIDDEN FILE INPUT -->
          <input 
            type="file" 
            ref="fileInput" 
            style="display: none" 
            accept=".zip" 
            @change="handleFileChange"
          />
        </div>
      </div>
    </div>
  </main>
</template>