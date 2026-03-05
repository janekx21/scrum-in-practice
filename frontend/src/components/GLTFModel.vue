<script setup lang="ts">
import { type GLTF, GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js'
import { watch, shallowRef, onMounted } from 'vue'
import * as THREE from 'three'

const props = defineProps<{
  path?: string
  raw_data?: ArrayBuffer
}>()

const dracoLoader = new DRACOLoader()
dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/')

const model = shallowRef<GLTF>()
onMounted(() => {
if (props.raw_data) {
  const loader = new GLTFLoader()
  loader.setDRACOLoader(dracoLoader)
  loader.parse(props.raw_data, 'frame', (m) => {
    model.value = m
  })
} else {
  const loader = new GLTFLoader()
  loader.setDRACOLoader(dracoLoader)
  loader.load(props.path!, (m) => {
    model.value = m
  })
}
  
})

watch(model, (newModel) => {
  if (newModel) {
    newModel.scene.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        // Fix the material properties
        child.material = child.material.clone()
        child.material.metalness = 0
        child.material.roughness = 1
        child.material.envMapIntensity = null
      }
    })
  }
})


//watch(error, (e) => {
//  if (e) console.error('3D Model Loading Error:', e)
//})
</script>

<template>
  <!-- Render the entire scene from the file, not just one node -->
  <primitive v-if="model" :object="model.scene" :rotation="[-Math.PI / 2, 0, 0]"> </primitive>
</template>
