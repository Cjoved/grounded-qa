<script setup>
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const { isAuthenticated, checkSession } = useAuth()

onMounted(() => {
  checkSession()
})
</script>

<template>
  <div class="min-h-screen bg-white text-gray-900">
    <router-view v-slot="{ Component }">
      <header v-if="isAuthenticated" class="border-b px-6 py-4">
        <h1 class="text-xl font-semibold">Grounded Q&A</h1>
      </header>

      <nav v-if="isAuthenticated" class="flex gap-4 px-6 py-3 border-b text-sm">
        <router-link to="/chat" class="text-gray-500 hover:text-gray-900">Chat</router-link>
        <router-link to="/documents" class="text-gray-500 hover:text-gray-900">Documents</router-link>
        <router-link to="/eval" class="text-gray-500 hover:text-gray-900">Eval</router-link>
      </nav>

      <main class="max-w-3xl mx-auto px-6 py-6" style="height: calc(100vh - 130px)">
        <component :is="Component" />
      </main>
    </router-view>
  </div>
</template>