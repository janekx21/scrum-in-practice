<script setup lang="ts">
import { RouterLink } from 'vue-router'
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
          <a href="https://github.com" target="_blank" class="btn btn-outline-secondary btn-lg px-4">
            Documentation
          </a>
        </div>
      </div>
    </div>
  </main>
</template>