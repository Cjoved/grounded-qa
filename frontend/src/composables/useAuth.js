import { ref } from "vue";

// TODO (Week 1): initialize the Supabase client here with
// import.meta.env.VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY, and check
// against ALLOWED_EMAIL (enforced server-side too — never trust the
// frontend check alone).

const user = ref(null);
const isAuthenticated = ref(false);

export function useAuth() {
  async function signIn(email, password) {
    // TODO (Week 1): call supabase.auth.signInWithPassword
    throw new Error("Not implemented");
  }

  async function signOut() {
    // TODO (Week 1): call supabase.auth.signOut
    throw new Error("Not implemented");
  }

  return { user, isAuthenticated, signIn, signOut };
}
