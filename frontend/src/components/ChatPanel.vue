<script setup>
import { ref } from "vue";
import { useChat } from "../composables/useChat";
import SourceCitation from "./SourceCitation.vue";

const { messages, asking, error, ask } = useChat();
const input = ref("");

function submit() {
  if (!input.value.trim()) return;
  ask(input.value);
  input.value = "";
}
</script>

<template>
  <div class="flex flex-col h-full">
    <div class="flex-1 overflow-y-auto space-y-4 mb-4">
      <div v-for="(msg, i) in messages" :key="i">
        <p class="text-sm font-medium">{{ msg.role === "user" ? "You" : "Assistant" }}</p>
        <p class="text-sm">{{ msg.content }}</p>
        <SourceCitation v-if="msg.sources" :sources="msg.sources" />
      </div>
      <p v-if="asking" class="text-sm text-gray-500">Thinking...</p>
      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
    </div>

    <form @submit.prevent="submit" class="flex gap-2">
      <input
        v-model="input"
        type="text"
        placeholder="Ask a question about your documents..."
        class="flex-1 border rounded px-3 py-2 text-sm"
      />
      <button type="submit" :disabled="asking" class="px-4 py-2 bg-black text-white rounded text-sm">
        Ask
      </button>
    </form>
  </div>
</template>
