export type ShoppingList = {
  id: string
  name: string
  items: ShoppingListItem[]
}

export type ShoppingListItem = {
  text: string
  done: boolean
}

