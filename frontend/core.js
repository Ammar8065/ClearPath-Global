export const API_BASE_URL = window.location.origin;

export const JURISDICTIONS = [
  { value: "AU", label: "Australia (AU)" },
  { value: "SG", label: "Singapore (SG)" },
  { value: "HK", label: "Hong Kong (HK)" },
  { value: "UAE", label: "United Arab Emirates (UAE)" },
  { value: "US", label: "United States (US)" },
];

export const SECTION_META = {
  dashboard: { title: "Dashboard", sub: "Privacy-first cross-border advisory workspace" },
  evaluate: { title: "Private Assessment", sub: "Run a stateless client assessment without storing financial data" },
  clients: { title: "Client Storage Disabled", sub: "Private mode prevents persistent client financial records" },
  rules: { title: "Rules Library", sub: "Versioned, legislation-backed rules" },
  sources: { title: "Knowledge Sources", sub: "Legislation and guidance underpinning rules" },
  assets: { title: "Asset Storage Disabled", sub: "Private mode prevents persistent asset registers" },
  ask: { title: "Ask ClearPath", sub: "Grounded search over the rules and sources knowledge base" },
};

export const elements = {
  statusMessage: document.getElementById("statusMessage"),
  topbarTitle: document.getElementById("topbarTitle"),
  topbarSub: document.getElementById("topbarSub"),
  rulesList: document.getElementById("rulesList"),
  sourcesList: document.getElementById("sourcesList"),
  evaluationReviewPanel: document.getElementById("evaluationReviewPanel"),
  evaluationResult: document.getElementById("evaluationResult"),
  showDeletedRulesToggle: document.getElementById("showDeletedRulesToggle"),
  rulesJurisdictionFilter: document.getElementById("rulesJurisdictionFilter"),
  sourcesJurisdictionFilter: document.getElementById("sourcesJurisdictionFilter"),
  ruleJurisdictionSelect: document.getElementById("ruleJurisdictionSelect"),
  sourceJurisdictionSelect: document.getElementById("sourceJurisdictionSelect"),
  ruleForm: document.getElementById("ruleForm"),
  sourceForm: document.getElementById("sourceForm"),
  evaluateForm: document.getElementById("evaluateForm"),
  ruleJsonError: document.getElementById("ruleJsonError"),
  dashEvaluateBtn: document.getElementById("dashEvaluateBtn"),
  loadRulesBtn: document.getElementById("loadRulesBtn"),
  loadSourcesBtn: document.getElementById("loadSourcesBtn"),
  evaluateGuidedSections: document.getElementById("evaluateGuidedSections"),
  evaluateGuidedFieldset: document.getElementById("evaluateGuidedFieldset"),
  resetEvaluateFormBtn: document.getElementById("resetEvaluateFormBtn"),
  evaluateAnswerCount: document.getElementById("evaluateAnswerCount"),
  evaluateAssessmentLabel: document.getElementById("evaluateAssessmentLabel"),
  evaluateJurisdictionFocus: document.getElementById("evaluateJurisdictionFocus"),
  previewEvaluationBtn: document.getElementById("previewEvaluationBtn"),
  exportAssessmentBtn: document.getElementById("exportAssessmentBtn"),
  importAssessmentBtn: document.getElementById("importAssessmentBtn"),
  assessmentImportInput: document.getElementById("assessmentImportInput"),
  downloadPdfBtn: document.getElementById("downloadPdfBtn"),
  evalResultActions: document.getElementById("evalResultActions"),
  aiAssistCard: document.getElementById("aiAssistCard"),
  aiNotesInput: document.getElementById("aiNotesInput"),
  aiExtractBtn: document.getElementById("aiExtractBtn"),
  aiExtractionResult: document.getElementById("aiExtractionResult"),
  aiSummaryBtn: document.getElementById("aiSummaryBtn"),
  includeAiSummaryWrap: document.getElementById("includeAiSummaryWrap"),
  includeAiSummaryToggle: document.getElementById("includeAiSummaryToggle"),
  ragUnavailableCard: document.getElementById("ragUnavailableCard"),
  ragUnavailableReason: document.getElementById("ragUnavailableReason"),
  ragCard: document.getElementById("ragCard"),
  ragCardSub: document.getElementById("ragCardSub"),
  ragForm: document.getElementById("ragForm"),
  ragQuestionInput: document.getElementById("ragQuestionInput"),
  ragAskBtn: document.getElementById("ragAskBtn"),
  ragResult: document.getElementById("ragResult"),
};

export function setStatus(message, isError = false) {
  if (!elements.statusMessage) return;
  elements.statusMessage.textContent = message;
  elements.statusMessage.classList.toggle("error", isError);
}

export async function apiRequest(path, options = {}) {
  setStatus("Working...", false);
  const response = await fetch(new URL(path, API_BASE_URL), {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message = typeof data === "string"
      ? data
      : data.detail || `Request failed with status ${response.status}`;
    throw new Error(message);
  }
  return data;
}

export function populateSelect(select, options, placeholder) {
  if (!select) return;
  select.innerHTML = "";
  if (placeholder) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = placeholder;
    select.appendChild(option);
  }
  options.forEach(({ value, label }) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    select.appendChild(option);
  });
}

export function populateJurisdictionControls() {
  populateSelect(elements.rulesJurisdictionFilter, JURISDICTIONS, "All jurisdictions");
  populateSelect(elements.sourcesJurisdictionFilter, JURISDICTIONS, "All jurisdictions");
  populateSelect(elements.ruleJurisdictionSelect, JURISDICTIONS);
  populateSelect(elements.sourceJurisdictionSelect, JURISDICTIONS);

  if (elements.ruleJurisdictionSelect) elements.ruleJurisdictionSelect.value = "AU";
  if (elements.sourceJurisdictionSelect) elements.sourceJurisdictionSelect.value = "SG";
}

export function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function riskBadge(level) {
  const safe = escapeHtml(level);
  return `<span class="badge badge-risk-${safe}">${safe.toUpperCase()}</span>`;
}

export function jurisdictionBadge(jurisdiction) {
  return `<span class="badge badge-jurisdiction">${escapeHtml(jurisdiction)}</span>`;
}

export function deletedBadge() {
  return '<span class="badge badge-deleted">Deleted</span>';
}

export function scoreFill(score) {
  if (score >= 65) return "var(--risk-high)";
  if (score >= 35) return "var(--risk-medium)";
  return "var(--risk-low)";
}
