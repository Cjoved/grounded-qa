import { ref } from "vue";
import { getEvalHistory, runEval } from "../services/api";

export function useEval() {
  const latestResults = ref(null);
  const history = ref([]);
  const running = ref(false);
  const error = ref("");

  async function run() {
    running.value = true;
    error.value = "";
    try {
      latestResults.value = await runEval();
    } catch (e) {
      error.value = e.message;
    } finally {
      running.value = false;
    }
  }

  async function loadHistory() {
    error.value = "";
    try {
      history.value = await getEvalHistory();
    } catch (e) {
      error.value = e.message;
    }
  }

  return { latestResults, history, running, error, run, loadHistory };
}
