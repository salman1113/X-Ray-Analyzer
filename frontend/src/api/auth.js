import { apiFetch, clearTokens } from "./client";

export const registerUser = (data) =>
  apiFetch("/auth/register", {
    method: "POST",
    auth: false,
    body: JSON.stringify(data),
  });

export const loginUser = (data) =>
  apiFetch("/auth/login", {
    method: "POST",
    auth: false,
    body: JSON.stringify(data),
  });

export const verifyOtp = (email, otp) =>
  apiFetch("/auth/verify-otp", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ email, otp }),
  });

export const forgotPassword = (email, origin) =>
  apiFetch("/auth/forgot-password", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ email, origin }),
  });

export const refreshToken = (refresh_token) =>
  apiFetch("/auth/refresh", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ refresh_token }),
  });

export const fetchCurrentUser = () => apiFetch("/auth/me");

export const logoutUser = async () => {
  try {
    await apiFetch("/auth/logout", { method: "POST" });
  } catch {
    // Logout failure should not block client-side cleanup
  }
  clearTokens();
};

// ── Passkey APIs ────────────────────────────────────────────────────────────

export const startPasskeyRegister = (email) =>
  apiFetch(`/auth/passkey/register/start?email=${encodeURIComponent(email)}`, {
    method: "POST",
    auth: false,
  });

export const verifyPasskeyRegister = (email, response) =>
  apiFetch(`/auth/passkey/register/verify?email=${encodeURIComponent(email)}`, {
    method: "POST",
    auth: false,
    body: JSON.stringify(response),
  });

export const startPasskeyLogin = (email) =>
  apiFetch(`/auth/passkey/login/start?email=${encodeURIComponent(email)}`, {
    method: "POST",
    auth: false,
  });

export const verifyPasskeyLogin = (email, response) =>
  apiFetch(`/auth/passkey/login/verify?email=${encodeURIComponent(email)}`, {
    method: "POST",
    auth: false,
    body: JSON.stringify(response),
  });

// ── Dashboard data (legacy compatibility, now via /admin/dashboard) ────────

export const fetchDashboardData = () => apiFetch("/admin/dashboard");
