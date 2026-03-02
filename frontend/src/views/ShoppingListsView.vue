<script setup lang="ts">
import { useShoppingListStore } from '@/stores/shoppingList.ts'
import { onMounted } from 'vue'

const store = useShoppingListStore()

onMounted(() => store.fetchAllItems())

</script>

<template>
    <main class="container">
    <h1 class="mb-4">Shopping List</h1>

    <button class="btn btn-outline-primary mb-2 w-100" @click="store.addEmptyItem()">
      Add Shopping List
    </button>

    <div class="list-group list-group-flush">
      <div class="list-group-item" v-for="shoppingList in store.items" :key="shoppingList.id">
        <div class="input-group">
          <a class="btn btn-outline-primary" :href="'/shopping-list/' + shoppingList.id"> Open </a>
          <input
            type="text"
            class="form-control"
            placeholder="Shopping List Name"
            v-model="shoppingList.name"
            @change="store.syncToServer(shoppingList.id)"
          />
          <button
            class="btn btn-outline-danger"
            type="button"
            @click="store.removeItem(shoppingList.id)"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </main>
</template>
