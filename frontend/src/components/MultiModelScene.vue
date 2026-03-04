<script setup lang="ts">
import { TresCanvas } from '@tresjs/core'
import { KeyboardControls, OrbitControls } from '@tresjs/cientos'
import GltfModel from '@/components/GLTFModel.vue'

const { model_paths, model_bytes } = defineProps<{
  model_paths: string[]
  model_bytes: ArrayBuffer[]
}>()

function isMobile(): boolean {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
}
</script>

<template>
  <div class="fps-container" style="height: calc(100vh - 56px); width: 100%; background: #000">
    <TresCanvas clear-color="#c5c5c5" alpha>
      <!-- Move camera further back [40, 40, 40] to see large buildings -->
      <TresPerspectiveCamera :position="[0, 0, 0]" :look-at="[10, 0, 0]" />
      <OrbitControls v-if="isMobile()" make-default />
      <KeyboardControls v-else />

      <!-- Brighter lights for building scans -->
      <TresAmbientLight :intensity="1.0" />
      <TresDirectionalLight :position="[20, 40, 20]" :intensity="3.0" cast-shadow />

      <TresGridHelper :args="[500, 500, '#444', '#222']" />

      <GltfModel v-for="path of model_paths" :key="path" :path="path" />
      <GltfModel v-for="(data,i) of model_bytes" :key="i" :raw_data="data" />
    </TresCanvas>
  </div>
</template>
