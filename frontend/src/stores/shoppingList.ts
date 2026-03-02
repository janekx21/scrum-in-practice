import { computed, type ComputedRef, ref } from 'vue'
import { createShoppingList, getAllShoppingLists, getShoppingList, updateShoppingList } from '@/api/shoppingListApi'
import { defineStore } from 'pinia'
import type { ShoppingList, ShoppingListItem } from '@/model'


export function newShoppingListItem(): ShoppingListItem {
  return {
    text: '',
    done: false,
  }
}

export const useShoppingListStore = defineStore(
  'shoppingList',
  () => {
    const items = ref<ShoppingList[]>([])

    async function addEmptyItem() {
      const item = await createShoppingList("")
      items.value.push(item)
      console.log(items.value)
    }

    function removeItem(id: string) {
      const idx = items.value.findIndex((item) => item.id == id)
      if (idx !== -1) {
        items.value.splice(idx, 1)
        // TODO delete item from server
      }
    }

    function getById(id: string): ComputedRef<ShoppingList | undefined> {

      return computed(() => items.value.find((item) => item.id == id))

    }

    async function syncToServer(id: string) {
      const list = items.value.find((x) => x.id === id)

      if (!list) {
        return
      }

      await updateShoppingList(list)
    }

    async function fetchAllItems() {
      items.value = await getAllShoppingLists()
    }

    async function fetchSingleItem(id: string) {
      const item = await getShoppingList(id)

      const idx = items.value.findIndex(item => item.id == id);

      if(idx != -1) {
        items.value[idx] = item;
      } else {
        items.value.push(item)
      }
    }

    return {items, addEmptyItem, removeItem, getById, syncToServer, fetchAllItems, fetchSingleItem}
  },
  // {persist: true},
)
