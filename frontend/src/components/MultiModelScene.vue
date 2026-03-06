<script setup lang="ts">
import { TresCanvas } from '@tresjs/core'
import { KeyboardControls, OrbitControls } from '@tresjs/cientos'
import GltfModel from '@/components/GLTFModel.vue'
import { computed } from 'vue'

const props = defineProps<{
  model_paths: string[]
  model_bytes: ArrayBuffer[]
  path_points?: number[][]
  path_orientation?: number[]
}>()

// Flatten points for the TresLine geometry
const flattenedPoints = computed(() => {
  if (!props.path_points || props.path_points.length < 2) return new Float32Array(0)
  return new Float32Array(props.path_points.flat())
})

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

      <TresGridHelper :args="[500, 500, '#444', '#222']" :position="[0, -2, 0]" />

      <GltfModel v-for="path of model_paths" :key="path" :path="path" />
      <GltfModel v-for="(data,i) of model_bytes" :key="i" :raw_data="data" />

      <!-- Path Visualization (Red Line and Dot) -->
      <TresGroup :rotation="[-Math.PI / 2, 0, 0]">
        <TresLine v-if="flattenedPoints.length > 0" :key="flattenedPoints.length">
          <TresBufferGeometry>
            <TresBufferAttribute
              attach="attributes-position"
              :count="flattenedPoints.length / 3"
              :array="flattenedPoints"
              :item-size="3"
            />
          </TresBufferGeometry>
          <TresLineBasicMaterial color="#ff0000" :linewidth="5" :depth-test="true" />
        </TresLine>

        <TresMesh 
          v-if="props.path_points && props.path_points.length > 0" 
          :position="(props.path_points[props.path_points.length - 1]as any)"
        >
          <TresSphereGeometry :args="[0.05, 16, 16]" />
          <TresMeshBasicMaterial color="#ff0000" :depth-test="true" />

          <TresMesh :quaternion="props.path_orientation">
            <TresConeGeometry :args="[0.1, 0.3, 16]" :rotate-z="Math.PI / 2" :translate="[0.2,0,0]" />
            <TresMeshBasicMaterial color="#00b020" :depth-test="true" />
          </TresMesh>

        </TresMesh>
      </TresGroup>
    </TresCanvas>
  </div>
</template>