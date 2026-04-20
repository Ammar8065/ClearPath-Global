import { apiRequest } from "./core.js";

const JURISDICTIONS = [
  { code: "AU", label: "Australia" },
  { code: "SG", label: "Singapore" },
  { code: "HK", label: "Hong Kong" },
  { code: "UAE", label: "UAE" },
  { code: "US", label: "United States" },
];

const CATEGORIES = [
  { key: "residency", label: "Residency" },
  { key: "tax", label: "Tax" },
  { key: "cross_border", label: "Cross-Border" },
  { key: "structure", label: "Structure" },
];

const EXPIRY_WINDOW_DAYS = 90;

function renderBarRows(rows, maxCount) {
  if (!rows.length) return '<div class="dash-bar-empty">No data yet.</div>';
  return rows.map(({ label, count, colorClass, warn }) => `
    <div class="dash-bar-row${warn ? " dash-bar-row-gap" : ""}">
      <span class="dash-bar-label">${label}</span>
      <div class="dash-bar-track">
        ${count > 0
          ? `<div class="dash-bar-fill ${colorClass}" style="width:${Math.max(4, Math.round((count / maxCount) * 100))}%"></div>`
          : ""}
      </div>
      <span class="dash-bar-count${warn ? " dash-bar-count-gap" : ""}">${count > 0 ? count : "—"}</span>
    </div>
  `).join("");
}

function daysUntil(dateStr) {
  const target = new Date(dateStr + "T00:00:00");
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return Math.ceil((target - now) / (1000 * 60 * 60 * 24));
}

function urgencyClass(days) {
  if (days <= 0) return "dash-urgency-expired";
  if (days <= 30) return "dash-urgency-critical";
  if (days <= 60) return "dash-urgency-warning";
  return "dash-urgency-ok";
}

function urgencyLabel(days) {
  if (days <= 0) return "Expired";
  if (days === 1) return "1 day left";
  return `${days} days left`;
}

function renderRuleTable(rules, mode) {
  if (!rules.length) {
    const msg = mode === "expiring"
      ? "No rules expiring in the next 90 days."
      : "No rules added yet.";
    return `<div class="dash-bar-empty">${msg}</div>`;
  }

  const rows = rules.map((r) => {
    const riskClass = `badge-risk-${r.risk_level}`;
    if (mode === "expiring") {
      const days = daysUntil(r.effective_to);
      const uClass = urgencyClass(days);
      return `
        <div class="dash-table-row">
          <span class="dash-table-code">${r.rule_code}</span>
          <span class="badge badge-jurisdiction">${r.jurisdiction}</span>
          <span class="badge ${riskClass}">${r.risk_level.toUpperCase()}</span>
          <span class="dash-table-date">${r.effective_to}</span>
          <span class="dash-table-urgency ${uClass}">${urgencyLabel(days)}</span>
        </div>`;
    }
    // mode === "recent"
    const createdDate = r.created_at ? r.created_at.split("T")[0] : "—";
    return `
      <div class="dash-table-row">
        <span class="dash-table-code">${r.rule_code}</span>
        <span class="badge badge-jurisdiction">${r.jurisdiction}</span>
        <span class="badge ${riskClass}">${r.risk_level.toUpperCase()}</span>
        <span class="dash-table-category">${r.category.replace("_", " ")}</span>
        <span class="dash-table-date">${createdDate}</span>
      </div>`;
  }).join("");

  return `<div class="dash-table">${rows}</div>`;
}

