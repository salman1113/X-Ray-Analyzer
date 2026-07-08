import { getCurrentSubdomain } from "../lib/subdomain";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const API_URL = `${API_BASE}/api/v1`;
const REQUEST_TIMEOUT_MS = 30000;

// ── Token helpers ───────────────────────────────────────────────────────────

export const getAccessToken = () => localStorage.getItem("access_token");
export const getRefreshToken = () => localStorage.getItem("refresh_token");

export const setTokens = (access, refresh) => {
  localStorage.setItem("access_token", access);
  if (refresh) localStorage.setItem("refresh_token", refresh);
};

export const clearTokens = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("has_passkey");
};

// ── Auto-refresh logic ─────────────────────────────────────────────────────

let isRefreshing = false;
let refreshQueue = [];

const processQueue = (error, token = null) => {
  refreshQueue.forEach((p) => {
    if (error) p.reject(error);
    else p.resolve(token);
  });
  refreshQueue = [];
};

async function refreshAccessToken() {
  const refresh = getRefreshToken();
  if (!refresh) throw new Error("No refresh token");

  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });

  if (!res.ok) {
    clearTokens();
    window.location.href = "/login";
    throw new Error("Refresh failed");
  }

  const data = await res.json();
  setTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

// ── Core fetch wrapper ─────────────────────────────────────────────────────

export async function apiFetch(path, options = {}) {
  const { auth = true, raw = false, ...fetchOpts } = options;

  const headers = { ...(fetchOpts.headers || {}) };

  if (auth) {
    const token = getAccessToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  // Forward tenant subdomain to API for resolution
  const sub = getCurrentSubdomain();
  if (sub && !headers["X-Tenant-Subdomain"]) {
    headers["X-Tenant-Subdomain"] = sub;
  }

  // Don't set Content-Type for FormData (browser sets boundary automatically)
  if (!(fetchOpts.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  // Add timeout via AbortController
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let res;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...fetchOpts,
      headers,
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeout);
    if (err.name === "AbortError") {
      throw new Error("Request timed out");
    }
    throw err;
  }
  clearTimeout(timeout);

  // If 401 and we have a refresh token, try refreshing
  if (res.status === 401 && auth && getRefreshToken()) {
    if (!isRefreshing) {
      isRefreshing = true;
      try {
        await refreshAccessToken();
        isRefreshing = false;
        processQueue(null, getAccessToken());
      } catch (err) {
        isRefreshing = false;
        processQueue(err);
        throw err;
      }
    } else {
      await new Promise((resolve, reject) => {
        refreshQueue.push({ resolve, reject });
      });
    }

    // Retry with new token
    headers["Authorization"] = `Bearer ${getAccessToken()}`;
    res = await fetch(`${API_URL}${path}`, { ...fetchOpts, headers });
  }

  if (raw) return res;

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    const error = new Error(err.detail || err.message || "Request failed");
    error.status = res.status;
    throw error;
  }

  return res.json();
}

export { API_URL, API_BASE };
