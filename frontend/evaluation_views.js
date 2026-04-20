import { jurisdictionBadge, riskBadge, scoreFill } from "./core.js";

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function renderPreviewResult(result, context) {
  const matchedRules = result.rules.filter((rule) => rule.matched);
  const unmatchedRules = result.rules.filter((rule) => !rule.matched);
  const reference = result.assessment_label || "Private assessment";

  return `
    <div class="eval-report">
      <div class="report-header">
        <div class="report-eyebrow">ClearPath Global - Private Rule Preview</div>
        <div class="report-risk-score">
          <div class="risk-indicator ${matchedRules.length ? "medium" : "low"}">${matchedRules.length ? "preview" : "clear"}</div>
          <div>
            <div class="risk-label">${matchedRules.length} Potential Match${matchedRules.length === 1 ? "" : "es"}</div>
            <div class="risk-sub">${escapeHtml(reference)} - ${result.matched_count} of ${result.total_active_rules} active rules currently match the provided facts.</div>
          </div>
        </div>
        <div class="report-meta">
          <div class="report-meta-item">
            <div class="report-meta-key">Reference</div>
            <div class="report-meta-val">${escapeHtml(reference)}</div>
          </div>
          <div class="report-meta-item">
            <div class="report-meta-key">Focus</div>
            <div class="report-meta-val">${escapeHtml(context.focusLabel || "General review")}</div>
          </div>
          <div class="report-meta-item">
            <div class="report-meta-key">Facts Provided</div>
            <div class="report-meta-val">${context.factCount}</div>
          </div>
          <div class="report-meta-item">
            <div class="report-meta-key">Readiness</div>
            <div class="report-meta-val">${context.readiness ?? 0}%</div>
          </div>
        </div>
      </div>

      <div>
        <div class="report-section-title">Matched Rules</div>
        <div class="item-list">
          ${matchedRules.length ? matchedRules.map((rule) => `
            <div class="triggered-rule-card ${rule.risk_level}">
              <div class="rule-card-top">
                <span class="rule-code">${escapeHtml(rule.rule_code)}</span>
                <div class="badge-row">
                  ${jurisdictionBadge(rule.jurisdiction)}
                  ${riskBadge(rule.risk_level)}
                </div>
              </div>
              <div class="rule-desc">${escapeHtml(rule.description)}</div>
              <div class="rule-source-row">
                <span class="rule-confidence">${escapeHtml(rule.reason)}</span>
              </div>
            </div>
          `).join("") : `
            <div class="no-triggers">
              <div class="no-triggers-title">No rules currently match</div>
              <div class="no-triggers-desc">The entered facts do not currently satisfy any active rule conditions.</div>
            </div>
          `}
        </div>
      </div>

      ${unmatchedRules.length ? `
        <div class="cat-breakdown-panel">
          <div class="report-section-title">Unmatched Rules</div>
          <div class="item-list preview-muted-list">
            ${unmatchedRules.slice(0, 6).map((rule) => `
              <div class="preview-muted-item">
                <div>
                  <div class="item-title">${escapeHtml(rule.rule_code)}</div>
                  <div class="item-meta">${escapeHtml(rule.description)}</div>
                </div>
                <div class="badge-row">${jurisdictionBadge(rule.jurisdiction)}</div>
              </div>
            `).join("")}
          </div>
        </div>
      ` : ""}
    </div>
  `;
}

function renderCategoryBreakdown(categoryBreakdown) {
  const labels = {
    residency: "Residency",
    tax: "Tax",
    cross_border: "Cross-Border",
    structure: "Structure",
  };

  return Object.entries(categoryBreakdown).map(([category, data]) => {
    const percent = Math.round(data.score);
    return `
      <div class="cat-row">
        <div class="cat-label">
          <span>${escapeHtml(labels[category] || category)}</span>
          <span class="cat-meta">${data.triggered_count} rule${data.triggered_count !== 1 ? "s" : ""} - ${escapeHtml(data.max_risk)} max</span>
        </div>
        <div class="cat-bar-track">
          <div class="cat-bar-fill" style="width:${percent}%;background:${scoreFill(data.score)}"></div>
        </div>
        <span class="cat-score">${percent}</span>
      </div>
    `;
  }).join("");
}

function renderCitations(citations) {
  if (!citations?.length) return "";
  return `
    <div class="report-section-title" style="margin-top:24px">Legislative Citations</div>
    <div class="citations-list">
      ${citations.map((citation) => `
        <div class="citation-item">
          <div class="citation-top">
            <span class="citation-code">${escapeHtml(citation.rule_code)}</span>
            <span class="badge badge-jurisdiction">${escapeHtml(citation.jurisdiction)}</span>
          </div>
          <div class="citation-source"><a href="${escapeHtml(citation.source_url)}" target="_blank" rel="noreferrer">${escapeHtml(citation.source_title)}</a></div>
          ${citation.section_reference ? `<div class="citation-ref">${escapeHtml(citation.section_reference)}</div>` : ""}
        </div>
      `).join("")}
    </div>
  `;
}

