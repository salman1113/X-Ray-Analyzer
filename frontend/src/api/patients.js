import { apiFetch } from "./client";

export const listPatients = () => apiFetch("/patients/");

export const getPatient = (patientId) => apiFetch(`/patients/${patientId}`);

export const createPatient = (data) =>
  apiFetch("/patients/", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updatePatient = (patientId, data) =>
  apiFetch(`/patients/${patientId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const deletePatient = (patientId) =>
  apiFetch(`/patients/${patientId}`, { method: "DELETE" });
