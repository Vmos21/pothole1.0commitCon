const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api/v1';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    ...options,
  });

  if (!response.ok) {
    const body = await response.text();
    let detail = body;
    try {
      detail = JSON.parse(body).detail ?? body;
    } catch {
      detail = body;
    }
    throw new Error(detail || `Request failed (${response.status})`);
  }

  if (response.status === 204) return null;
  return response.json();
}

export function loginOfficial(credentials) {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
  });
}

export function fetchCurrentOfficial() {
  return request('/auth/me');
}

export function logoutOfficial() {
  return request('/auth/logout', { method: 'POST' });
}

export function fetchIncidents() {
  return request('/incidents');
}

export function fetchCameraStatus(incidentId) {
  return request(`/incidents/${encodeURIComponent(incidentId)}/camera-check`);
}

export function fetchEstimate(input) {
  return request('/incidents/estimate', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}
