import { API_BASE_URL, apiRequest, elements, escapeHtml, JURISDICTIONS, setStatus } from "./core.js";
import {
  DEFAULT_STATE,
  FIELD_MAP,
  fieldVisible,
  FOCUS_OPTIONS,
  GROUP_FIELD_KEYS,
  GROUPS,
  PRESETS,
  TAX_RESIDENCY_OPTIONS,
  US_STATE_OPTIONS,
} from "./evaluation_config.js";
import { renderAiSummary, renderEvaluationResult, renderPreviewResult } from "./evaluation_views.js";

let answers = { ...DEFAULT_STATE };
let focusJurisdictions = new Set();
let _reviewTimer = null;
let aiEnabled = false;
let lastEvaluationResult = null;
let pendingExtraction = null;

function debouncedRenderReview() {
  clearTimeout(_reviewTimer);
  _reviewTimer = setTimeout(renderReviewPanel, 80);
}

const CORE_PRIORITY_KEYS = [
  "days_in_country",
  "citizenship",
  "residency_country",
  "tax_residency_status",
];

const FOCUS_PRIORITY_KEYS = {
  AU: [
    "australian_source_income",
    "australian_property_owned",
    "permanent_abode_outside_country",
    "strong_personal_economic_ties_in_country",
  ],
  SG: [
    "singapore_source_income",
    "total_days_in_country",
    "sg_company_owned",
  ],
  HK: [
    "hong_kong_source_income",
    "hk_company_owned",
    "employer_provided_benefits_hk",
  ],
  UAE: [
    "uae_business_owned",
    "has_other_tax_residency",
    "tax_residency_certificate_requested",
  ],
  US: [
    "us_substantial_presence_days",
    "pfic_holdings",
    "foreign_financial_accounts_balance",
  ],
};

function focusLabelList(codes = [...focusJurisdictions]) {
  return codes.map((code) => FOCUS_OPTIONS.find((option) => option.value === code)?.label || code).join(", ");
}

function isValueProvided(field, value) {
  if (field.type === "ternary") return value === true || value === false;
  if (field.type === "number") return value !== null && value !== "" && Number.isFinite(Number(value));
  return typeof value === "string" ? value.trim() !== "" : value !== null && value !== undefined;
}

// Single definition of "provided" shared by the payload, the fact counter,
// and the highlights list: a field counts only when it is visible under the
// current showWhen rules AND has an answer. Hidden follow-up answers (e.g. a
// FIRB answer whose parent question was flipped back to No) are stale and
// must never reach the engine.
function providedEntries(sourceAnswers = answers) {
  return Object.entries(FIELD_MAP).filter(([key, field]) =>
    fieldVisible(field.showWhen, sourceAnswers) && isValueProvided(field, sourceAnswers[key]));
}

function buildPayload(sourceAnswers = answers) {
  const payload = {};
  providedEntries(sourceAnswers).forEach(([key, field]) => {
    const value = sourceAnswers[key];
    payload[key] = field.type === "number" ? Number(value) : value;
  });
  return payload;
}

function providedFactCount(sourceAnswers = answers) {
  return providedEntries(sourceAnswers).length;
}

function inferFocusFromAnswers(sourceAnswers = answers) {
  const derived = new Set(focusJurisdictions);
  GROUPS.forEach((group) => {
    if (!group.focus) return;
    const hasAnswers = GROUP_FIELD_KEYS[group.id].some((key) => isValueProvided(FIELD_MAP[key], sourceAnswers[key]));
    if (hasAnswers) derived.add(group.focus);
  });
  return derived;
}

function groupShouldShow(group) {
  if (group.alwaysVisible) return true;
  if (group.focus && focusJurisdictions.has(group.focus)) return true;
  return group.fields.some((field) => fieldVisible(field.showWhen, answers) && isValueProvided(field, answers[field.key]));
}

function answeredCountForGroup(group, sourceAnswers = answers) {
  return visibleFields(group.fields).filter((field) => isValueProvided(field, sourceAnswers[field.key])).length;
}

