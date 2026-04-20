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
  tenants: { title: "Workspaces", sub: "Manage advisory firm workspaces" },
};

export const elements = {
  activeTenantSelect: document.getElementById("activeTenantSelect"),
  clientTenantIdInput: document.getElementById("clientTenantId"),
  statusMessage: document.getElementById("statusMessage"),
  topbarTitle: document.getElementById("topbarTitle"),
  topbarSub: document.getElementById("topbarSub"),
  rulesList: document.getElementById("rulesList"),
  sourcesList: document.getElementById("sourcesList"),
  clientsList: document.getElementById("clientsList"),
  assetsList: document.getElementById("assetsList"),
  tenantsList: document.getElementById("tenantsList"),
  evaluationReviewPanel: document.getElementById("evaluationReviewPanel"),
  evaluationResult: document.getElementById("evaluationResult"),
  showDeletedRulesToggle: document.getElementById("showDeletedRulesToggle"),
  rulesJurisdictionFilter: document.getElementById("rulesJurisdictionFilter"),
  sourcesJurisdictionFilter: document.getElementById("sourcesJurisdictionFilter"),
  ruleJurisdictionSelect: document.getElementById("ruleJurisdictionSelect"),
  sourceJurisdictionSelect: document.getElementById("sourceJurisdictionSelect"),
  clientResidencySelect: document.getElementById("clientResidencySelect"),
  assetLocationSelect: document.getElementById("assetLocationSelect"),
  evaluateClientSelect: document.getElementById("evaluateClientSelect"),
  tenantForm: document.getElementById("tenantForm"),
  ruleForm: document.getElementById("ruleForm"),
  sourceForm: document.getElementById("sourceForm"),
  clientForm: document.getElementById("clientForm"),
  assetForm: document.getElementById("assetForm"),
  evaluateForm: document.getElementById("evaluateForm"),
  ruleJsonError: document.getElementById("ruleJsonError"),
  dashEvaluateBtn: document.getElementById("dashEvaluateBtn"),
  loadClientsBtn: document.getElementById("loadClientsBtn"),
  loadRulesBtn: document.getElementById("loadRulesBtn"),
  loadSourcesBtn: document.getElementById("loadSourcesBtn"),
  loadAssetsBtn: document.getElementById("loadAssetsBtn"),
  refreshTenantsBtn: document.getElementById("refreshTenantsBtn"),
  evaluateClientId: document.getElementById("evaluateClientId"),
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
};

export function getActiveTenantId() {
  return elements.activeTenantSelect?.value ? Number(elements.activeTenantSelect.value) : null;
}

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
  populateSelect(elements.clientResidencySelect, JURISDICTIONS);
  populateSelect(elements.assetLocationSelect, JURISDICTIONS);

  if (elements.ruleJurisdictionSelect) elements.ruleJurisdictionSelect.value = "AU";
  if (elements.sourceJurisdictionSelect) elements.sourceJurisdictionSelect.value = "SG";
  if (elements.clientResidencySelect) elements.clientResidencySelect.value = "UAE";
  if (elements.assetLocationSelect) elements.assetLocationSelect.value = "AU";
}

export function riskBadge(level) {
  return `<span class="badge badge-risk-${level}">${level.toUpperCase()}</span>`;
}

export function jurisdictionBadge(jurisdiction) {
  return `<span class="badge badge-jurisdiction">${jurisdiction}</span>`;
}

export function deletedBadge() {
  return '<span class="badge badge-deleted">Deleted</span>';
}

export function scoreFill(score) {
  if (score >= 65) return "var(--risk-high)";
  if (score >= 35) return "var(--risk-medium)";
  return "var(--risk-low)";
}
