import { apiFetch } from "./client";

export const getUsage = () => apiFetch("/billing/usage");
