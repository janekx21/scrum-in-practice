<script setup lang="ts">
import { onMounted } from 'vue'
import { useThreeStore } from '@/stores/useThreeStore'
import { TresCanvas } from '@tresjs/core'
import { KeyboardControls } from '@tresjs/cientos'
import GLTFExample from '@/components/GLTFExample.vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const id = route.params['id']
const store = useThreeStore()
// On mount, load the 'sample_building' scan
onMounted(() => store.loadScan(id))
</script>

<template>
  <div class="fps-container" style="height: calc(100vh - 56px); width: 100%; background: #000;">
    <TresCanvas clear-color="#111" shadows alpha>
      <!-- Move camera further back [40, 40, 40] to see large buildings -->
      <TresPerspectiveCamera :position="[0, 0, 0]" :look-at="[10, 0, 0]" />
      <!-- <OrbitControls make-default /> -->
      <KeyboardControls />

      <!-- Brighter lights for building scans -->
      <TresAmbientLight :intensity="2.0" />
      <TresDirectionalLight :position="[20, 40, 20]" :intensity="3.0" cast-shadow />

      <Suspense>
        <!-- Correctly pass the store's modelUrl to the component -->
        <GLTFExample v-if="store.scanInfo" :path="'/api/scan/' + id + '/full.glb'" />
      </Suspense>

      <TresGridHelper :args="[500, 500, '#444', '#222']" />
    </TresCanvas>
  </div>
</template>

