import type { User } from '../types'

const KEY = 'calyx_user'

export function getSession(): User | null {
  try {
    const raw = sessionStorage.getItem(KEY)
    return raw ? (JSON.parse(raw) as User) : null
  } catch {
    return null
  }
}

export function setSession(user: User): void {
  sessionStorage.setItem(KEY, JSON.stringify(user))
}

export function clearSession(): void {
  sessionStorage.removeItem(KEY)
}
