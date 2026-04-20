/* DOM rendering for the private-assessment flow.
   All renderers are explicit about the state they take. */

import { elements, JURISDICTIONS } from "./core.js";
import {
  FIELD_MAP,
  FOCUS_OPTIONS,
  GROUPS,
  TAX_RESIDENCY_OPTIONS,
} from "./evaluation_config.js";
import {
  answeredCountForGroup,
  escapeHtml,
  focusLabelList,
  groupShouldShow,
} from "./evaluation_state.js";

export function setAnswerCountText(text) {
  if (elements.evaluateAnswerCount) elements.evaluateAnswerCount.textContent = text;
}

export function syncAnswerCount(count) {
  setAnswerCountText(`${count} fact${count === 1 ? "" : "s"} provided`);
}

export function renderReviewPanel(snapshot) {
  if (!elements.evaluationReviewPanel) return;

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

export function renderFocusChips(focusJurisdictions) {
  if (!elements.evaluateJurisdictionFocus) return;
  elements.evaluateJurisdictionFocus.innerHTML = FOCUS_OPTIONS.map((option) => `
    <button type="button" class="focus-chip${focusJurisdictions.has(option.value) ? " active" : ""}" data-focus-jurisdiction="${option.value}">
      ${option.label}
    </button>
  `).join("");
}

export function renderField(field, answers) {
  const value = answers[field.key];
  if (field.type === "ternary") {
    const selected = value === true ? "true" : value === false ? "false" : "unknown";
    return `
      <label class="eval-question">
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
      <label class="eval-question">
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
      <label class="eval-question">
        <span class="eval-question-title">${field.label}</span>
        <span class="eval-question-help">${field.help}</span>
        <select data-eval-field="${field.key}">
          ${TAX_RESIDENCY_OPTIONS.map((option) => `<option value="${option.value}"${value === option.value ? " selected" : ""}>${option.label}</option>`).join("")}
        </select>
      </label>
    `;
  }
  return `
    <label class="eval-question">
      <span class="eval-question-title">${field.label}</span>
      <span class="eval-question-help">${field.help}</span>
      <input data-eval-field="${field.key}" type="${field.type === "number" ? "number" : "text"}" value="${value ?? ""}" placeholder="${field.placeholder || ""}" />
    </label>
  `;
}

export function renderQuestionGroups(answers, focusJurisdictions) {
  if (!elements.evaluateGuidedSections) return;
  elements.evaluateGuidedSections.innerHTML = GROUPS.filter((group) => groupShouldShow(group, answers, focusJurisdictions)).map((group) => {
    const answered = answeredCountForGroup(group, answers);
    const pillClass = answered === group.fields.length
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
          <span class="eval-group-pill${pillClass}">${answered}/${group.fields.length} answered</span>
        </summary>
        <div class="eval-group-grid">${group.fields.map((field) => renderField(field, answers)).join("")}</div>
      </details>
    `;
  }).join("");
}
