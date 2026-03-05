<script setup lang="ts">
import { useWebSocket } from '@vueuse/core'
import { onMounted, ref, watch } from 'vue'
import MultiModelScene from '@/components/MultiModelScene.vue'


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

</script>
<template>
  <div class="container py-5 text-center">
    {{ status }}
    {{ data }}
    <div class="card shadow-lg p-5">
      <h2 class="display-5 fw-bold text-danger mb-4">EVOK Live Stream</h2>
      <div class="ratio ratio-16x9 bg-dark d-flex align-items-center justify-content-center mb-4">
        <span class="text-white">Connecting to EVOK Camera Feed...</span>
         <MultiModelScene :model_bytes="model_bytes" :model_paths="[]"/>
      </div>
      <div class="d-flex justify-content-center gap-3">
        <RouterLink to="/" class="btn btn-outline-secondary">Back to Home Page</RouterLink>
        <button class="btn btn-danger" @click="toggleStream">Start/Stop Stream</button>
       </div>
    </div>
  </div>
</template>

