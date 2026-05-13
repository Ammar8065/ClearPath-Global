import { populateJurisdictionControls } from "./core.js";
import { loadDashboardStats, initDashboardSection } from "./dashboard.js";
import { initEvaluationSection } from "./evaluation.js";
import { initNavigation } from "./navigation.js";
import { loadRules, initRulesSection } from "./rules.js";
import { loadSources, initSourcesSection } from "./sources.js";

export async function bootApp() {
  populateJurisdictionControls();

  const loaded = { rules: false, sources: false };

  initNavigation({
    onNavigate: (section) => {
      if (section === "dashboard") loadDashboardStats();
      if (section === "rules" && !loaded.rules) { loaded.rules = true; loadRules(); }
      if (section === "sources" && !loaded.sources) { loaded.sources = true; loadSources(); }
    },
  });
  initDashboardSection();
  initRulesSection({ loadDashboardStats });
  initSourcesSection({ loadDashboardStats });
  initEvaluationSection();

  await loadDashboardStats();

  const dashboardPollInterval = setInterval(() => {
    if (document.getElementById("section-dashboard")?.classList.contains("active")) {
      loadDashboardStats();
    }
  }, 15_000);
}