export async function loadDashboardStats() {
  try {
    const [tenants, rules, sources] = await Promise.all([
      apiRequest("/tenants"),
      apiRequest("/rules"),
      apiRequest("/sources"),
    ]);

    const active = rules.filter((r) => !r.is_deleted);
    const total = active.length;

    // — Top stat cards —
    const el = (id) => document.getElementById(id);
    if (el("statClients")) el("statClients").textContent = tenants.length;
    if (el("statRules")) el("statRules").textContent = total;
    if (el("statSources")) el("statSources").textContent = sources.length;

    // Risk counts
    const riskCounts = { high: 0, medium: 0, low: 0 };
    active.forEach((r) => { if (r.risk_level in riskCounts) riskCounts[r.risk_level]++; });
    if (el("statHighRisk")) el("statHighRisk").textContent = riskCounts.high;

    // Expiring soon count
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    const cutoff = new Date(now);
    cutoff.setDate(cutoff.getDate() + EXPIRY_WINDOW_DAYS);
    const expiring = active.filter((r) => {
      if (!r.effective_to) return false;
      const d = new Date(r.effective_to + "T00:00:00");
      return d >= now && d <= cutoff;
    });
    const expired = active.filter((r) => {
      if (!r.effective_to) return false;
      return new Date(r.effective_to + "T00:00:00") < now;
    });
    const expiringTotal = expiring.length + expired.length;
    if (el("statExpiring")) {
      el("statExpiring").textContent = expiringTotal;
      el("statExpiring").closest(".stat-card")?.classList.toggle("stat-card--alert", expiringTotal > 0);
    }

    // Low confidence count
    const lowConfidence = active.filter((r) => r.confidence_level === "low").length;
    if (el("statLowConfidence")) {
      el("statLowConfidence").textContent = lowConfidence;
      el("statLowConfidence").closest(".stat-card")?.classList.toggle("stat-card--warn", lowConfidence > 0);
    }

    // — Last updated —
    if (el("dashLastUpdated")) {
      el("dashLastUpdated").textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    }

    // Flash live indicator
    const liveIndicator = el("dashLiveIndicator");
    if (liveIndicator) {
      liveIndicator.classList.add("dash-live-pulse");
      setTimeout(() => liveIndicator.classList.remove("dash-live-pulse"), 1000);
    }

    // — Risk breakdown —
    const maxRisk = Math.max(...Object.values(riskCounts), 1);
    if (el("dashRiskBreakdown")) {
      el("dashRiskBreakdown").innerHTML = renderBarRows([
        { label: "High", count: riskCounts.high, colorClass: "dash-bar-high" },
        { label: "Medium", count: riskCounts.medium, colorClass: "dash-bar-medium" },
        { label: "Low", count: riskCounts.low, colorClass: "dash-bar-low" },
      ], maxRisk);
    }

    // — Jurisdiction coverage —
    const jCounts = {};
    JURISDICTIONS.forEach(({ code }) => { jCounts[code] = 0; });
    active.forEach((r) => { if (r.jurisdiction in jCounts) jCounts[r.jurisdiction]++; });
    const maxJ = Math.max(...Object.values(jCounts), 1);
    if (el("dashJurisdictionBreakdown")) {
      el("dashJurisdictionBreakdown").innerHTML = renderBarRows(
        JURISDICTIONS.map(({ code, label }) => ({
          label,
          count: jCounts[code],
          colorClass: "dash-bar-brand",
          warn: jCounts[code] === 0,
        })),
        maxJ,
      );
    }

    // — Category breakdown —
    const catCounts = {};
    CATEGORIES.forEach(({ key }) => { catCounts[key] = 0; });
    active.forEach((r) => { if (r.category in catCounts) catCounts[r.category]++; });
    const maxCat = Math.max(...Object.values(catCounts), 1);
    if (el("dashCategoryBreakdown")) {
      el("dashCategoryBreakdown").innerHTML = renderBarRows(
        CATEGORIES.map(({ key, label }) => ({
          label,
          count: catCounts[key],
          colorClass: "dash-bar-brand",
          warn: catCounts[key] === 0,
        })),
        maxCat,
      );
    }

    // — Confidence distribution —
    const confCounts = { high: 0, medium: 0, low: 0 };
    active.forEach((r) => { if (r.confidence_level in confCounts) confCounts[r.confidence_level]++; });
    const maxConf = Math.max(...Object.values(confCounts), 1);
    if (el("dashConfidenceBreakdown")) {
      el("dashConfidenceBreakdown").innerHTML = renderBarRows([
        { label: "High", count: confCounts.high, colorClass: "dash-bar-low" },
        { label: "Medium", count: confCounts.medium, colorClass: "dash-bar-medium" },
        { label: "Low", count: confCounts.low, colorClass: "dash-bar-high" },
      ], maxConf);
    }

    // — Source coverage —
    const sourceRuleCounts = {};
    sources.forEach((s) => { sourceRuleCounts[s.id] = { title: s.title, count: 0 }; });
    active.forEach((r) => {
      if (r.source_id in sourceRuleCounts) sourceRuleCounts[r.source_id].count++;
    });
    const sourceRows = Object.values(sourceRuleCounts)
      .sort((a, b) => b.count - a.count)
      .slice(0, 8);
    const maxSrc = Math.max(...sourceRows.map((s) => s.count), 1);
    if (el("dashSourceCoverage")) {
      el("dashSourceCoverage").innerHTML = renderBarRows(
        sourceRows.map(({ title, count }) => ({
          label: title.length > 30 ? title.slice(0, 28) + "…" : title,
          count,
          colorClass: "dash-bar-brand",
          warn: count === 0,
        })),
        maxSrc,
      );
    }

    // — Expiring rules table —
    const expiringList = [...expired, ...expiring]
      .sort((a, b) => new Date(a.effective_to) - new Date(b.effective_to))
      .slice(0, 8);
    if (el("dashExpiringRules")) {
      el("dashExpiringRules").innerHTML = renderRuleTable(expiringList, "expiring");
    }

    // — Recently added rules table —
    const recentRules = [...active]
      .sort((a, b) => {
        const aDate = a.created_at || "";
        const bDate = b.created_at || "";
        return bDate.localeCompare(aDate);
      })
      .slice(0, 8);
    if (el("dashRecentRules")) {
      el("dashRecentRules").innerHTML = renderRuleTable(recentRules, "recent");
    }

  } catch (error) {
    console.error("Dashboard stats failed:", error);
  }
}

export function initDashboardSection() {
  document.getElementById("dashRefreshBtn")?.addEventListener("click", loadDashboardStats);
}
