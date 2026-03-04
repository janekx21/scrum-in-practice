<template>
  <div class="container py-5 text-center">
    <div class="card shadow-lg p-5">
      <h2 class="display-5 fw-bold text-danger mb-4">EVOK Live Stream</h2>
      <div class="ratio ratio-16x9 bg-dark d-flex align-items-center justify-content-center mb-4">
        <span class="text-white">Connecting to EVOK Camera Feed...</span>
      </div>
      <div class="d-flex justify-content-center gap-3">
        <RouterLink to="/" class="btn btn-outline-secondary">Back to Home Page</RouterLink>
        <button class="btn btn-danger" @click="toggleStream">Start/Stop Stream</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const toggleStream = () => {
  alert("Attempting to connect to EVOK hardware...")
}
</script>