function uniquePriorityKeys(focusCodes = [...focusJurisdictions]) {
  return [...new Set([
    ...CORE_PRIORITY_KEYS,
    ...focusCodes.flatMap((code) => FOCUS_PRIORITY_KEYS[code] || []),
  ])].filter((key) => FIELD_MAP[key]);
}

function missingPriorityFields(sourceAnswers = answers, focusCodes = [...focusJurisdictions]) {
  return uniquePriorityKeys(focusCodes)
    .filter((key) => !isValueProvided(FIELD_MAP[key], sourceAnswers[key]))
    .map((key) => FIELD_MAP[key]);
}

function formatFieldValue(field, value) {
  if (field.type === "ternary") return value ? "Yes" : "No";
  if (field.type === "number") return new Intl.NumberFormat().format(Number(value));
  if (field.type === "jurisdiction") {
    return JURISDICTIONS.find((option) => option.value === value)?.label || value;
  }
  if (field.type === "tax_status") {
    return TAX_RESIDENCY_OPTIONS.find((option) => option.value === value)?.label || value;
  }
  if (field.type === "us_state") {
    return US_STATE_OPTIONS.find((option) => option.value === value)?.label || value;
  }
  return String(value);
}

function summarizeKnownFacts(sourceAnswers, limit = 8) {
  return providedEntries(sourceAnswers)
    .slice(0, limit)
    .map(([key, field]) => ({
      key,
      label: field.label,
      value: formatFieldValue(field, sourceAnswers[key]),
    }));
}

const ENUM_OPTION_VALUES = {
  jurisdiction: JURISDICTIONS.map((option) => option.value),
  tax_status: TAX_RESIDENCY_OPTIONS.map((option) => option.value).filter(Boolean),
  us_state: US_STATE_OPTIONS.map((option) => option.value).filter(Boolean),
};

function payloadToAnswers(payload) {
  const nextAnswers = { ...DEFAULT_STATE };
  Object.entries(FIELD_MAP).forEach(([key, field]) => {
    if (!(key in payload)) return;
    const value = payload[key];
    if (field.type === "number") {
      const num = value === "" || value === null ? null : Number(value);
      nextAnswers[key] = Number.isFinite(num) ? num : null;
    } else if (field.type === "ternary") {
      nextAnswers[key] = value === true ? true : value === false ? false : null;
    } else {
      // Imported values must match a real option — otherwise the select
      // would display "Not specified" while the stale value silently
      // stayed in the payload.
      const allowed = ENUM_OPTION_VALUES[field.type] || [];
      nextAnswers[key] = allowed.includes(value) ? value : "";
    }
  });
  return nextAnswers;
}

function setAnswerCountText(text) {
  if (elements.evaluateAnswerCount) elements.evaluateAnswerCount.textContent = text;
}

function syncAnswerCount(count) {
  setAnswerCountText(`${count} fact${count === 1 ? "" : "s"} provided`);
}

function getAssessmentSnapshot() {
  const reference = elements.evaluateAssessmentLabel?.value.trim() || "";
  const payload = buildPayload();
  const focus = [...inferFocusFromAnswers()];
  const priorityMissing = missingPriorityFields(answers, focus);
  const priorityTotal = uniquePriorityKeys(focus).length;

  return {
    reference,
    payload,
    knownAnswers: answers,
    focus,
    factCount: providedFactCount(),
    priorityMissing,
    priorityTotal,
    priorityAnswered: priorityTotal - priorityMissing.length,
    highlights: summarizeKnownFacts(answers),
  };
}

