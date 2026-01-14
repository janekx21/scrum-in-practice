import type { DeepPartial, ShoppingList } from "@/model"
import { mande } from "mande";

const BASE = '/api' // uses Vite proxy


const shoppingList = mande(`${BASE}/shopping-list`);

export async function createShoppingList(name: string) {
  return await shoppingList.post<ShoppingList>({name})
}

export async function getShoppingList(id: string) {
  return await shoppingList.get<ShoppingList>(`/${id}`)
}

export async function updateShoppingList(payload: ShoppingList) {
  let res = await shoppingList.patch<{ok: boolean}>(`/${payload.id}`, payload)
  if (!res.ok) throw new Error("updateShoppingList failed")
}

export async function getAllShoppingLists() {
  return await shoppingList.get<ShoppingList[]>()
}

// TODO remove
// export async function existsShoppingList(id: string) {
//   const res = await fetch(`${BASE}/shopping-list/${id}`, { method: 'GET' })
//   return res.ok
// }

