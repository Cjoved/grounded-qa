import { ref } from "vue";
import { listDocuments, uploadFile } from "../services/api";

export function useUpload() {
  const documents = ref([]);
  const uploading = ref(false);
  const error = ref("");

  async function loadDocuments() {
    error.value = "";
    try {
      const res = await listDocuments();
      documents.value = res.documents;
    } catch (e) {
      error.value = e.message;
    }
  }

  async function upload(file) {
    uploading.value = true;
    error.value = "";
    try {
      await uploadFile(file);
      await loadDocuments();
    } catch (e) {
      error.value = e.message;
    } finally {
      uploading.value = false;
    }
  }

  return { documents, uploading, error, loadDocuments, upload };
}
