export const ADMIN_TOKEN_STORAGE_KEY = "hota-mds-admin-token";


function buildApiUrl(pathname) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "";
  return `${baseUrl}${pathname}`;
}


async function readApiResponse(response) {
  const payload = await response.json().catch(() => ({
    success: false,
    code: "INVALID_RESPONSE",
    message: "backend response is invalid",
    data: null,
  }));

  if (!response.ok || payload.success === false) {
    const error = new Error(payload.message || "request failed");
    error.status = response.status;
    error.code = payload.code;
    error.data = payload.data;
    throw error;
  }

  return payload;
}


export async function apiRequest(pathname, { method = "GET", token = "", body } = {}) {
  const headers = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(buildApiUrl(pathname), {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  return readApiResponse(response);
}
