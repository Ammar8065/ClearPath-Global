import { apiRequest, elements, setStatus } from "./core.js";

let refreshWorkspaceViews = async () => {};
let loadDashboardStats = async () => {};

export function syncSelectedTenant() {
  if (elements.clientTenantIdInput) {
    elements.clientTenantIdInput.value = elements.activeTenantSelect?.value || "";
  }
}

export async function loadTenants() {
  try {
    const tenants = await apiRequest("/tenants");
    const current = elements.activeTenantSelect?.value || "";

    if (elements.activeTenantSelect) {
      elements.activeTenantSelect.innerHTML = '<option value="">No tenant selected</option>';
      tenants.forEach((tenant) => {
        const option = document.createElement("option");
        option.value = tenant.id;
        option.textContent = tenant.name;
        elements.activeTenantSelect.appendChild(option);
      });

      if (current && tenants.some((tenant) => String(tenant.id) === current)) {
        elements.activeTenantSelect.value = current;
      } else if (tenants.length) {
        elements.activeTenantSelect.value = String(tenants[0].id);
      }
    }

    syncSelectedTenant();

    if (!elements.tenantsList) {
      setStatus("Ready");
      return;
    }

    if (!tenants.length) {
      elements.tenantsList.innerHTML = '<div class="empty-state">No workspaces yet. Create one to get started.</div>';
    } else {
      elements.tenantsList.innerHTML = "";
      tenants.forEach((tenant) => {
        const card = document.createElement("div");
        card.className = "tenant-card";
        card.innerHTML = `
          <div>
            <div class="tenant-name">${tenant.name}</div>
            <div class="tenant-id">Workspace ID #${tenant.id}</div>
          </div>
          <button
            class="btn btn-danger btn-sm tenant-delete-btn"
            data-tenant-id="${tenant.id}"
            data-tenant-name="${tenant.name}"
            title="Remove workspace"
          >Remove</button>
        `;
        elements.tenantsList.appendChild(card);
      });
    }

    setStatus("Ready");
  } catch (error) {
    console.error(error);
    syncSelectedTenant();
    setStatus(`Failed to load workspaces: ${error.message}`, true);
  }
}

export function initTenantsSection({ refreshWorkspaceViews: refreshViews, loadDashboardStats: loadStats }) {
  refreshWorkspaceViews = refreshViews;
  loadDashboardStats = loadStats;

  elements.activeTenantSelect?.addEventListener("change", async () => {
    syncSelectedTenant();
    await refreshWorkspaceViews();
  });

  elements.tenantForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = { name: new FormData(elements.tenantForm).get("name").trim() };

    try {
      await apiRequest("/tenants", { method: "POST", body: JSON.stringify(payload) });
      elements.tenantForm.reset();
      await loadTenants();
      await refreshWorkspaceViews();
      await loadDashboardStats();
      setStatus("Workspace created.");
    } catch (error) {
      console.error(error);
      setStatus(`Failed: ${error.message}`, true);
    }
  });

  elements.refreshTenantsBtn?.addEventListener("click", loadTenants);

  elements.tenantsList?.addEventListener("click", async (event) => {
    const btn = event.target.closest(".tenant-delete-btn");
    if (!btn) return;

    const tenantId = btn.dataset.tenantId;
    const tenantName = btn.dataset.tenantName;

    if (!confirm(`Remove workspace "${tenantName}"?\n\nThis will permanently delete the workspace and all its associated client records. This action cannot be undone.`)) return;

    try {
      await apiRequest(`/tenants/${tenantId}`, { method: "DELETE" });

      if (elements.activeTenantSelect?.value === tenantId) {
        elements.activeTenantSelect.value = "";
        syncSelectedTenant();
      }

      await loadTenants();
      await refreshWorkspaceViews();
      await loadDashboardStats();
      setStatus(`Workspace "${tenantName}" removed.`);
    } catch (error) {
      console.error(error);
      setStatus(`Failed to remove workspace: ${error.message}`, true);
    }
  });
}
