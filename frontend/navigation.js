import { elements, SECTION_META } from "./core.js";

let _onNavigate = null;

const MOBILE_BREAKPOINT = 900;
const COLLAPSE_STORAGE_KEY = "clearpath.sidebarCollapsed";

function isMobileViewport() {
  return window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`).matches;
}

function getAppShell() {
  return document.querySelector(".app");
}

function setCollapsed(collapsed) {
  const sidebar = document.getElementById("sidebar");
  const app = getAppShell();
  if (!sidebar) return;
  sidebar.classList.toggle("sidebar--collapsed", collapsed);
  app?.classList.toggle("sidebar-is-collapsed", collapsed);
}

function applyStoredCollapseState(sidebar) {
  if (!sidebar || isMobileViewport()) return;
  try {
    if (localStorage.getItem(COLLAPSE_STORAGE_KEY) === "1") {
      setCollapsed(true);
    }
  } catch (_) { /* localStorage unavailable — ignore */ }
}

function persistCollapseState(collapsed) {
  try {
    localStorage.setItem(COLLAPSE_STORAGE_KEY, collapsed ? "1" : "0");
  } catch (_) { /* ignore */ }
}

function closeMobileSidebar() {
  document.body.classList.remove("sidebar-open");
  const sidebar = document.getElementById("sidebar");
  if (sidebar) sidebar.classList.remove("sidebar--open");
}

function openMobileSidebar() {
  document.body.classList.add("sidebar-open");
  const sidebar = document.getElementById("sidebar");
  if (sidebar) sidebar.classList.add("sidebar--open");
}

export function initSidebarControls() {
  if (window.__clearPathSidebarInitialized) return;
  const sidebar = document.getElementById("sidebar");
  const toggle = document.getElementById("sidebarToggle");
  const opener = document.getElementById("sidebarOpen");
  const scrim = document.getElementById("sidebarScrim");
  if (!sidebar) return;
  window.__clearPathSidebarInitialized = true;

  applyStoredCollapseState(sidebar);

  toggle?.addEventListener("click", (event) => {
    event.preventDefault();
    const collapsed = !sidebar.classList.contains("sidebar--collapsed");
    setCollapsed(collapsed);
    persistCollapseState(collapsed);
    toggle.setAttribute("aria-label", collapsed ? "Expand sidebar" : "Collapse sidebar");
    toggle.setAttribute("title", collapsed ? "Expand" : "Collapse");
  });

  opener?.addEventListener("click", (event) => {
    event.preventDefault();
    openMobileSidebar();
  });

  scrim?.addEventListener("click", (event) => {
    event.preventDefault();
    closeMobileSidebar();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && document.body.classList.contains("sidebar-open")) {
      closeMobileSidebar();
    }
  });

  window.addEventListener("resize", () => {
    if (!isMobileViewport() && document.body.classList.contains("sidebar-open")) {
      closeMobileSidebar();
    }
  });
}

function resolveSectionId(sectionId) {
  if (!sectionId) return "dashboard";
  return document.getElementById(`section-${sectionId}`) ? sectionId : "dashboard";
}

function getSectionFromHash() {
  return resolveSectionId(window.location.hash.replace(/^#/, ""));
}

export function navigateTo(sectionId, { updateHash = false } = {}) {
  const targetSectionId = resolveSectionId(sectionId);

  document.querySelectorAll(".nav-item").forEach((element) => element.classList.remove("active"));
  document.querySelectorAll(".section").forEach((element) => element.classList.remove("active"));

  const navElement = document.querySelector(`.nav-item[data-section="${targetSectionId}"]`);
  const sectionElement = document.getElementById(`section-${targetSectionId}`);

  if (navElement) navElement.classList.add("active");
  if (sectionElement) sectionElement.classList.add("active");

  const meta = SECTION_META[targetSectionId] || {};
  elements.topbarTitle.textContent = meta.title || targetSectionId;
  elements.topbarSub.textContent = meta.sub || "";

  if (updateHash) {
    const nextHash = `#${targetSectionId}`;
    if (window.location.hash !== nextHash) {
      history.replaceState(null, "", nextHash);
    }
  }

  _onNavigate?.(targetSectionId);
}

export function initNavigation({ onNavigate } = {}) {
  _onNavigate = onNavigate || null;

  initSidebarControls();

  if (window.__clearPathNavInitialized) {
    navigateTo(getSectionFromHash());
    return;
  }

  window.__clearPathNavInitialized = true;

  document.querySelectorAll(".nav-item").forEach((item) => {
    const sectionId = resolveSectionId(item.dataset.section);
    item.setAttribute("href", `#${sectionId}`);
    item.addEventListener("click", (event) => {
      event.preventDefault();
      navigateTo(sectionId, { updateHash: true });
      if (isMobileViewport()) closeMobileSidebar();
    });
  });

  elements.dashEvaluateBtn.addEventListener("click", () => {
    navigateTo("evaluate", { updateHash: true });
    if (isMobileViewport()) closeMobileSidebar();
  });
  window.addEventListener("hashchange", () => navigateTo(getSectionFromHash()));
  navigateTo(getSectionFromHash());

  initSidebarControls();
}
