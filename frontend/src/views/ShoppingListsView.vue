<script setup lang="ts">
import { useShoppingListStore } from '@/stores/shoppingList.ts'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const store = useShoppingListStore()
const router = useRouter()

const uuidInput = ref('')
const statusMsg = ref('')
</script>

<template>
    <main class="container">
    <h1 class="mb-4">Shopping List</h1>
      
      <div class="input-group mb-3">
      <input
        class="form-control"
        placeholder="Enter UUID (Share ID)"
        v-model="uuidInput"
      />
      <button
        class="btn btn-outline-secondary"
        type="button"
        @click="async () => {
          statusMsg = ''
          try {
            const id = uuidInput.trim()
            if (!id) return
            await store.loadFromServer(id)
            router.push('/shopping-list/' + id)
          } catch (e: any) {
            const msg = String(e)
            if (msg.includes('404')) {
              statusMsg = 'No such list. Create one.'
            } else {
              statusMsg = 'Load error: ' + msg
            }
          }
        }"
      >
        Load
      </button>
    </div>

    <div class="text-muted small mb-3" v-if="statusMsg">{{ statusMsg }}</div>
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