function renderReviewPanel() {
  if (!elements.evaluationReviewPanel) return;

  const snapshot = getAssessmentSnapshot();
  const readiness = snapshot.priorityTotal
    ? Math.round((snapshot.priorityAnswered / snapshot.priorityTotal) * 100)
    : 100;
  const focusLabel = focusLabelList(snapshot.focus) || "General review";
  const missingHtml = snapshot.priorityMissing.length
    ? snapshot.priorityMissing.slice(0, 5).map((field) => `
      <li class="review-list-item">${escapeHtml(field.label)}</li>
    `).join("")
    : '<li class="review-list-item review-list-item-ok">Core prompts covered for the current scope.</li>';
  const highlightHtml = snapshot.highlights.length
    ? snapshot.highlights.map((item) => `
      <li class="review-highlight-item">
        <span class="review-highlight-label">${escapeHtml(item.label)}</span>
        <span class="review-highlight-value">${escapeHtml(item.value)}</span>
      </li>
    `).join("")
    : '<li class="review-highlight-item review-highlight-item-empty">No facts added yet.</li>';

  elements.evaluationReviewPanel.innerHTML = `
    <div class="card eval-review-card">
      <div class="review-kicker">Live Review Snapshot</div>
      <div class="card-title">Assessment readiness</div>
      <div class="card-sub">Use this panel to sense-check scope, completeness, and privacy posture before you preview or run the rules engine.</div>

      <div class="review-stat-grid">
        <div class="review-stat">
          <div class="review-stat-label">Reference</div>
          <div class="review-stat-value">${escapeHtml(snapshot.reference || "Not set")}</div>
        </div>
        <div class="review-stat">
          <div class="review-stat-label">Provided facts</div>
          <div class="review-stat-value">${snapshot.factCount}</div>
        </div>
        <div class="review-stat">
          <div class="review-stat-label">Key facts covered</div>
          <div class="review-stat-value">${snapshot.priorityAnswered}/${snapshot.priorityTotal || 0}</div>
        </div>
      </div>

      <div class="review-progress-shell">
        <div class="review-progress-copy">
          <span>Readiness score</span>
          <strong>${readiness}%</strong>
        </div>
        <div class="review-progress-track">
          <div class="review-progress-fill" style="width:${readiness}%;"></div>
        </div>
      </div>

      <div class="review-section">
        <div class="review-section-title">Focus areas</div>
        <div class="review-chip-row">
          ${snapshot.focus.length
            ? snapshot.focus.map((code) => `
              <span class="review-chip">${escapeHtml(FOCUS_OPTIONS.find((option) => option.value === code)?.label || code)}</span>
            `).join("")
            : '<span class="review-chip review-chip-muted">General review</span>'}
        </div>
        <div class="review-section-note">${escapeHtml(focusLabel)}</div>
      </div>

      <div class="review-section">
        <div class="review-section-title">Next best facts to add</div>
        <ul class="review-list">${missingHtml}</ul>
      </div>

      <div class="review-section">
        <div class="review-section-title">Current payload highlights</div>
        <ul class="review-highlight-list">${highlightHtml}</ul>
      </div>

      <div class="review-mode-note">Unknown answers stay out of the payload — the engine will not infer a negative from missing information.</div>
    </div>
  `;
}

function renderFocusChips() {
  if (!elements.evaluateJurisdictionFocus) return;
  elements.evaluateJurisdictionFocus.innerHTML = FOCUS_OPTIONS.map((option) => `
    <button type="button" class="focus-chip${focusJurisdictions.has(option.value) ? " active" : ""}" data-focus-jurisdiction="${option.value}">
      ${option.label}
    </button>
  `).join("");
}

function visibleFields(fields) {
  return fields.filter((field) => fieldVisible(field.showWhen, answers));
}

