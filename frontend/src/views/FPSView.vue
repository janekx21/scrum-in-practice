<template>
  <div class="fps-container" style="height: calc(100vh - 56px); width: 100%; background: #000;">
    <TresCanvas clear-color="#111" shadows alpha>
      <!-- The camera starts here, but GLTFExample will move it to the right spot -->
      <TresPerspectiveCamera :position="[10, 10, 10]" />
      <OrbitControls make-default />

      <TresAmbientLight :intensity="2" />
      <TresDirectionalLight :position="[10, 10, 10]" :intensity="2" />

      <Suspense>
        <GLTFExample v-if="store.scanInfo" :path="store.scanInfo.modelUrl" />
      </Suspense>
      
      <TresGridHelper :args="[200, 200, '#444', '#222']" />
    </TresCanvas>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useThreeStore } from '@/stores/useThreeStore'
import { TresCanvas } from '@tresjs/core'
import { OrbitControls } from '@tresjs/cientos'
import GLTFExample from '@/components/GLTFExample.vue'

const store = useThreeStore()
onMounted(() => store.loadScan('sample_building'))
</script>