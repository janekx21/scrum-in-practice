<template>
  <div class="fps-container">
    <div v-if="store.isLoading" class="loader">Processing 3D Scan...</div>
    <!-- The team member implementing three.js will put their Canvas component here -->
    <div id="three-canvas-container" v-else-if="store.currentScan">
       <!-- Data is now ready in store.currentScan -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useThreeStore } from '@/stores/useThreeStore'

const store = useThreeStore()

onMounted(() => {
  // Replace 'building_scan_01' with your actual filename
  store.loadScan('building_scan_01')
})
</script>