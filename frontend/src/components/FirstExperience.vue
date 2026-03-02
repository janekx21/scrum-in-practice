<script setup lang="ts">
import { useLoop } from '@tresjs/core'
import { ref } from 'vue'
import { OrbitControls, useTweakPane } from '@tresjs/cientos';
import GLTFExample from './GLTFExample.vue'

//// Reference to our donut mesh for animation
//const donutRef = ref()
//
//// Animation loop
//const { onBeforeRender } = useLoop()
//
//onBeforeRender(({ elapsed }) => {
//  if (donutRef.value) {
//    // Rotate the donut on both X and Y axes
//    donutRef.value.rotation.x = elapsed * 0.5
//    donutRef.value.rotation.y = elapsed * 0.3
//  }
//})
</script>

<template>

  <OrbitControls />

  <!-- Camera Setup -->
    <TresPerspectiveCamera
      :position="[1, 2, 5]"
      :fov="45"
      :aspect="1"
      :near="0.1"
      :far="1000"
    />

  <TresScene>
    <TresDirectionalLight :position="[0, 2, 4]" :intensity="2" cast-shadow />

  <!-- The Donut -->
    <TresMesh ref="donutRef" :position="[0, 2, 0]">
      <TresTorusGeometry :args="[1, 0.4, 16, 32]" />
      <!-- <TresMeshBasicMaterial color="#ff6b35" /> -->
    </TresMesh>

    <GLTFExample/>
  </TresScene>

</template>
