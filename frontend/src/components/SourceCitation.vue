<script setup>
defineProps({
  sources: { type: Array, default: () => [] },
});
</script>

<template>
  <div v-if="sources.length" class="mt-2 space-y-1 text-xs text-gray-500">
    <p class="uppercase tracking-wide">Sources</p>
    <div
      v-for="(source, i) in sources"
      :key="i"
      class="border-l-2 border-gray-300 pl-2"
    >
      <span class="font-medium">{{ source.filename }}</span>
      <span class="ml-1">({{ (source.score * 100).toFixed(0) }}% match)</span>
      <p class="text-gray-400 line-clamp-2">{{ source.chunk_text }}</p>
    </div>
  </div>
</template>
