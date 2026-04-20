import {
  apiRequest,
  elements,
  getActiveTenantId,
  jurisdictionBadge,
  setStatus,
} from "./core.js";

export async function loadAssets() {
  try {
    const tenantId = getActiveTenantId();

    if (!tenantId) {
      elements.assetsList.innerHTML = '<div class="empty-state">Select a workspace in the sidebar to view assets.</div>';
      setStatus("Ready");
      return;
    }

    const assets = await apiRequest(`/assets?tenant_id=${tenantId}`);
    if (!assets.length) {
      elements.assetsList.innerHTML = '<div class="empty-state">No assets recorded yet for this workspace.</div>';
      setStatus("Ready");
      return;
    }

    elements.assetsList.innerHTML = "";
    assets.forEach((asset) => {
      const card = document.createElement("div");
      card.className = "item-card";
      card.innerHTML = `
        <div class="item-top">
          <div>
            <div class="item-title">Asset #${asset.id} — Client #${asset.client_id}</div>
            <div class="item-meta">
              <span>Ownership: ${asset.ownership_structure}</span>
            </div>
          </div>
          <div class="badge-row">
            <span class="badge badge-asset-type">${asset.type}</span>
            ${jurisdictionBadge(asset.location)}
          </div>
        </div>
      `;
      elements.assetsList.appendChild(card);
    });
    setStatus("Ready");
  } catch (error) {
    console.error(error);
    setStatus(`Failed to load assets: ${error.message}`, true);
  }
}

export function initAssetsSection() {
  elements.assetForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(elements.assetForm);
    const payload = {
      client_id: Number(formData.get("client_id")),
      type: formData.get("type"),
      location: formData.get("location"),
      ownership_structure: formData.get("ownership_structure"),
    };

    try {
      await apiRequest("/assets", { method: "POST", body: JSON.stringify(payload) });
      elements.assetForm.reset();
      elements.assetLocationSelect.value = "AU";
      await loadAssets();
      setStatus("Asset created.");
    } catch (error) {
      console.error(error);
      setStatus(`Failed: ${error.message}`, true);
    }
  });

  elements.loadAssetsBtn.addEventListener("click", loadAssets);
}
