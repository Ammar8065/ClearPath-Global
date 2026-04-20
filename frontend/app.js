import { populateJurisdictionControls } from "./core.js";
import { loadDashboardStats, initDashboardSection } from "./dashboard.js";
import { initEvaluationSection } from "./evaluation.js";
import { initNavigation } from "./navigation.js";
import { loadRules, initRulesSection } from "./rules.js";
import { loadSources, initSourcesSection } from "./sources.js";
import { initTenantsSection, loadTenants } from "./tenants.js";

async function refreshWorkspaceViews() {
  return Promise.resolve();
}

export async function bootApp() {
  populateJurisdictionControls();
  initNavigation({
    onNavigate: (section) => {
      if (section === "dashboard") loadDashboardStats();
    },
  });
  initDashboardSection();
  initTenantsSection({
    refreshWorkspaceViews,
    loadDashboardStats,
  });
  initRulesSection({ loadDashboardStats });
  initSourcesSection({ loadDashboardStats });
  initEvaluationSection();

  await loadTenants();
  await loadDashboardStats();
  await loadRules();
  await loadSources();
  await refreshWorkspaceViews();

  // Auto-refresh dashboard every 15 seconds while it's the active view
  setInterval(() => {
    if (document.getElementById("section-dashboard")?.classList.contains("active")) {
      loadDashboardStats();
    }
  }, 15_000);
}