function renderField(field) {
  const value = answers[field.key];
  const isFollowUp = !!field.showWhen;
  const wrapClass = `eval-question${isFollowUp ? " eval-question-followup" : ""}`;

  if (field.type === "ternary") {
    const selected = value === true ? "true" : value === false ? "false" : "unknown";
    return `
      <label class="${wrapClass}">
        <span class="eval-question-title">${field.label}</span>
        <span class="eval-question-help">${field.help}</span>
        <div class="ternary-input">
          <button type="button" class="ternary-option${selected === "unknown" ? " active" : ""}" data-ternary-key="${field.key}" data-ternary-value="unknown">Unknown</button>
          <button type="button" class="ternary-option${selected === "false" ? " active" : ""}" data-ternary-key="${field.key}" data-ternary-value="false">No</button>
          <button type="button" class="ternary-option${selected === "true" ? " active" : ""}" data-ternary-key="${field.key}" data-ternary-value="true">Yes</button>
        </div>
      </label>
    `;
  }
  if (field.type === "jurisdiction") {
    return `
      <label class="${wrapClass}">
        <span class="eval-question-title">${field.label}</span>
        <span class="eval-question-help">${field.help}</span>
        <select data-eval-field="${field.key}">
          <option value="">Not specified</option>
          ${JURISDICTIONS.map((option) => `<option value="${option.value}"${value === option.value ? " selected" : ""}>${option.label}</option>`).join("")}
        </select>
      </label>
    `;
  }
  if (field.type === "tax_status") {
    return `
      <label class="${wrapClass}">
        <span class="eval-question-title">${field.label}</span>
        <span class="eval-question-help">${field.help}</span>
        <select data-eval-field="${field.key}">
          ${TAX_RESIDENCY_OPTIONS.map((option) => `<option value="${option.value}"${value === option.value ? " selected" : ""}>${option.label}</option>`).join("")}
        </select>
      </label>
    `;
  }
  if (field.type === "us_state") {
    return `
      <label class="${wrapClass}">
        <span class="eval-question-title">${field.label}</span>
        <span class="eval-question-help">${field.help}</span>
        <select data-eval-field="${field.key}">
          ${US_STATE_OPTIONS.map((option) => `<option value="${option.value}"${value === option.value ? " selected" : ""}>${option.label}</option>`).join("")}
        </select>
      </label>
    `;
  }
  return `
    <label class="${wrapClass}">
      <span class="eval-question-title">${field.label}</span>
      <span class="eval-question-help">${field.help}</span>
      <input data-eval-field="${field.key}" type="${field.type === "number" ? "number" : "text"}" value="${value ?? ""}" placeholder="${field.placeholder || ""}" />
    </label>
  `;
}

function renderQuestionGroups() {
  if (!elements.evaluateGuidedSections) return;
  elements.evaluateGuidedSections.innerHTML = GROUPS.filter(groupShouldShow).map((group) => {
    const visible = visibleFields(group.fields);
    const answered = visible.filter((field) => isValueProvided(field, answers[field.key])).length;
    const total = visible.length;
    const pillClass = total > 0 && answered === total
      ? " eval-group-pill-complete"
      : answered > 0
        ? " eval-group-pill-active"
        : "";
    return `
      <details class="eval-group"${group.open ? " open" : ""}>
        <summary class="eval-group-summary">
          <div>
            <div class="eval-group-title">${group.title}</div>
            <div class="eval-group-desc">${group.description}</div>
          </div>
          <span class="eval-group-pill${pillClass}">${answered}/${total} answered</span>
        </summary>
        <div class="eval-group-grid">${visible.map(renderField).join("")}</div>
      </details>
    `;
  }).join("");
}

function applyAnswers(nextAnswers, nextFocus = [], nextLabel = "") {
  answers = { ...DEFAULT_STATE, ...nextAnswers };
  focusJurisdictions = new Set(nextFocus);
  if (elements.evaluateAssessmentLabel) elements.evaluateAssessmentLabel.value = nextLabel || "";
  renderFocusChips();
  renderQuestionGroups();
  syncAnswerCount(providedFactCount());
  renderReviewPanel();
}

function handleWorksheetChange(target) {
  const key = target.dataset.evalField;
  if (!key || !FIELD_MAP[key]) return;
  const field = FIELD_MAP[key];
  answers[key] = field.type === "number" ? (target.value === "" ? null : Number(target.value)) : target.value;
  renderQuestionGroups();
  syncAnswerCount(providedFactCount());
  debouncedRenderReview();
}

function requestBody(snapshot) {
  return {
    assessment_label: elements.evaluateAssessmentLabel?.value.trim() || null,
    // Scope the evaluation to the focused jurisdictions so generic fields
    // (days_in_country, tax_residency_status, ...) are only read by the
    // rules of the countries this assessment is actually about. An empty
    // focus means a general review across every jurisdiction.
    jurisdiction_scope: snapshot.focus.length ? snapshot.focus : null,
    client_data: snapshot.payload,
  };
}

