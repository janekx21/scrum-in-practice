<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { uploadScan, fetchAllScans } from '@/api/threeApi'
import type { ScanRecord } from '@/model'

const fileInput = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)
const previousScans = ref<ScanRecord[]>([])

// Function to fetch data from backend - EXACTLY AS PER YOUR WORKING CODE
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

  const file = target.files[0]!
  if (!file.name.endsWith('.zip')) {
    alert('Please upload only .zip files.')
    return
  }

  const name = prompt("Please enter the Building/Incident name:")
  if (!name) {
    alert("Name is mandatory for upload.")
    return
  }

  try {
    isUploading.value = true
    await uploadScan(name, file)
    alert("Upload successful!")
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
  <div class="home-wrapper">
    <!-- Hero Section -->
    <header class="hero-section text-center text-white p-5">
      <div class="container py-4">
        <div class="badge rounded-pill bg-danger mb-3 px-3 py-2 fw-bold tracking-wider">EMERGENCY RESPONSE SYSTEM</div>
        <h1 class="display-1 fw-black tracking-tight mb-2">EVOK</h1>
        <p class="lead opacity-75 mx-auto mb-5" style="max-width: 650px;">
          High-precision 3D Building Scanning & Real-time Visualization for Guided Medical Assistance and Rescue Operations.
        </p>

        <div class="d-flex justify-content-center gap-3 flex-wrap">
          <!-- Preserved your exact RouterLink path -->
          <RouterLink to="/livestreaming" class="btn btn-warning btn-lg px-4 py-3 fw-bold shadow-sm d-flex align-items-center">
            <span class="status-dot me-2"></span> Connect to Live Stream
          </RouterLink>

          <!-- Preserved your exact upload button logic -->
          <button @click="triggerUpload" class="btn btn-outline-light btn-lg px-4 py-3 fw-bold border-2" :disabled="isUploading">
            <span v-if="!isUploading">↑ Upload New ZIP</span>
            <span v-else>Processing...</span>
          </button>
          
          <input type="file" ref="fileInput" class="d-none" accept=".zip" @change="handleFileChange" />
        </div>
      </div>
    </header>

    <!-- Content Section -->
    <main class="container mt-n5 position-relative">
      <div class="row justify-content-center">
        <div class="col-lg-10">
          <div class="card border-0 shadow-lg rounded-4 overflow-hidden">
            <div class="card-header bg-white border-0 py-4 px-4 d-flex justify-content-between align-items-center">
              <div>
                <h4 class="mb-0 fw-bold text-dark">EVOK Scan History</h4>
                <small class="text-muted small text-uppercase fw-bold tracking-wider">Tactical Incident Records</small>
              </div>
              <button @click="loadScans" class="btn btn-light btn-sm rounded-circle shadow-sm" title="Refresh List">
                ↻
              </button>
            </div>

            <div class="card-body p-0">
              <div class="table-responsive">
                <table class="table table-hover mb-0">
                  <thead class="bg-light">
                    <tr>
                      <th class="ps-4 py-3 text-uppercase small fw-bold text-muted">Building / Incident Name</th>
                      <th class="py-3 text-uppercase small fw-bold text-muted">Registration Time</th>
                      <th class="py-3 text-uppercase small fw-bold text-muted text-end pe-4">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="scan in previousScans" :key="scan.id" class="align-middle">
                      <td class="ps-4 py-3">
                        <div class="d-flex align-items-center">
                          <div class="scan-pill me-3" style="background: #f1f5f9; font-size: 1.1rem;">🏢</div>
                          <span class="fw-bold text-dark">{{ scan.name }}</span>
                        </div>
                      </td>
                      <td class="py-3 text-muted">
                        {{ scan.upload_datetime }}
                      </td>
                      <td class="text-end pe-4 py-3">
                        <!-- Preserved your exact <a> tag based navigation -->
                        <a class="btn btn-dark btn-sm rounded-3 px-4 fw-bold shadow-sm transition-all" :href="'/fps/' + scan.id">
                          Initialize 3D View
                        </a>
                      </td>
                    </tr>
                    
                    <!-- Empty State -->
                    <tr v-if="previousScans.length === 0">
                      <td colspan="3" class="text-center py-5">
                        <div class="opacity-25 mb-2 h2">📂</div>
                        <p class="text-muted mb-0">No scans uploaded yet. Start by uploading a building ZIP.</p>
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

    <footer class="text-center py-5 text-muted small">
      <p>© 2026 EVOK Medical Support Systems | Tactical Guidance Interface</p>
    </footer>
  </div>
</template>

<style scoped>
.home-wrapper {
  background-color: #f1f5f9;
  min-height: 100vh;
}

.hero-section {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  padding-bottom: 110px !important;
  border-bottom: 4px solid #facc15;
}

.fw-black {
  font-weight: 900;
  letter-spacing: -2px;
}

.mt-n5 {
  margin-top: -70px !important;
  z-index: 10;
}

.scan-pill {
  background: #e2e8f0;
  color: #475569;
  font-size: 0.65rem;
  font-weight: 800;
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid #cbd5e1;
}

.tracking-wider {
  letter-spacing: 0.1em;
}

.status-dot {
  width: 8px;
  height: 8px;
  background-color: #dc2626;
  border-radius: 50%;
  display: inline-block;
  animation: pulse-red 2s infinite;
}

@keyframes pulse-red {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7); }
  70% { transform: scale(1.1); box-shadow: 0 0 0 6px rgba(220, 38, 38, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
}

.btn-warning {
  background-color: #facc15;
  border: none;
  color: #000;
}

.btn-warning:hover {
  background-color: #eab308;
  transform: translateY(-1px);
}

.btn-dark {
  background-color: #0f172a;
}

.transition-all {
  transition: all 0.2s ease;
}

.card {
  border: 1px solid rgba(0,0,0,0.05);
}
</style>