<script setup>
import { onMounted } from "vue";
import { useEval } from "../composables/useEval";

const { latestResults, running, error, run, loadHistory } = useEval();

onMounted(loadHistory);
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold">Eval Dashboard</h2>
      <button @click="run" :disabled="running" class="px-3 py-1.5 bg-black text-white rounded text-sm">
        {{ running ? "Running..." : "Run Eval" }}
      </button>
    </div>

    <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

    <div v-if="latestResults" class="grid grid-cols-3 gap-4">
      <div class="border rounded p-3">
        <p class="text-xs text-gray-500 uppercase">Retrieval Hit-Rate</p>
        <p class="text-2xl font-semibold">
          {{ (latestResults.summary.avg_retrieval_hit_rate * 100).toFixed(0) }}%
        </p>
      </div>
      <div class="border rounded p-3">
        <p class="text-xs text-gray-500 uppercase">Faithfulness</p>
        <p class="text-2xl font-semibold">
          {{ (latestResults.summary.avg_faithfulness * 100).toFixed(0) }}%
        </p>
      </div>
      <div class="border rounded p-3">
        <p class="text-xs text-gray-500 uppercase">Relevance</p>
        <p class="text-2xl font-semibold">
          {{ (latestResults.summary.avg_relevance * 100).toFixed(0) }}%
        </p>
      </div>
    </div>

    <table v-if="latestResults" class="w-full text-sm">
      <thead>
        <tr class="text-left text-gray-500 border-b">
          <th class="py-1">Question</th>
          <th class="py-1">Hit</th>
          <th class="py-1">Faithfulness</th>
          <th class="py-1">Relevance</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(r, i) in latestResults.results" :key="i" class="border-b">
          <td class="py-1">{{ r.question }}</td>
          <td class="py-1">{{ r.retrieval_hit ? "✓" : "✗" }}</td>
          <td class="py-1">{{ r.faithfulness_score.toFixed(2) }}</td>
          <td class="py-1">{{ r.relevance_score.toFixed(2) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
