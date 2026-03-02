import type { ShoppingList } from "@/model"
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
  const res = await shoppingList.patch<{ok: boolean}>(`/${payload.id}`, payload)
  if (!res.ok) throw new Error("updateShoppingList failed")
}

export async function getAllShoppingLists() {
  return await shoppingList.get<ShoppingList[]>()
}
