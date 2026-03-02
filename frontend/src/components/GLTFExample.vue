<script setup lang="ts">
import { useGraph, useLoader } from '@tresjs/core'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js'
import { computed } from 'vue'

// Setup DRACO loader for compressed GLTFs
const dracoLoader = new DRACOLoader()
dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/')

// Load a GLTF model
const { state: model, isLoading, error } = useLoader(
  GLTFLoader,
  '/blender-cube.glb',
  {
    extensions: (loader) => {
      if (loader instanceof GLTFLoader) {
        loader.setDRACOLoader(dracoLoader)
      }
    },
  },
)

// Extract the scene and graph
const scene = computed(() => model.value?.scene)
const graph = useGraph(scene)

const nodes = computed(() => graph.value?.nodes)
</script>

<template>
  <!-- Render the Cube node if it exists -->
  <primitive
    v-if="nodes?.BlenderCube"
    :object="nodes?.BlenderCube"
  />
</template>
