<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <header>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
      <div class="container">
        <RouterLink class="navbar-brand" to="/">EVOK</RouterLink>
        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarNav"
        >
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav ms-auto">
            <li class="nav-item">
              <RouterLink class="nav-link" to="/">Home</RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink class="nav-link btn btn-primary text-white ms-lg-2" to="/fps">
                Open 3D Viewer
              </RouterLink>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  </header>
  
  <RouterView />
</template>

<style scoped></style>
