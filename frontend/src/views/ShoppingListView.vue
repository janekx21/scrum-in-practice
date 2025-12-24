<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { newShoppingListItem, useShoppingListStore } from '@/stores/shoppingList'
import { createShoppingList, updateShoppingList, existsShoppingList } from '@/api/shoppingListApi'

const store = useShoppingListStore()
const route = useRoute()
const router = useRouter()

const statusMsg = ref('')


const shoppingList = computed(() => {
  const id = route.params.id
  if (typeof id !== 'string') return undefined
  // store.getById(id) in your project is a computed; take its value
  return store.getById(id).value
})

async function save() {
  statusMsg.value = ''

  const list = shoppingList.value
  if (!list) {
    statusMsg.value = 'No list loaded.'
    return
  }

  const routeId = String(route.params.id)

  const payload = {
    name: list.name,
    items: list.items.map((i) => i.text),
  }

    const exists = await existsShoppingList(routeId)

  if (exists) {
    await updateShoppingList(routeId, payload)
    statusMsg.value = 'Saved. UUID: ' + routeId
    return
  }

  // Create a new list first
  const created = await createShoppingList({ name: payload.name, items: [] })

  // Then push items/name into DB using update endpoint
  await updateShoppingList(created.id, payload)

    list.id = created.id
  list.serverId = created.id

  statusMsg.value = 'Created & saved. UUID: ' + created.id

    router.replace('/shopping-list/' + created.id)
}
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
            <input class="form-check-input mt-0" type="checkbox" v-model="item.done" />
          </div>

          <input type="text" class="form-control" placeholder="Item" v-model="item.text" />

          <button class="btn btn-outline-danger" type="button" @click="shoppingList.items.splice(i, 1)">
            Delete
          </button>
        </div>
      </div>
    </div>

    <!-- Save button -->
    <button class="btn btn-success w-100" @click="save">
      Save
    </button>

    <div class="text-muted small mt-2" v-if="statusMsg">{{ statusMsg }}</div>
  </main>

  <main class="container" v-else>
    <div class="text-muted">No list found in local state for this URL.</div>
  </main>
</template>
