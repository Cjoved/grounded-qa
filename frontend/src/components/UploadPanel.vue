<script setup>
import { onMounted, ref } from "vue";
import { useUpload } from "../composables/useUpload";

const { documents, uploading, error, loadDocuments, upload, deleteDocument } = useUpload();
const fileInput = ref(null);

onMounted(loadDocuments);

function handleFileChange(event) {
  const file = event.target.files[0];
  if (file) upload(file);
}

async function handleDelete(doc) {
  if (!confirm(`Delete "${doc.filename}"?`)) return;
  await deleteDocument(doc.document_id);
}
</script>

<template>
  <div class="space-y-4">
    <h2 class="text-lg font-semibold">Documents</h2>

    <input
      ref="fileInput"
      type="file"
      accept=".pdf,.docx,.pptx,.html,.htm,.md,.txt"
      @change="handleFileChange"
      :disabled="uploading"
    />

    <p v-if="uploading" class="text-sm text-gray-500">Uploading...</p>
    <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

    <ul class="space-y-2">
      <li
        v-for="doc in documents"
        :key="doc.document_id"
        class="flex items-center justify-between px-3 py-2 bg-gray-50 rounded border"
      >
        <span class="text-sm">{{ doc.filename }} ({{ doc.chunk_count }} chunks)</span>
        <button
          @click="handleDelete(doc)"
          class="text-red-600 hover:text-red-800 text-sm px-2 py-1 border border-red-300 rounded hover:bg-red-50"
        >
          Delete
        </button>
      </li>
      <li v-if="documents.length === 0" class="text-sm text-gray-500 text-center py-4">
        No documents uploaded yet
      </li>
    </ul>
  </div>
</template>
