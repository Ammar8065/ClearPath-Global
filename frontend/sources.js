import { apiRequest, elements, escapeHtml, jurisdictionBadge, setStatus } from "./core.js";

let loadDashboardStats = async () => {};

export async function loadSources() {
  try {
    const sources = await apiRequest("/sources");
    const jurisdiction = elements.sourcesJurisdictionFilter.value;
    const filtered = jurisdiction ? sources.filter((source) => source.jurisdiction === jurisdiction) : sources;

    if (!filtered.length) {
      elements.sourcesList.innerHTML = '<div class="empty-state">No sources found.</div>';
      setStatus("Ready");
      return;
    }

    elements.sourcesList.innerHTML = "";
    filtered.forEach((source) => {
      const card = document.createElement("div");
      card.className = "item-card";
      const safeUrl = /^https?:\/\//i.test(source.url) ? source.url : "";
      card.innerHTML = `
        <div class="item-top">
          <div class="item-title">${escapeHtml(source.title)}</div>
          <div class="badge-row">
            ${jurisdictionBadge(source.jurisdiction)}
            <span class="badge badge-source-type">${escapeHtml(source.source_type.replace(/_/g, " "))}</span>
          </div>
        </div>
        <div class="item-meta" style="margin-top:6px">
          <span>Source ID: <strong>#${escapeHtml(source.id)}</strong></span>
          <a href="${escapeHtml(safeUrl)}" target="_blank" rel="noreferrer" style="color:var(--brand);word-break:break-all">${escapeHtml(source.url)}</a>
        </div>
      `;
      elements.sourcesList.appendChild(card);
    });
    setStatus("Ready");
  } catch (error) {
    console.error(error);
    setStatus(`Failed to load sources: ${error.message}`, true);
  }
}

export function initSourcesSection({ loadDashboardStats: loadStats }) {
  loadDashboardStats = loadStats;

  elements.sourceForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(elements.sourceForm);
    const payload = {
      jurisdiction: formData.get("jurisdiction"),
      title: formData.get("title").trim(),
      url: formData.get("url").trim(),
      source_type: formData.get("source_type"),
    };

    try {
      await apiRequest("/sources", { method: "POST", body: JSON.stringify(payload) });
      elements.sourceForm.reset();
      await loadSources();
      await loadDashboardStats();
      setStatus("Source created.");
    } catch (error) {
      console.error(error);
      setStatus(`Failed: ${error.message}`, true);
    }
  });

  elements.loadSourcesBtn.addEventListener("click", loadSources);
  elements.sourcesJurisdictionFilter.addEventListener("change", loadSources);
}