function getActionSnapshot(actionLabel) {
  const snapshot = getAssessmentSnapshot();
  if (snapshot.factCount > 0) return snapshot;
  setStatus(`Add at least one fact before ${actionLabel}.`, true);
  return null;
}

function exportAssessment() {
  const snapshot = getActionSnapshot("exporting this assessment");
  if (!snapshot) return;

  const body = {
    version: 1,
    exported_at: new Date().toISOString(),
    assessment_label: elements.evaluateAssessmentLabel?.value.trim() || "",
    focus_jurisdictions: snapshot.focus,
    client_data: snapshot.payload,
  };
  const blob = new Blob([JSON.stringify(body, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "private-assessment.json";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  setStatus("Assessment exported locally.");
}

async function downloadPdfReport() {
  const snapshot = getActionSnapshot("generating this report");
  if (!snapshot) return;

  const includeAiSummary = aiEnabled && !!elements.includeAiSummaryToggle?.checked;
  setStatus(includeAiSummary ? "Generating report with AI summary..." : "Generating report...");
  try {
    const res = await fetch(`${API_BASE_URL}/evaluate/private/report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...requestBody(snapshot), include_ai_summary: includeAiSummary }),
    });
    if (!res.ok) throw new Error(`Server returned ${res.status}`);

    const blob = await res.blob();
    const disposition = res.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="?([^"]+)"?/i);
    const filename = match ? match[1] : "ClearPath Report.pdf";

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    setStatus("Report downloaded.");
  } catch (error) {
    console.error(error);
    setStatus(`Report generation failed: ${error.message}`, true);
  }
}

async function importAssessment(file) {
  const parsed = JSON.parse(await file.text());
  const payload = parsed.client_data && typeof parsed.client_data === "object" ? parsed.client_data : parsed;
  const nextAnswers = payloadToAnswers(payload);
  const nextFocus = Array.isArray(parsed.focus_jurisdictions) ? parsed.focus_jurisdictions : [...inferFocusFromAnswers(nextAnswers)];
  applyAnswers(nextAnswers, nextFocus, typeof parsed.assessment_label === "string" ? parsed.assessment_label : "");
  setStatus("Assessment imported from local file.");
}

async function runPreview() {
  const snapshot = getActionSnapshot("previewing this assessment");
  if (!snapshot) return;

  const result = await apiRequest("/evaluate/private/preview", {
    method: "POST",
    body: JSON.stringify(requestBody(snapshot)),
  });
  elements.evaluationResult.innerHTML = renderPreviewResult(result, {
    focusLabel: focusLabelList(snapshot.focus),
    factCount: snapshot.factCount,
    readiness: snapshot.priorityTotal ? Math.round((snapshot.priorityAnswered / snapshot.priorityTotal) * 100) : 100,
  });
  elements.evalResultActions?.classList.add("hidden");
  setStatus(`Preview complete - ${result.matched_count} matching rule${result.matched_count === 1 ? "" : "s"} found.`);
}

async function runEvaluation() {
  const snapshot = getActionSnapshot("running this assessment");
  if (!snapshot) return;

  const result = await apiRequest("/evaluate/private", {
    method: "POST",
    body: JSON.stringify(requestBody(snapshot)),
  });
  lastEvaluationResult = result;
  elements.evaluationResult.innerHTML = renderEvaluationResult(result, {
    focusLabel: focusLabelList(snapshot.focus),
    factCount: snapshot.factCount,
    readiness: snapshot.priorityTotal ? Math.round((snapshot.priorityAnswered / snapshot.priorityTotal) * 100) : 100,
  });
  elements.evalResultActions?.classList.remove("hidden");
  const missingSuffix = snapshot.priorityMissing.length
    ? ` ${snapshot.priorityMissing.length} key prompt${snapshot.priorityMissing.length === 1 ? "" : "s"} still unanswered.`
    : "";
  setStatus(`Assessment complete - ${result.overall_risk.toUpperCase()} overall risk.${missingSuffix}`);
}

// ── AI Assist ────────────────────────────────────────────────────────────────

async function initAiStatus() {
  try {
    const res = await fetch(new URL("/ai/status", API_BASE_URL));
    const status = res.ok ? await res.json() : { enabled: false };
    aiEnabled = !!status.enabled;
  } catch {
    aiEnabled = false;
  }
  elements.aiAssistCard?.classList.toggle("hidden", !aiEnabled);
  elements.aiSummaryBtn?.classList.toggle("hidden", !aiEnabled);
  elements.includeAiSummaryWrap?.classList.toggle("hidden", !aiEnabled);
}

function renderExtractionOutcome(extraction) {
  if (!elements.aiExtractionResult) return;

  const factsHtml = extraction.facts.length
    ? extraction.facts.map((fact) => `
      <div class="ai-fact-item">
        <div class="ai-fact-main">
          <span class="ai-fact-label">${escapeHtml(fact.label)}</span>
          <span class="ai-fact-value">${escapeHtml(formatFieldValue(FIELD_MAP[fact.field], fact.value))}</span>
        </div>
        <div class="ai-fact-evidence">&ldquo;${escapeHtml(fact.evidence)}&rdquo;</div>
      </div>
    `).join("")
    : '<div class="ai-empty-note">No worksheet facts were found in the notes.</div>';

  const unmappedHtml = extraction.unmapped_notes.length
    ? `
      <div class="ai-subhead">Mentioned but not on the worksheet</div>
      <ul class="ai-unmapped-list">${extraction.unmapped_notes.map((note) => `<li>${escapeHtml(note)}</li>`).join("")}</ul>
    `
    : "";

  const warningsHtml = extraction.warnings.length
    ? `<ul class="ai-warning-list">${extraction.warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`).join("")}</ul>`
    : "";

  elements.aiExtractionResult.innerHTML = `
    <div class="ai-extract-outcome">
      <div class="ai-subhead">${extraction.facts.length} fact${extraction.facts.length === 1 ? "" : "s"} extracted &mdash; review, then apply</div>
      <div class="ai-fact-list">${factsHtml}</div>
      ${unmappedHtml}
      ${warningsHtml}
      ${extraction.facts.length ? '<button type="button" class="btn btn-primary" id="aiApplyBtn">Apply To Worksheet</button>' : ""}
    </div>
  `;
  document.getElementById("aiApplyBtn")?.addEventListener("click", applyExtraction);
}

async function runAiExtraction() {
  const notes = elements.aiNotesInput?.value.trim();
  if (!notes) {
    setStatus("Paste some client notes before extracting.", true);
    return;
  }

  if (elements.aiExtractBtn) elements.aiExtractBtn.disabled = true;
  try {
    const extraction = await apiRequest("/ai/extract", {
      method: "POST",
      body: JSON.stringify({ notes }),
    });
    pendingExtraction = extraction;
    renderExtractionOutcome(extraction);
    setStatus(`AI extraction complete - ${extraction.facts.length} fact${extraction.facts.length === 1 ? "" : "s"} found.`);
  } catch (error) {
    console.error(error);
    setStatus(`AI extraction failed: ${error.message}`, true);
  } finally {
    if (elements.aiExtractBtn) elements.aiExtractBtn.disabled = false;
  }
}

function applyExtraction() {
  if (!pendingExtraction) return;

  const merged = { ...buildPayload(), ...pendingExtraction.client_data };
  const nextAnswers = payloadToAnswers(merged);
  applyAnswers(
    nextAnswers,
    [...inferFocusFromAnswers(nextAnswers)],
    elements.evaluateAssessmentLabel?.value.trim() || "",
  );
  setStatus(`Applied ${pendingExtraction.facts.length} AI-extracted fact${pendingExtraction.facts.length === 1 ? "" : "s"} to the worksheet.`);
}

async function runAiSummary() {
  if (!lastEvaluationResult) {
    setStatus("Run a full evaluation before generating a summary.", true);
    return;
  }

  if (elements.aiSummaryBtn) elements.aiSummaryBtn.disabled = true;
  try {
    const result = await apiRequest("/ai/summarise", {
      method: "POST",
      body: JSON.stringify({ evaluation: lastEvaluationResult }),
    });
    let container = document.getElementById("aiSummaryContainer");
    if (!container) {
      container = document.createElement("div");
      container.id = "aiSummaryContainer";
      elements.evaluationResult?.prepend(container);
    }
    container.innerHTML = renderAiSummary(result.summary);
    setStatus("AI summary generated.");
  } catch (error) {
    console.error(error);
    setStatus(`AI summary failed: ${error.message}`, true);
  } finally {
    if (elements.aiSummaryBtn) elements.aiSummaryBtn.disabled = false;
  }
}

export function initEvaluationSection() {
  applyAnswers(DEFAULT_STATE, [], "");
  initAiStatus();

  elements.aiExtractBtn?.addEventListener("click", () => runAiExtraction());
  elements.aiSummaryBtn?.addEventListener("click", () => runAiSummary());

  elements.evaluateGuidedSections?.addEventListener("input", (event) => handleWorksheetChange(event.target));
  elements.evaluateGuidedSections?.addEventListener("change", (event) => handleWorksheetChange(event.target));

  elements.evaluateGuidedSections?.addEventListener("click", (event) => {
    const button = event.target.closest(".ternary-option");
    if (!button) return;
    event.preventDefault();
    answers[button.dataset.ternaryKey] = button.dataset.ternaryValue === "true" ? true : button.dataset.ternaryValue === "false" ? false : null;
    renderQuestionGroups();
    syncAnswerCount(providedFactCount());
    debouncedRenderReview();
  });

  elements.evaluateJurisdictionFocus?.addEventListener("click", (event) => {
    const button = event.target.closest(".focus-chip");
    if (!button) return;
    event.preventDefault();
    const jurisdiction = button.dataset.focusJurisdiction;
    if (focusJurisdictions.has(jurisdiction)) focusJurisdictions.delete(jurisdiction);
    else focusJurisdictions.add(jurisdiction);
    renderFocusChips();
    renderQuestionGroups();
    syncAnswerCount(providedFactCount());
    debouncedRenderReview();
  });

  document.querySelectorAll("[data-eval-preset]").forEach((button) => {
    button.addEventListener("click", () => {
      const preset = PRESETS[button.dataset.evalPreset];
      applyAnswers(preset.answers, preset.focus, preset.assessmentLabel);
      setStatus(`Loaded ${button.dataset.evalPreset.replace(/-/g, " ")} preset.`);
    });
  });

  elements.evaluateAssessmentLabel?.addEventListener("input", debouncedRenderReview);

  elements.resetEvaluateFormBtn?.addEventListener("click", () => {
    applyAnswers(DEFAULT_STATE, [], "");
    lastEvaluationResult = null;
    pendingExtraction = null;
    if (elements.aiExtractionResult) elements.aiExtractionResult.innerHTML = "";
    if (elements.evaluationResult) {
      elements.evaluationResult.innerHTML = `
        <div class="eval-empty">
          <div class="eval-empty-icon">
            <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2"><circle cx="24" cy="24" r="20"/><path d="M24 14v10l6 4"/></svg>
          </div>
          <div class="eval-empty-title">No assessment run yet</div>
          <div class="eval-empty-desc">Use the live review snapshot to confirm completeness, preview the likely rule matches if needed, and then run the private assessment.</div>
        </div>
      `;
    }
    elements.evalResultActions?.classList.add("hidden");
    setStatus("Assessment reset.");
  });

  elements.previewEvaluationBtn?.addEventListener("click", () => runPreview().catch((error) => {
    console.error(error);
    setStatus(`Preview failed: ${error.message}`, true);
  }));

  elements.evaluateForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    runEvaluation().catch((error) => {
      console.error(error);
      setStatus(`Evaluation failed: ${error.message}`, true);
    });
  });

  elements.exportAssessmentBtn?.addEventListener("click", exportAssessment);
  elements.downloadPdfBtn?.addEventListener("click", downloadPdfReport);
  elements.importAssessmentBtn?.addEventListener("click", () => elements.assessmentImportInput?.click());
  elements.assessmentImportInput?.addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      await importAssessment(file);
    } catch (error) {
      console.error(error);
      setStatus("Could not import the selected assessment file.", true);
    } finally {
      event.target.value = "";
    }
  });
}
