<script setup lang="ts">
import { useLoader } from '@tresjs/core'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js'
import { watch } from 'vue'

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

watch(error, (e) => {
  if (e) console.error("3D Model Loading Error:", e)
})
</script>

<template>
  <!-- Render the entire scene from the file, not just one node -->
  <primitive 
    v-if="model" 
    :object="model.scene" 
  />
</template>