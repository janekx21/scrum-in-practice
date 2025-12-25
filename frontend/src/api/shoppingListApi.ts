type ServerShoppingList = {
    id: string
    name: string
    items: string[]
  }
  
  const BASE = '/api' // uses Vite proxy
  
  export async function createShoppingList(payload: { name: string; items: string[] }) {
    const res = await fetch(`${BASE}/shopping-list/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error(`createShoppingList failed: ${res.status}`)
    return (await res.json()) as { id: string; name: string }
  }
  
  export async function getShoppingList(id: string) {
    const res = await fetch(`${BASE}/shopping-list/${id}`, { method: 'GET' })
    if (!res.ok) throw new Error(`getShoppingList failed: ${res.status}`)
    return (await res.json()) as ServerShoppingList
  }
  
  export async function updateShoppingList(
    id: string,
    payload: { name?: string; items?: string[] },
  ) {
    const res = await fetch(`${BASE}/shopping-list/${id}`, {
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error(`updateShoppingList failed: ${res.status}`)
    return (await res.json()) as { status: string }
  }

  export async function existsShoppingList(id: string) {
    const res = await fetch(`${BASE}/shopping-list/${id}`, { method: 'GET' })
    return res.ok
  }
  
  