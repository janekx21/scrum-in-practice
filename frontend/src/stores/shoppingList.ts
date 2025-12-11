import {computed, type ComputedRef, ref} from 'vue'
import {defineStore} from 'pinia'
import {v4 as uuid} from 'uuid'

type ShoppingList = {
  id: string
  name: string
  items: ShoppingListItem[]
}

type ShoppingListItem = {
  done: boolean
  text: string
}

function newShoppingList(): ShoppingList {
  return {id: uuid(), name: '', items: []}
}

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

    function addEmptyItem() {
      items.value.push(newShoppingList())
    }

    function removeItem(id: string) {
      const idx = items.value.findIndex((item) => item.id == id)
      if (idx != undefined) {
        items.value.splice(idx, 1)
      }
    }

    // const doubleCount = computed(() => count.value * 2)
    function getById(id: string): ComputedRef<ShoppingList | undefined> {
      return computed(() => items.value.find((item) => item.id == id))
    }

    return {items, addEmptyItem, removeItem, getById}
  },
  {persist: true},
)
