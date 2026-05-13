import { elements, SECTION_META } from "./core.js";

let _onNavigate = null;

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

  // Rewire nav clicks via clone+replace so any pre-existing handlers (e.g. the
  // fallback bootstrap in script.js, which has no onNavigate callback) are
  // dropped and the modular navigateTo runs on every click.
  document.querySelectorAll(".nav-item").forEach((item) => {
    const sectionId = resolveSectionId(item.dataset.section);
    const fresh = item.cloneNode(true);
    item.parentNode.replaceChild(fresh, item);
    fresh.setAttribute("href", `#${sectionId}`);
    fresh.addEventListener("click", (event) => {
      event.preventDefault();
      navigateTo(sectionId, { updateHash: true });
    });
  });

  if (!window.__clearPathNavInitialized) {
    window.__clearPathNavInitialized = true;
    elements.dashEvaluateBtn?.addEventListener("click", () => navigateTo("evaluate", { updateHash: true }));
    window.addEventListener("hashchange", () => navigateTo(getSectionFromHash()));
  }

  navigateTo(getSectionFromHash());
}
