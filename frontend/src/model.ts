export type ShoppingList = {
  id: string
  name: string
  items: ShoppingListItem[]
}

export type ShoppingListItem = {
  text: string
  done: boolean
}

// Utility datatype for making properties recursive partial for patch
// Example:
// With a type T = {a: {b: str}[]}
// The DeepPartial<T> = {a: {b: str | undefined}[] | undefined}
export declare type DeepPartial<T> = {
    [K in keyof T]?: DeepPartial<T[K]>;
};

