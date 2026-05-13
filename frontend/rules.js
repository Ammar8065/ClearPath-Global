import {
  apiRequest,
  deletedBadge,
  elements,
  escapeHtml,
  jurisdictionBadge,
  riskBadge,
  setStatus,
} from "./core.js";

let loadDashboardStats = async () => {};

export async function loadRules() {
  try {
    const rules = await apiRequest("/rules");
    const includeDeleted = elements.showDeletedRulesToggle.checked;
    const jurisdiction = elements.rulesJurisdictionFilter.value;

    let filtered = includeDeleted ? rules : rules.filter((rule) => !rule.is_deleted);
    if (jurisdiction) filtered = filtered.filter((rule) => rule.jurisdiction === jurisdiction);

    if (!filtered.length) {
      elements.rulesList.innerHTML = '<div class="empty-state">No rules found for the current filter.</div>';
      setStatus("Ready");
      return;
    }

    elements.rulesList.innerHTML = "";
    filtered.forEach((rule) => {
      const card = document.createElement("div");
      card.className = "item-card";
      card.innerHTML = `
        <div class="item-top">
          <div>
            <div class="item-title" style="font-family:monospace">${escapeHtml(rule.rule_code)} <small style="font-family:inherit;font-weight:500;color:var(--text-muted)">v${escapeHtml(rule.version ?? 1)}</small></div>
          </div>
          <div class="badge-row">
            ${jurisdictionBadge(rule.jurisdiction)}
            ${riskBadge(rule.risk_level)}
            <span class="badge badge-category">${escapeHtml(rule.category)}</span>
            ${rule.is_deleted ? deletedBadge() : ""}
            ${rule.review_status && rule.review_status !== "verified_current" ? `<span class="badge badge-review-${rule.review_status === "needs_update" ? "update" : "bad-source"}">${escapeHtml(rule.review_status.replace(/_/g, " "))}</span>` : ""}
          </div>
        </div>
        <div class="item-desc">${escapeHtml(rule.description)}</div>
        <div class="item-meta">
          <span>Confidence: <strong>${escapeHtml(rule.confidence_level)}</strong> · Effective: ${escapeHtml(rule.effective_from)}${rule.effective_to ? ` → ${escapeHtml(rule.effective_to)}` : " onwards"} · Source #${escapeHtml(rule.source_id)}</span>
        </div>
        ${!rule.is_deleted ? '<div style="margin-top:10px"><button class="btn btn-danger" data-rule-id="">Soft Delete</button></div>' : ""}
      `;

      const deleteButton = card.querySelector("[data-rule-id]");
      if (deleteButton) {
        deleteButton.dataset.ruleId = rule.id;
        deleteButton.addEventListener("click", () => handleRuleDelete(rule.id));
      }

      elements.rulesList.appendChild(card);
    });
    setStatus("Ready");
  } catch (error) {
    console.error(error);
    setStatus(`Failed to load rules: ${error.message}`, true);
  }
}

async function handleRuleDelete(ruleId) {
  if (!confirm("Soft delete this rule? It will be excluded from future evaluations.")) return;

  try {
    await apiRequest(`/rules/${ruleId}`, { method: "DELETE" });
    await loadRules();
    await loadDashboardStats();
    setStatus("Rule deleted.");
  } catch (error) {
    console.error(error);
    setStatus(`Failed: ${error.message}`, true);
  }
}

export function initRulesSection({ loadDashboardStats: loadStats }) {
  loadDashboardStats = loadStats;

  elements.ruleForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(elements.ruleForm);
    const conditionText = formData.get("condition_expression").trim();
    let parsedCondition;

    try {
      parsedCondition = JSON.parse(conditionText);
      elements.ruleJsonError.classList.add("hidden");
    } catch {
      elements.ruleJsonError.classList.remove("hidden");
      setStatus("Fix the JSON condition before submitting.", true);
      return;
    }

    const payload = {
      rule_code: formData.get("rule_code").trim(),
      jurisdiction: formData.get("jurisdiction"),
      category: formData.get("category"),
      condition_expression: parsedCondition,
      description: formData.get("description").trim(),
      risk_level: formData.get("risk_level"),
      confidence_level: formData.get("confidence_level"),
      source_id: Number(formData.get("source_id")),
      version: Number(formData.get("version")),
      effective_from: formData.get("effective_from"),
      effective_to: formData.get("effective_to") || null,
    };

    try {
      await apiRequest("/rules", { method: "POST", body: JSON.stringify(payload) });
      elements.ruleForm.reset();
      elements.ruleForm.elements.version.value = "1";
      elements.ruleForm.elements.condition_expression.value = '{ "field": "", "operator": "", "value": "" }';
      elements.ruleJsonError.classList.add("hidden");
      await loadRules();
      await loadDashboardStats();
      setStatus("Rule created.");
    } catch (error) {
      console.error(error);
      setStatus(`Failed: ${error.message}`, true);
    }
  });

  elements.loadRulesBtn.addEventListener("click", loadRules);
  elements.showDeletedRulesToggle.addEventListener("change", loadRules);
  elements.rulesJurisdictionFilter.addEventListener("change", loadRules);
}
