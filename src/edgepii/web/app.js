const state = { models: {}, model: "distilbert", busy: false };

const examples = {
  health: {text: "I'm a warehouse supervisor with chronic back pain from lifting heavy boxes. I live in Springfield and have two children. How can I reduce fatigue after long shifts?"}
};

const byId = (id) => document.getElementById(id);
const modelSelect = byId("model");
const contextInput = byId("context");
const questionInput = byId("question");
const analyzeButton = byId("analyze");

function updateModelDetails(resetThreshold = true) {
  const spec = state.models[modelSelect.value];
  if (!spec) return;
  state.model = modelSelect.value;
  byId("metric-f1").textContent = Number(spec.capid_f1).toFixed(3);
  byId("metric-latency").textContent = `${spec.median_ms} ms`;
}

async function refreshStatus() {
  try {
    const response = await fetch("/api/health", { cache: "no-store" });
    const data = await response.json();
    byId("metric-ram").textContent = `${Number(data.ram_mib).toFixed(1)} MiB`;
  } catch (error) {
    byId("metric-ram").textContent = "Unavailable";
  }
}

async function loadModels() {
  try {
    const response = await fetch("/api/models", { cache: "no-store" });
    const data = await response.json();
    state.models = data.models;
    modelSelect.innerHTML = Object.entries(state.models)
      .map(([key, spec]) => `<option value="${key}">${spec.label}</option>`)
      .join("");
    modelSelect.value = data.default;
    modelSelect.disabled = false;
    updateModelDetails();
  } catch (error) {
    showError(
      "The local server is unavailable. Restart the GUI and refresh this page.",
    );
  }
}

function setBusy(busy) {
  state.busy = busy;
  analyzeButton.disabled = busy;
  analyzeButton.textContent = busy ? "Running check" : "Run privacy check";
  modelSelect.disabled = busy;
}

function showError(message) {
  const results = byId("results");
  results.classList.remove("is-empty");
  byId("empty-state").hidden = false;
  byId("result-content").hidden = true;
  byId("empty-state").classList.add("error-box");
  byId("empty-state").querySelector("h2").textContent =
    "Unable to complete analysis";
  byId("empty-state").querySelector("p").textContent = message;
}

function resetEmptyState() {
  byId("empty-state").classList.remove("error-box");
  byId("empty-state").querySelector("h2").textContent = "No result yet";
  byId("empty-state").querySelector("p").textContent =
    "Run the privacy check to see protected text and detected entities.";
}

function escapeHtml(value) {
  return String(value).replace(
    /[&<>"]/g,
    (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[char],
  );
}

function renderResult(result) {
  resetEmptyState();

  byId("results").classList.remove("is-empty");
  byId("empty-state").hidden = true;
  byId("result-content").hidden = false;
  byId("protected-context").textContent = result.text;

  const loadText = result.loaded_now ? `, load ${Math.round(result.load_ms)} ms` : "";

  byId("run-meta").textContent = `${result.model_label} | ${Math.round(result.inference_ms)} ms inference${loadText}`;

  const spans = result.spans || [];
  byId("entity-count").textContent = `${spans.length} ${spans.length === 1 ? "entity" : "entities"}`;
  byId("no-entities").hidden = spans.length !== 0;
  byId("entity-body").innerHTML = spans
    .map((span) => {
      const relevance =
        span.relevance_probability == null
          ? "Not evaluated"
          : `${Math.round(span.relevance_probability * 100)}%`;
      const decision = span.masked ? "Masked" : "Retained";
      const decisionClass = span.masked ? "masked" : "kept";
      return `<tr>
      <td>${escapeHtml(span.value)}</td>
      <td><span class="pill type-tag">${escapeHtml(span.label)}</span></td>
      <td><span class="pill ${span.relevance_probability > 0.7 ? "kept" : "masked"}">${relevance}</span></td>
    </tr>`;
    })
    .join("");
  byId("results").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function analyze() {
  if (state.busy) return;

  const context = contextInput.value.trim();
  if (!context) {
    contextInput.focus();
    showError("Enter a context before running the model.");
    return;
  }

  setBusy(true);
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: modelSelect.value,
        context,
        policy: "context-aware",
        threshold: 0.75,
      }),
    });
    const data = await response.json();
    if (!response.ok || !data.ok)
      throw new Error(data.error || "Analysis failed");
    renderResult(data.result);
    await refreshStatus();
  } catch (error) {
    showError(error.message || "Analysis failed");
  } finally {
    setBusy(false);
  }
}

modelSelect.addEventListener("change", () => updateModelDetails(true));

byId("examples").innerHTML += `<select id="examples" name="examples">
        ${Object.entries(examples).map(([key, example]) => `<option value="${key}">${key}</option>`).join("")}
    </select>
`;

byId("examples").addEventListener("change", (event) => {
  const example = examples[event.target.value];
  if (!example) return;

  contextInput.value = example.text;
  byId("context-count").textContent = `${contextInput.value.length} characters`;
  resetEmptyState();
});

contextInput.addEventListener("input", () => {
  byId("context-count").textContent = `${contextInput.value.length} characters`;
});

byId("clear").addEventListener("click", () => {
  contextInput.value = "";
  questionInput.value = "";
  byId("examples").value = "";
  byId("context-count").textContent = "0 characters";
  contextInput.focus();
});

analyzeButton.addEventListener("click", analyze);

document.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    analyze();
  }
});

document.querySelectorAll(".copy-button").forEach((button) =>
  button.addEventListener("click", async () => {
    const target = byId(button.dataset.copy);
    await navigator.clipboard.writeText(target.textContent);
    const original = button.textContent;
    button.textContent = "Copied";
    window.setTimeout(() => {
      button.textContent = original;
    }, 1200);
  }),
);

loadModels();
refreshStatus();

window.setInterval(refreshStatus, 3000);
