import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/views/Login.vue'), meta: { public: true } },
    { path: '/chat', component: () => import('@/views/Chat.vue'), meta: { requiresAuth: true } },
    { path: '/documents', component: () => import('@/views/Documents.vue'), meta: { requiresAuth: true } },
    { path: '/eval', component: () => import('@/views/Eval.vue'), meta: { requiresAuth: true } },
    { path: '/', redirect: '/chat' },
    { path: '/:pathMatch(.*)*', redirect: '/chat' },
  ],
})

router.beforeEach(async (to, from, next) => {
  const { checkSession, isAuthenticated } = useAuth()
  await checkSession()

  if (to.meta.requiresAuth && !isAuthenticated.value) {
    next('/login')
  } else if (to.meta.public && isAuthenticated.value) {
    next('/chat')
  } else {
    next()
  }
})

export default router