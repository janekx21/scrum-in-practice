<script setup lang="ts">
import { useRoute } from 'vue-router'
import MultiModelScene from '@/components/MultiModelScene.vue'

const route = useRoute()
const id = route.params['id']
</script>

<template>
  <MultiModelScene :model_paths="['/api/scan/' + id + '/full.glb']"/>
</template>

