<script setup>
import { onMounted, ref } from "vue";
import { useUpload } from "../composables/useUpload";

const { documents, uploading, error, loadDocuments, upload } = useUpload();
const fileInput = ref(null);

onMounted(loadDocuments);

function handleFileChange(event) {
  const file = event.target.files[0];
  if (file) upload(file);
}
</script>

<template>
  <div class="space-y-4">
    <h2 class="text-lg font-semibold">Documents</h2>

    <input
      ref="fileInput"
      type="file"
      accept=".pdf,.docx,.pptx,.html,.md"
      @change="handleFileChange"
      :disabled="uploading"
    />

    <p v-if="uploading" class="text-sm text-gray-500">Uploading...</p>
    <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

    <ul class="space-y-1">
      <li v-for="doc in documents" :key="doc.document_id" class="text-sm">
        {{ doc.filename }} ({{ doc.chunks }} chunks)
      </li>
    </ul>
  </div>
</template>
