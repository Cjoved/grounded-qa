import { ref } from "vue";
import { listDocuments, uploadFile, deleteDocument as apiDeleteDocument } from "../services/api";

export function useUpload() {
  const documents = ref([]);
  const uploading = ref(false);
  const error = ref("");

  async function loadDocuments() {
    error.value = "";
    try {
      documents.value = await listDocuments();
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

  async function deleteDocument(documentId) {
    error.value = "";
    try {
      await apiDeleteDocument(documentId);
      await loadDocuments();
    } catch (e) {
      error.value = e.message;
    }
  }

  return { documents, uploading, error, loadDocuments, upload, deleteDocument };
}
