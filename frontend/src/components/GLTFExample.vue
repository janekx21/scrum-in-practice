<script setup lang="ts">
import { useLoader } from '@tresjs/core'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js'
import { watch } from 'vue'
import * as THREE from 'three'

const props = defineProps<{
  path: string
}>()

const dracoLoader = new DRACOLoader()
dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/')

const { state: model, error } = useLoader(
  GLTFLoader,
  props.path, // Use the prop passed from the view
  {
    extensions: (loader) => {
      if (loader instanceof GLTFLoader) {
        loader.setDRACOLoader(dracoLoader)
      }
    },
  },
)


watch(model, (newModel) => {
  if (newModel) {
    newModel.scene.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        const oldMat = child.material

        // Fix the material properties
        child.material = child.material.clone()
        child.material.metalness = 0
        child.material.roughness = 1
        child.material.envMapIntensity = null
      }
    })
  }
})

watch(error, (e) => {
  if (e) console.error("3D Model Loading Error:", e)
})
</script>

<template>
  <!-- Render the entire scene from the file, not just one node -->
  <primitive
    v-if="model"
    :object="model.scene"
    :rotation="[-Math.PI / 2, 0, 0]"
  >
  </primitive>
</template>