export function renderEvaluationResult(result, context) {
  const risk = result.overall_risk;
  const score = Math.min(100, Math.max(0, result.score || 0));
  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  const dashArray = `${(score / 100) * circumference} ${circumference}`;
  const jurisdictions = [...new Set(result.summary.map((item) => item.jurisdiction))].join(", ") || context.focusLabel || "General review";
  const reference = result.assessment_label || "Private assessment";

  const rulesHtml = !result.summary.length
    ? `
      <div class="no-triggers">
        <div class="no-triggers-title">No risk triggers identified</div>
        <div class="no-triggers-desc">No active rules were triggered by the facts entered in this private assessment.</div>
      </div>
    `
    : result.summary.map((item) => `
      <div class="triggered-rule-card ${item.risk_level}">
        <div class="rule-card-top">
          <span class="rule-code">${escapeHtml(item.rule_code)}</span>
          <div class="badge-row">
            ${jurisdictionBadge(item.jurisdiction)}
            ${riskBadge(item.risk_level)}
            <span class="badge badge-category">${escapeHtml(item.category || "")}</span>
          </div>
        </div>
        <div class="rule-desc">${escapeHtml(item.description)}</div>
        <div class="rule-source-row">
          ${item.section_reference ? `<span class="rule-section-ref">${escapeHtml(item.section_reference)}</span>` : ""}
          <span class="rule-score-chip">Score: ${(item.rule_score ?? 0).toFixed(1)}</span>
          <span class="rule-confidence">Confidence: ${escapeHtml(item.confidence_level || "-")}</span>
        </div>
        ${item.source_title
          ? `<div class="rule-source"><a href="${escapeHtml(item.source_url)}" target="_blank" rel="noreferrer">${escapeHtml(item.source_title)}</a></div>`
          : `<div class="rule-source">Source #${item.source_id}</div>`}
      </div>
    `).join("");

  return `
    <div class="eval-report">
      <div class="report-header">
        <div class="report-eyebrow">ClearPath Global - Private Assessment Report</div>
        <div class="report-risk-score">
          <div class="risk-indicator ${risk}">${escapeHtml(risk)}</div>
          <div class="score-gauge" title="Weighted composite risk score: ${score}/100">
            <svg width="70" height="70" viewBox="0 0 70 70">
              <circle cx="35" cy="35" r="${radius}" fill="none" stroke="var(--border)" stroke-width="7"/>
              <circle cx="35" cy="35" r="${radius}" fill="none" stroke="${scoreFill(score)}" stroke-width="7"
                stroke-dasharray="${dashArray}" stroke-dashoffset="${circumference / 4}" stroke-linecap="round"
                transform="rotate(-90 35 35)"/>
              <text x="35" y="39" text-anchor="middle" font-size="13" font-weight="700" fill="${scoreFill(score)}">${Math.round(score)}</text>
            </svg>
            <div class="score-label">Score</div>
          </div>
          <div>
            <div class="risk-label">${escapeHtml(risk.charAt(0).toUpperCase() + risk.slice(1))} Risk</div>
            <div class="risk-sub">${result.triggered_rules.length} rule${result.triggered_rules.length !== 1 ? "s" : ""} triggered across ${escapeHtml(jurisdictions)}</div>
          </div>
        </div>
        <div class="report-meta">
          <div class="report-meta-item"><div class="report-meta-key">Reference</div><div class="report-meta-val">${escapeHtml(reference)}</div></div>
          <div class="report-meta-item"><div class="report-meta-key">Facts Provided</div><div class="report-meta-val">${context.factCount}</div></div>
          <div class="report-meta-item"><div class="report-meta-key">Readiness</div><div class="report-meta-val">${context.readiness ?? 0}%</div></div>
          <div class="report-meta-item"><div class="report-meta-key">Rules Triggered</div><div class="report-meta-val">${result.triggered_rules.length}</div></div>
          <div class="report-meta-item"><div class="report-meta-key">Jurisdictions</div><div class="report-meta-val">${escapeHtml(jurisdictions)}</div></div>
        </div>
      </div>

      <div class="cat-breakdown-panel">
        <div class="report-section-title">Category Breakdown</div>
        <div class="cat-breakdown">${renderCategoryBreakdown(result.category_breakdown)}</div>
      </div>

      <div>
        <div class="report-section-title">Triggered Rules</div>
        <div class="item-list">${rulesHtml}</div>
      </div>

      ${renderCitations(result.citations)}
    </div>
  `;
}
