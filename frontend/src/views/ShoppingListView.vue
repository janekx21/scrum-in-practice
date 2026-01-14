<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { newShoppingListItem, useShoppingListStore } from '@/stores/shoppingList'
import { createShoppingList, updateShoppingList } from '@/api/shoppingListApi'

const store = useShoppingListStore()
const route = useRoute()
const router = useRouter()
const id = typeof route.params.id === 'string' ? route.params.id : ""

onMounted(() => store.fetchSingleItem(id))

const shoppingList = computed(() => {
  // store.getById(id) in your project is a computed; take its value
  return store.getById(id).value
})

</script>

<template>
  <main class="container" v-if="shoppingList">
    <h1 class="mb-4">{{ shoppingList.name }}</h1>

    <!-- Add Item first -->
    <button
      class="btn btn-outline-primary mb-3 w-100"
      @click="shoppingList.items.push(newShoppingListItem())"
    >
      Add Item
    </button>

    <!-- Items list -->
    <div class="list-group list-group-flush mb-3">
      <div class="list-group-item" v-for="(item, i) in shoppingList.items" :key="i">
        <div class="input-group">
          <div class="input-group-text">
            <input class="form-check-input mt-0" type="checkbox" v-model="item.done" @change="store.syncToServer(id)" />
          </div>

          <input type="text" class="form-control" placeholder="Item" v-model="item.text" @change="store.syncToServer(id)" />

          <button class="btn btn-outline-danger" type="button" @click="shoppingList.items.splice(i, 1); store.syncToServer(id)">
            Delete
          </button>
        </div>
      </div>
    </div>

  </main>

  <main class="container" v-else>
    <div class="text-muted">No list found in local state for this URL.</div>
  </main>
</template>
