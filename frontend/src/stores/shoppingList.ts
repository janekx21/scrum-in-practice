import {computed, type ComputedRef, ref} from 'vue'
import { createShoppingList, getShoppingList, updateShoppingList } from '@/api/shoppingListApi'
import {defineStore} from 'pinia'
import {v4 as uuid} from 'uuid'

type ShoppingList = {
  id: string
  serverId?: string 
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
      if (idx !== -1) {
        items.value.splice(idx, 1)
      }
    }

    // const doubleCount = computed(() => count.value * 2)
    function getById(id: string): ComputedRef<ShoppingList | undefined> {
      return computed(() => items.value.find((item) => item.id == id))
    }

    async function uploadToServer(localId: string) {
      const list = items.value.find((x) => x.id === localId)
      if (!list) return
    
      const payload = {
        name: list.name,
        items: list.items.map((i) => i.text), // backend expects list[str] :contentReference[oaicite:12]{index=12}
      }
    
      const created = await createShoppingList(payload)
      list.serverId = created.id
      return created.id
    }
    
    async function syncToServer(localId: string) {
      const list = items.value.find((x) => x.id === localId)
      if (!list?.serverId) return
    
      await updateShoppingList(list.serverId, {
        name: list.name,
        items: list.items.map((i) => i.text),
      })
    }
    
    async function loadFromServer(serverId: string) {
      // already in local store?
      const existing = items.value.find((x) => x.id === serverId)
      if (existing) return existing.id
    
      const data = await getShoppingList(serverId)
    
      const localList: ShoppingList = {
        id: data.id,          // ✅ key: use server UUID as local id
        serverId: data.id,
        name: data.name,
        items: data.items.map((t) => ({ text: t, done: false })),
      }
    
      items.value.push(localList)
      return localList.id
    }      

    return {items, addEmptyItem, removeItem, getById, uploadToServer, syncToServer, loadFromServer}
  },
  {persist: true},
)
