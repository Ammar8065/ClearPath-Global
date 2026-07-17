import { apiRequest, setAuthTokenProvider, setStatus } from "./core.js";

const CLERK_JS_SRC = "https://cdn.jsdelivr.net/npm/@clerk/clerk-js@5/dist/clerk.browser.js";

let currentSession = { authenticated: false, userId: null, role: null, authEnabled: true };
let clerk = null;

export function getRole() {
  return currentSession.role;
}

export function isAdmin() {
  return currentSession.role === "admin";
}

function overlayElements() {
  return {
    overlay: document.getElementById("loginOverlay"),
    signInMount: document.getElementById("clerkSignIn"),
    error: document.getElementById("loginError"),
    footer: document.querySelector(".sidebar-footer"),
  };
}

function showLogin() {
  const { overlay } = overlayElements();
  if (overlay) overlay.classList.remove("hidden");
}

function hideLogin() {
  const { overlay } = overlayElements();
  if (overlay) overlay.classList.add("hidden");
}

function applySession(session) {
  currentSession = session;
  document.body.dataset.role = session.role || "";
  renderSidebarUser();
}

function displayName() {
  const user = clerk?.user;
  if (!user) return currentSession.userId || "";
  return user.fullName || user.primaryEmailAddress?.emailAddress || user.username || currentSession.userId;
}

function renderSidebarUser() {
  const { footer } = overlayElements();
  if (!footer) return;
  if (!currentSession.authenticated || !currentSession.authEnabled) {
    footer.innerHTML = "";
    return;
  }
  footer.innerHTML = `
    <div class="sidebar-user">
      <div class="sidebar-user-info">
        <div class="sidebar-user-name"></div>
        <div class="sidebar-user-role"></div>
      </div>
      <button type="button" class="btn btn-secondary btn-logout" id="logoutBtn">Logout</button>
    </div>
  `;
  footer.querySelector(".sidebar-user-name").textContent = displayName();
  footer.querySelector(".sidebar-user-role").textContent =
    currentSession.role === "admin" ? "Administrator" : "Viewer";
  footer.querySelector("#logoutBtn").addEventListener("click", async () => {
    try {
      await clerk?.signOut();
    } finally {
      window.location.reload();
    }
  });
}

function loadClerkJs(publishableKey) {
  return new Promise((resolve, reject) => {
    if (window.Clerk) {
      resolve();
      return;
    }
    const script = document.createElement("script");
    script.src = CLERK_JS_SRC;
    script.async = true;
    script.crossOrigin = "anonymous";
    script.dataset.clerkPublishableKey = publishableKey;
    script.onload = resolve;
    script.onerror = () => reject(new Error("Could not load the sign-in widget (network?)."));
    document.head.appendChild(script);
  });
}

async function establishBackendSession() {
  // Re-query status with the Bearer token attached so the backend decides
  // the role (admin vs viewer) — never trusted from the client side.
  const status = await apiRequest("/auth/status");
  applySession({
    authenticated: Boolean(status.authenticated),
    userId: status.user_id,
    role: status.role,
    authEnabled: status.auth_enabled,
  });
  return status.authenticated;
}

/**
 * Resolve once the user is authenticated (immediately when a Clerk session
 * already exists or auth is disabled server-side). Blocks app boot until then.
 */
export async function initAuth() {
  window.addEventListener("cp:unauthorized", () => {
    applySession({ authenticated: false, userId: null, role: null, authEnabled: true });
    showLogin();
  });

  let status;
  try {
    status = await apiRequest("/auth/status");
  } catch {
    setStatus("Could not reach the server to check the session.", true);
    status = { auth_enabled: true, authenticated: false, publishable_key: null };
  }

  if (!status.auth_enabled) {
    applySession({ authenticated: true, userId: status.user_id, role: status.role, authEnabled: false });
    return;
  }

  const { signInMount, error } = overlayElements();
  if (!status.publishable_key) {
    showLogin();
    if (error) {
      error.textContent = "Login is enabled but CLERK_PUBLISHABLE_KEY is not configured on the server.";
      error.classList.remove("hidden");
    }
    return new Promise(() => {}); // Unrecoverable client-side; block boot.
  }

  try {
    await loadClerkJs(status.publishable_key);
    // Loaded with data-clerk-publishable-key, the CDN bundle exposes a ready
    // instance at window.Clerk; without it, the class. Support both.
    clerk = typeof window.Clerk === "function" ? new window.Clerk(status.publishable_key) : window.Clerk;
    await clerk.load();
  } catch (clerkError) {
    showLogin();
    if (error) {
      error.textContent = clerkError.message;
      error.classList.remove("hidden");
    }
    return new Promise(() => {});
  }

  setAuthTokenProvider(async () => (clerk.session ? clerk.session.getToken() : null));

  if (clerk.user && (await establishBackendSession())) {
    hideLogin();
    return;
  }

  showLogin();
  clerk.mountSignIn(signInMount);

  await new Promise((resolve) => {
    clerk.addListener(async ({ user }) => {
      if (!user || currentSession.authenticated) return;
      if (await establishBackendSession()) {
        clerk.unmountSignIn(signInMount);
        hideLogin();
        setStatus("Ready");
        resolve();
      }
    });
  });
}
