<script setup lang="ts">
import { useWebSocket } from '@vueuse/core'
import { onMounted, ref, watch } from 'vue'
import MultiModelScene from '@/components/MultiModelScene.vue'
import { fetchAllStrams } from '@/api/threeApi'


const toggleStream = () => {
  alert("Attempting to connect to EVOK hardware...")
}

const { status, data, send, open, close, ws } = useWebSocket(
  `ws:/localhost:8765/ws`, {
    autoReconnect: true,
    
  }
)
onMounted(() => open())
watch(status, () => {
  console.log(status)
})
watch(data, () => {
  if (data.value instanceof Blob) {
    console.log("here a glb")

    data.value.arrayBuffer().then((b) => {
      model_bytes.value.push(b)
    })
  }
})

const model_bytes = ref<ArrayBuffer[]>([])
const selectedChannel = ref<string>()
const allStreams = ref<string>([])

function connectToStream(channel: string) {

}

onMounted(() => {
   fetchAllStrams().then((s) => {
    allStreams.value  = s
  })
})

</script>
<template>

<div class="livestream-container bg-black position-relative" style="height: calc(100vh - 56px);">
    
    <!-- UI Overlay Controls -->
    <div class="position-absolute top-0 start-0 m-3 z-3" style="width: 250px;">
      <div class="card bg-dark text-white border-secondary shadow">
        <div class="card-body">
          <h5 class="text-danger fw-bold mb-3">● EVOK LIVE</h5>
          
          <div v-if="!selectedChannel">
            <div class="list-group">
              <button 
                v-for="ch in allStreams" 
                :key="ch" 
                @click="connectToStream(ch)"
                class="list-group-item list-group-item-action list-group-item-dark small"
              >
                Connect to {{ ch }}
              </button>
            </div>
          </div>

          <div v-else>
            <p class="small text-success mb-1">Active: {{ selectedChannel }}</p>
            <p class="extra-small text-muted mb-3">Frame ID: {{ frameTrigger }}</p>
            <button @click="selectedChannel = null" class="btn btn-outline-light btn-sm w-100">
              Disconnect
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 3D Viewport -->
    <div v-if="selectedChannel" class="w-100 h-100">
      <MultiModelScene :model_bytes="model_bytes" :model_paths="[]"/>
    </div>
    
    <div v-else class="w-100 h-100 d-flex align-items-center justify-content-center text-secondary">
      <p>Select an EVOK channel to start livestreaming</p>
    </div>
  </div>
</template>

<style scoped>
.z-3 { z-index: 1050; }
.extra-small { font-size: 0.75rem; }
</style>