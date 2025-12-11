<script setup lang="ts">
// import TheWelcome from '../components/TheWelcome.vue'

import {newShoppingListItem, useShoppingListStore} from '@/stores/shoppingList.ts'
import {useRoute} from 'vue-router'
import {computed} from 'vue'

const store = useShoppingListStore()

const id = useRoute().params.id
const shoppingList = typeof id == 'string' ? store.getById(id) : computed(() => undefined)
</script>

<template>
  <main class="container" v-if="shoppingList">
    <h1 class="mb-4">{{ shoppingList.name }}</h1>
    <button
      class="btn btn-outline-primary mb-2 w-100"
      @click="shoppingList.items.push(newShoppingListItem())"
    >
      Add Item
    </button>

    <div class="list-group list-group-flush">
      <div class="list-group-item" v-for="(item, i) in shoppingList.items" :key="i">
        <div class="input-group">
          <div class="input-group-text">
            <input
              class="form-check-input mt-0"
              type="checkbox"
              v-model="item.done"
            />
          </div>
          <input
            type="text"
            class="form-control"
            placeholder="Shopping List Name"
            v-model="item.text"
          />
          <button
            class="btn btn-outline-danger"
            type="button"
            @click="shoppingList.items.splice(i, 1)"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </main>
</template>
