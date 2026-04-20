/* Private-assessment orchestrator: owns mutable state, wires events, calls the API. */

import { apiRequest, elements, setStatus } from "./core.js";
import { DEFAULT_STATE, FIELD_MAP, PRESETS } from "./evaluation_config.js";
import {
  buildPayload,
  focusLabelList,
  inferFocusFromAnswers,
  missingPriorityFields,
  payloadToAnswers,
  providedFactCount,
  summarizeKnownFacts,
  uniquePriorityKeys,
} from "./evaluation_state.js";
import {
  renderFocusChips,
  renderQuestionGroups,
  renderReviewPanel,
  syncAnswerCount,
} from "./evaluation_render.js";
import { renderEvaluationResult, renderPreviewResult } from "./evaluation_views.js";

let answers = { ...DEFAULT_STATE };
let focusJurisdictions = new Set();

function getAssessmentSnapshot() {
  const reference = elements.evaluateAssessmentLabel?.value.trim() || "";
  const payload = buildPayload(answers);
  const focus = [...inferFocusFromAnswers(answers, focusJurisdictions)];
  const priorityMissing = missingPriorityFields(answers, focus);
  const priorityTotal = uniquePriorityKeys(focus).length;

  return {
    reference,
    payload,
    knownAnswers: answers,
    focus,
    factCount: providedFactCount(answers),
    priorityMissing,
    priorityTotal,
    priorityAnswered: priorityTotal - priorityMissing.length,
    highlights: summarizeKnownFacts(answers),
  };
}

function refreshReviewPanel() {
  renderReviewPanel(getAssessmentSnapshot());
}

function applyAnswers(nextAnswers, nextFocus = [], nextLabel = "") {
  answers = { ...DEFAULT_STATE, ...nextAnswers };
  focusJurisdictions = new Set(nextFocus);
  if (elements.evaluateAssessmentLabel) elements.evaluateAssessmentLabel.value = nextLabel || "";
  renderFocusChips(focusJurisdictions);
  renderQuestionGroups(answers, focusJurisdictions);
  syncAnswerCount(providedFactCount(answers));
  refreshReviewPanel();
}

function handleWorksheetChange(target) {
  const key = target.dataset.evalField;
  if (!key || !FIELD_MAP[key]) return;
  const field = FIELD_MAP[key];
  answers[key] = field.type === "number" ? (target.value === "" ? null : Number(target.value)) : target.value;
  syncAnswerCount(providedFactCount(answers));
  refreshReviewPanel();
}

function requestBody(snapshot) {
  return {
    assessment_label: elements.evaluateAssessmentLabel?.value.trim() || null,
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

async function importAssessment(file) {
  const parsed = JSON.parse(await file.text());
  const payload = parsed.client_data && typeof parsed.client_data === "object" ? parsed.client_data : parsed;
  const nextAnswers = payloadToAnswers(payload);
  const nextFocus = Array.isArray(parsed.focus_jurisdictions)
    ? parsed.focus_jurisdictions
    : [...inferFocusFromAnswers(nextAnswers, focusJurisdictions)];
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
  setStatus(`Preview complete - ${result.matched_count} matching rule${result.matched_count === 1 ? "" : "s"} found.`);
}

async function runEvaluation() {
  const snapshot = getActionSnapshot("running this assessment");
  if (!snapshot) return;

  const result = await apiRequest("/evaluate/private", {
    method: "POST",
    body: JSON.stringify(requestBody(snapshot)),
  });
  elements.evaluationResult.innerHTML = renderEvaluationResult(result, {
    focusLabel: focusLabelList(snapshot.focus),
    factCount: snapshot.factCount,
    readiness: snapshot.priorityTotal ? Math.round((snapshot.priorityAnswered / snapshot.priorityTotal) * 100) : 100,
  });
  const missingSuffix = snapshot.priorityMissing.length
    ? ` ${snapshot.priorityMissing.length} key prompt${snapshot.priorityMissing.length === 1 ? "" : "s"} still unanswered.`
    : "";
  setStatus(`Assessment complete - ${result.overall_risk.toUpperCase()} overall risk.${missingSuffix}`);
}

export function initEvaluationSection() {
  applyAnswers(DEFAULT_STATE, [], "");

  elements.evaluateGuidedSections?.addEventListener("input", (event) => handleWorksheetChange(event.target));
  elements.evaluateGuidedSections?.addEventListener("change", (event) => handleWorksheetChange(event.target));

  elements.evaluateGuidedSections?.addEventListener("click", (event) => {
    const button = event.target.closest(".ternary-option");
    if (!button) return;
    event.preventDefault();
    answers[button.dataset.ternaryKey] = button.dataset.ternaryValue === "true" ? true : button.dataset.ternaryValue === "false" ? false : null;
    renderQuestionGroups(answers, focusJurisdictions);
    syncAnswerCount(providedFactCount(answers));
    refreshReviewPanel();
  });

  elements.evaluateJurisdictionFocus?.addEventListener("click", (event) => {
    const button = event.target.closest(".focus-chip");
    if (!button) return;
    event.preventDefault();
    const jurisdiction = button.dataset.focusJurisdiction;
    if (focusJurisdictions.has(jurisdiction)) focusJurisdictions.delete(jurisdiction);
    else focusJurisdictions.add(jurisdiction);
    renderFocusChips(focusJurisdictions);
    renderQuestionGroups(answers, focusJurisdictions);
    syncAnswerCount(providedFactCount(answers));
    refreshReviewPanel();
  });

  document.querySelectorAll("[data-eval-preset]").forEach((button) => {
    button.addEventListener("click", () => {
      const preset = PRESETS[button.dataset.evalPreset];
      applyAnswers(preset.answers, preset.focus, preset.assessmentLabel);
      setStatus(`Loaded ${button.dataset.evalPreset.replace(/-/g, " ")} preset.`);
    });
  });

  elements.evaluateAssessmentLabel?.addEventListener("input", refreshReviewPanel);

  elements.resetEvaluateFormBtn?.addEventListener("click", () => {
    applyAnswers(DEFAULT_STATE, [], "");
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
