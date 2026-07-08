import { apiFetch } from "./client";

export const listAllUsers = () => apiFetch("/users/");

export const listRoster = () => apiFetch("/users/roster");

export const removeDoctor = (email) =>
  apiFetch(`/users/roster/${encodeURIComponent(email)}`, { method: "DELETE" });
