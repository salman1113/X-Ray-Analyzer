import { apiFetch } from "./client";

export const getPlatformStats = () => apiFetch("/admin/stats");

export const getDashboardData = () => apiFetch("/admin/dashboard");
