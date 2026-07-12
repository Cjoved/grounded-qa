<script setup>
import { ref } from "vue";
import ChatPanel from "./components/ChatPanel.vue";
import EvalDashboard from "./components/EvalDashboard.vue";
import UploadPanel from "./components/UploadPanel.vue";

const tab = ref("chat");
</script>

<template>
  <div class="min-h-screen bg-white text-gray-900">
    <header class="border-b px-6 py-4">
      <h1 class="text-xl font-semibold">Grounded Q&A</h1>
    </header>

    <nav class="flex gap-4 px-6 py-3 border-b text-sm">
      <button @click="tab = 'chat'" :class="tab === 'chat' ? 'font-semibold' : 'text-gray-500'">
        Chat
      </button>
      <button @click="tab = 'documents'" :class="tab === 'documents' ? 'font-semibold' : 'text-gray-500'">
        Documents
      </button>
      <button @click="tab = 'eval'" :class="tab === 'eval' ? 'font-semibold' : 'text-gray-500'">
        Eval
      </button>
    </nav>

    <main class="max-w-3xl mx-auto px-6 py-6" style="height: calc(100vh - 130px)">
      <ChatPanel v-if="tab === 'chat'" />
      <UploadPanel v-else-if="tab === 'documents'" />
      <EvalDashboard v-else-if="tab === 'eval'" />
    </main>
  </div>
</template>
