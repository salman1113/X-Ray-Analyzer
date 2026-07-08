import { apiFetch, API_URL } from "./client";

export const listScans = (patientId = null) => {
  const query = patientId ? `?patient_id=${patientId}` : "";
  return apiFetch(`/scans/${query}`);
};

export const getScan = (scanId) => apiFetch(`/scans/${scanId}`);

export const createScan = (data) =>
  apiFetch("/scans/", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const uploadScanImage = async (scanId, file) => {
  const formData = new FormData();
  formData.append("file", file);

  return apiFetch(`/scans/${scanId}/upload`, {
    method: "POST",
    body: formData,
    // Don't set Content-Type — browser adds multipart boundary
    headers: {},
  });
};

export const deleteScan = (scanId) =>
  apiFetch(`/scans/${scanId}`, { method: "DELETE" });

// body_part defaults to "chest" for backwards compatibility
export const analyzeScan = (scanId, bodyPart = "chest") =>
  apiFetch("/ai/analyze", {
    method: "POST",
    body: JSON.stringify({ scan_id: scanId, body_part: bodyPart }),
  });

// Returns all supported body parts with conditions & descriptions
export const getBodyParts = () => apiFetch("/ai/body-parts");

// Returns the URL for the Grad-CAM heatmap image (use as <img src={...}>)
export const gradcamUrl = (scanId) =>
  `${API_URL}/ai/gradcam/${scanId}`;

// Returns the URL for the raw scan image (use as <img src={...}>)
export const scanImageUrl = (scanId) =>
  `${API_URL}/scans/${scanId}/image`;
