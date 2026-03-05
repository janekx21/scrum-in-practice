<script setup lang="ts">
import { useRoute } from 'vue-router'
import MultiModelScene from '@/components/MultiModelScene.vue'
import { ref } from 'vue'

const route = useRoute()
const id = route.params['id']

const model_bytes = ref<ArrayBuffer[]>([])

// Loads the data from bytes not path
function loadModelData() {
  fetch('/api/scan/' + id + '/full.glb').then((result) => {
    result.arrayBuffer().then((buff) => {
      model_bytes.value.push(buff)
    })
  })
}

loadModelData()
</script>

<template>
  <MultiModelScene :model_paths="[]" :model_bytes="model_bytes" />
</template>
