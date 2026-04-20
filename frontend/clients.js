import {
  apiRequest,
  deletedBadge,
  elements,
  getActiveTenantId,
  jurisdictionBadge,
  setStatus,
} from "./core.js";

let loadDashboardStats = async () => {};

export async function loadClients() {
  try {
    const tenantId = getActiveTenantId();

    if (!tenantId) {
      elements.clientsList.innerHTML = '<div class="empty-state">Select a workspace in the sidebar to view clients.</div>';
      setStatus("Ready");
      return;
    }

    const clients = await apiRequest(`/clients?tenant_id=${tenantId}`);

    if (!clients.length) {
      elements.clientsList.innerHTML = '<div class="empty-state">No clients in this workspace yet.</div>';
      setStatus("Ready");
      return;
    }

    elements.clientsList.innerHTML = "";
    clients.forEach((client) => {
      const card = document.createElement("div");
      card.className = "item-card";
      card.innerHTML = `
        <div class="item-top">
          <div>
            <div class="item-title">Client #${client.id}</div>
            <div class="item-meta">
              <span>Citizenships: ${Array.isArray(client.citizenships) ? client.citizenships.join(", ") : client.citizenships}</span>
              <span>Current residency: ${client.current_residency}</span>
            </div>
          </div>
          <div class="badge-row">
            ${jurisdictionBadge(client.current_residency)}
            ${client.is_deleted ? deletedBadge() : ""}
          </div>
        </div>
        ${!client.is_deleted ? '<button class="btn btn-danger" data-client-id="">Soft Delete</button>' : ""}
      `;

      const deleteButton = card.querySelector("[data-client-id]");
      if (deleteButton) {
        deleteButton.dataset.clientId = client.id;
        deleteButton.addEventListener("click", () => handleClientDelete(client.id));
      }

      elements.clientsList.appendChild(card);
    });
    setStatus("Ready");
  } catch (error) {
    console.error(error);
    setStatus(`Failed to load clients: ${error.message}`, true);
  }
}

export async function populateEvaluateClientSelect() {
  const tenantId = getActiveTenantId();
  elements.evaluateClientSelect.innerHTML = '<option value="">Select a client...</option>';
  if (!tenantId) return;

  try {
    const clients = await apiRequest(`/clients?tenant_id=${tenantId}`);
    clients
      .filter((client) => !client.is_deleted)
      .forEach((client) => {
        const option = document.createElement("option");
        option.value = client.id;
        option.textContent = `Client #${client.id} - ${client.current_residency}`;
        option.dataset.currentResidency = client.current_residency || "";
        option.dataset.primaryCitizenship = Array.isArray(client.citizenships)
          ? (client.citizenships[0] || "")
          : (client.citizenships || "");
        elements.evaluateClientSelect.appendChild(option);
      });
  } catch (error) {
    console.error(error);
  }
}

async function handleClientDelete(clientId) {
  if (!confirm("Soft delete this client? The record will be retained but marked as deleted.")) return;

  try {
    await apiRequest(`/clients/${clientId}`, { method: "DELETE" });
    await loadClients();
    await populateEvaluateClientSelect();
    await loadDashboardStats();
    setStatus("Client deleted.");
  } catch (error) {
    console.error(error);
    setStatus(`Failed: ${error.message}`, true);
  }
}

export function initClientsSection({ loadDashboardStats: loadStats }) {
  loadDashboardStats = loadStats;

  elements.clientForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const tenantId = getActiveTenantId();
    if (!tenantId) {
      setStatus("Select a workspace first.", true);
      return;
    }

    const formData = new FormData(elements.clientForm);
    const payload = {
      citizenships: formData.get("citizenships").split(",").map((value) => value.trim()).filter(Boolean),
      current_residency: formData.get("current_residency"),
      tenant_id: tenantId,
    };

    try {
      await apiRequest("/clients", { method: "POST", body: JSON.stringify(payload) });
      elements.clientForm.reset();
      elements.clientTenantIdInput.value = elements.activeTenantSelect.value || "";
      await loadClients();
      await populateEvaluateClientSelect();
      await loadDashboardStats();
      setStatus("Client created.");
    } catch (error) {
      console.error(error);
      setStatus(`Failed: ${error.message}`, true);
    }
  });

  elements.loadClientsBtn.addEventListener("click", loadClients);
}
