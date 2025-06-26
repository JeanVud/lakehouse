import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  isAuthenticated: boolean
  username: string
  login: (username: string, password: string) => boolean
  logout: () => void
}

const validCredentials = {
  admin: 'admin123',
  user: 'user123',
  demo: 'demo123',
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      username: '',
      login: (username: string, password: string) => {
        if (validCredentials[username as keyof typeof validCredentials] === password) {
          set({ isAuthenticated: true, username })
          return true
        }
        return false
      },
      logout: () => {
        set({ isAuthenticated: false, username: '' })
      },
    }),
    {
      name: 'auth-storage',
    }
  )
) 