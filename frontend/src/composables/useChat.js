import { ref } from "vue";
import { askQuestion } from "../services/api";

export function useChat() {
  const messages = ref([]); // { role: "user" | "assistant", content, sources? }
  const asking = ref(false);
  const error = ref("");

  async function ask(question) {
    messages.value.push({ role: "user", content: question });
    asking.value = true;
    error.value = "";
    try {
      const res = await askQuestion(question);
      messages.value.push({
        role: "assistant",
        content: res.answer,
        sources: res.sources,
      });
    } catch (e) {
      error.value = e.message;
    } finally {
      asking.value = false;
    }
  }

  return { messages, asking, error, ask };
}
