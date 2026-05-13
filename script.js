const SECTION_META = {
  dashboard: { title: "Dashboard", sub: "Privacy-first cross-border advisory workspace" },
  evaluate: { title: "Private Assessment", sub: "Run a stateless client assessment without storing financial data" },
  clients: { title: "Client Storage Disabled", sub: "Private mode prevents persistent client financial records" },
  rules: { title: "Rules Library", sub: "Versioned, legislation-backed rules" },
  sources: { title: "Knowledge Sources", sub: "Legislation and guidance underpinning rules" },
  assets: { title: "Asset Storage Disabled", sub: "Private mode prevents persistent asset registers" },
};

function getSectionElements() {
  return {
    topbarTitle: document.getElementById("topbarTitle"),
    topbarSub: document.getElementById("topbarSub"),
    statusMessage: document.getElementById("statusMessage"),
    dashEvaluateBtn: document.getElementById("dashEvaluateBtn"),
  };
}

function resolveSectionId(sectionId) {
  if (!sectionId) return "dashboard";
  return document.getElementById(`section-${sectionId}`) ? sectionId : "dashboard";
}

function getSectionFromHash() {
  return resolveSectionId(window.location.hash.replace(/^#/, ""));
}

function navigateTo(sectionId, { updateHash = false } = {}) {
  const targetSectionId = resolveSectionId(sectionId);
  const { topbarTitle, topbarSub } = getSectionElements();

  document.querySelectorAll(".nav-item").forEach((element) => {
    element.classList.toggle("active", element.dataset.section === targetSectionId);
  });
  document.querySelectorAll(".section").forEach((element) => {
    element.classList.toggle("active", element.id === `section-${targetSectionId}`);
  });

  const meta = SECTION_META[targetSectionId] || {};
  if (topbarTitle) topbarTitle.textContent = meta.title || targetSectionId;
  if (topbarSub) topbarSub.textContent = meta.sub || "";

  if (updateHash) {
    const nextHash = `#${targetSectionId}`;
    if (window.location.hash !== nextHash) {
      history.replaceState(null, "", nextHash);
    }
  }
}

function initNavigationFallback() {
  if (window.__clearPathNavInitialized) return;
  window.__clearPathNavInitialized = true;

  document.querySelectorAll(".nav-item").forEach((item) => {
    const sectionId = resolveSectionId(item.dataset.section);
    item.setAttribute("href", `#${sectionId}`);
    item.addEventListener("click", (event) => {
      event.preventDefault();
      navigateTo(sectionId, { updateHash: true });
    });
  });

  const { dashEvaluateBtn } = getSectionElements();
  if (dashEvaluateBtn) {
    dashEvaluateBtn.addEventListener("click", () => navigateTo("evaluate", { updateHash: true }));
  }

  window.addEventListener("hashchange", () => navigateTo(getSectionFromHash()));
  navigateTo(getSectionFromHash());
}

async function bootModularApp() {
  try {
    const { bootApp } = await import("/frontend/app.js");
    await bootApp();
  } catch (error) {
    console.error("ClearPath frontend bootstrap failed.", error);
    const { statusMessage } = getSectionElements();
    if (statusMessage) {
      statusMessage.textContent = "Frontend modules failed to load. Basic navigation is still available.";
      statusMessage.classList.add("error");
    }
  }
}

initNavigationFallback();
void bootModularApp();
