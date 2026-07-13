import { apiRequest, elements, escapeHtml, setStatus } from "./core.js";

let statusChecked = false;

function renderCitations(citations) {
  if (!citations.length) return "";
  const items = citations
    .map((c) => `
      <a class="rag-citation" href="${escapeHtml(c.url)}" target="_blank" rel="noopener">
        <span class="badge badge-jurisdiction">${escapeHtml(c.jurisdiction)}</span>
        <span class="rag-citation-type">${c.type === "rule" ? "Rule" : "Source"}</span>
        <span class="rag-citation-title">${escapeHtml(c.title)}</span>
      </a>
    `)
    .join("");
  return `
    <div class="ai-subhead">Cited rules &amp; sources</div>
    <div class="rag-citation-list">${items}</div>
  `;
}

function renderAnswer(result) {
  if (!elements.ragResult) return;
  const caveatHtml = result.caveat
    ? `<div class="rag-caveat">${escapeHtml(result.caveat)}</div>`
    : "";
  elements.ragResult.innerHTML = `
    <div class="rag-answer-card">
      <div class="rag-answer-text">${escapeHtml(result.answer)}</div>
      ${caveatHtml}
      ${renderCitations(result.citations)}
    </div>
  `;
}

async function checkRagStatus() {
  try {
    const status = await apiRequest("/rag/status");
    const ready = status.vector_db_available && status.ai_enabled;

    elements.ragUnavailableCard?.classList.toggle("hidden", ready);
    elements.ragCard?.classList.toggle("hidden", !ready);

    if (!ready && elements.ragUnavailableReason) {
      elements.ragUnavailableReason.textContent = !status.vector_db_available
        ? "The rules/sources vector database has not been built yet. Run rag/build_vector_db.py on the server, then reload this page."
        : "AI assist is not configured. Set ANTHROPIC_API_KEY on the server to enable grounded search.";
    }
    if (ready && elements.ragCardSub) {
      elements.ragCardSub.textContent =
        `Ask a question in plain English and get a grounded answer citing specific rules and official source pages. ` +
        `Indexed: ${status.rule_count} rules, ${status.source_chunk_count} source excerpts.`;
    }
  } catch {
    elements.ragUnavailableCard?.classList.remove("hidden");
    elements.ragCard?.classList.add("hidden");
    if (elements.ragUnavailableReason) {
      elements.ragUnavailableReason.textContent = "Could not reach the server to check RAG status.";
    }
  }
}

async function runRagQuery(event) {
  event.preventDefault();
  const question = elements.ragQuestionInput?.value.trim();
  if (!question) return;

  if (elements.ragAskBtn) elements.ragAskBtn.disabled = true;
  if (elements.ragResult) {
    elements.ragResult.innerHTML = '<div class="ai-empty-note">Searching the knowledge base&hellip;</div>';
  }
  try {
    const result = await apiRequest("/rag/query", {
      method: "POST",
      body: JSON.stringify({ question }),
    });
    renderAnswer(result);
    setStatus(`Answered from ${result.citations.length} cited rule/source${result.citations.length === 1 ? "" : "s"}.`);
  } catch (error) {
    console.error(error);
    if (elements.ragResult) {
      elements.ragResult.innerHTML = `<div class="ai-warning-list"><li>${escapeHtml(error.message)}</li></div>`;
    }
    setStatus(`RAG query failed: ${error.message}`, true);
  } finally {
    if (elements.ragAskBtn) elements.ragAskBtn.disabled = false;
  }
}

export function initRagSection() {
  elements.ragForm?.addEventListener("submit", runRagQuery);
}

export async function loadRagSection() {
  if (statusChecked) return;
  statusChecked = true;
  await checkRagStatus();
}
