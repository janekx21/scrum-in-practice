<script setup lang="ts">
import { TresCanvas } from '@tresjs/core'
import FirstExperience from '../components/FirstExperience.vue'
    // window-size
</script>

<template>
  <div style="width: 100%; height: 800px;">
    <TresCanvas
      clear-color="#82DBC5"
      shadows
      alpha
      window-size
      power-preference="high-performance"
      preserve-drawing-buffer
      physically-correct-lights
      >

      <FirstExperience />
    </TresCanvas>
  </div>
</template>
