import { ref } from 'vue'
import supabase from '@/services/supabase'

const user = ref(null)
const isAuthenticated = ref(false)

export function useAuth() {
  async function signIn(email, password) {
    if (!supabase) throw new Error('Supabase not configured')
    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error
    user.value = data.user
    isAuthenticated.value = true
    return data.session
  }

  async function signOut() {
    if (!supabase) return
    const { error } = await supabase.auth.signOut()
    if (error) throw error
    user.value = null
    isAuthenticated.value = false
  }

  async function checkSession() {
    if (!supabase) return null
    const { data: { session } } = await supabase.auth.getSession()
    if (session) {
      user.value = session.user
      isAuthenticated.value = true
      return session
    }
    return null
  }

  return { user, isAuthenticated, signIn, signOut, checkSession }
}