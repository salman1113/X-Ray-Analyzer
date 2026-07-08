import { apiFetch } from "./client";

export const listTenants = () => apiFetch("/tenants/");

export const getMyTenant = () => apiFetch("/tenants/mine");

export const getTenant = (hospitalId) => apiFetch(`/tenants/${hospitalId}`);

/** Public — look up a tenant by its subdomain slug (no auth required). */
export const getTenantBySubdomain = (subdomain) =>
  apiFetch(`/tenants/by-subdomain/${encodeURIComponent(subdomain)}`, {
    auth: false,
  });

export const updateTenant = (hospitalId, data) =>
  apiFetch(`/tenants/${hospitalId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const regenerateInviteCode = (hospitalId) =>
  apiFetch(`/tenants/${hospitalId}/regenerate-invite`, { method: "POST" });

export const deactivateTenant = (hospitalId) =>
  apiFetch(`/tenants/${hospitalId}`, { method: "DELETE" });
