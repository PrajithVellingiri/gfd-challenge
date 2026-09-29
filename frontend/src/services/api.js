import { API_BASE_URL } from '../config';

/**
 * Submits a new citizen development request.
 */
export async function submitCitizenRequest(payload) {
  const response = await fetch(`${API_BASE_URL}/api/requests`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(payload.user_id ? { 'X-User-Id': payload.user_id } : {})
    },
    body: JSON.stringify(payload)
  });

  const data = await response.json();
  if (!response.ok) {
    const errorMsg = data?.error?.message || data?.detail || 'Failed to submit request';
    throw new Error(errorMsg);
  }
  return data;
}

/**
 * Fetches the authenticated citizen's request history.
 */
export async function fetchCitizenRequests(userId) {
  const url = userId 
    ? `${API_BASE_URL}/api/requests?user_id=${encodeURIComponent(userId)}`
    : `${API_BASE_URL}/api/requests`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      ...(userId ? { 'X-User-Id': userId } : {})
    }
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.detail || 'Failed to fetch request history');
  }
  return Array.isArray(data) ? data : [];
}

/**
 * Fetches a single request by ID with ownership authorization check.
 */
export async function fetchCitizenRequestById(requestId, userId) {
  const url = `${API_BASE_URL}/api/requests/${encodeURIComponent(requestId)}?user_id=${encodeURIComponent(userId)}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'X-User-Id': userId
    }
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.detail || 'Failed to retrieve request');
  }
  return data;
}

/**
 * Uploads media attachment (image or audio) to Supabase Storage via backend.
 */
export async function uploadAttachment(file, userId, requestId, bucketType) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('user_id', userId);
  formData.append('request_id', requestId);
  formData.append('bucket_type', bucketType);

  const response = await fetch(`${API_BASE_URL}/api/requests/upload`, {
    method: 'POST',
    body: formData
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.detail || `Failed to upload ${bucketType}`);
  }
  return data;
}

/**
 * Triggers Multimodal AI Analysis for a citizen request.
 */
export async function triggerAIAnalysis(requestId, userId) {
  const url = userId 
    ? `${API_BASE_URL}/api/requests/${encodeURIComponent(requestId)}/analyze?user_id=${encodeURIComponent(userId)}`
    : `${API_BASE_URL}/api/requests/${encodeURIComponent(requestId)}/analyze`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(userId ? { 'X-User-Id': userId } : {})
    }
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.detail || 'Failed to analyze request with AI');
  }
  return data;
}

/**
 * Fetches existing Multimodal AI Analysis for a citizen request.
 */
export async function fetchAIAnalysis(requestId, userId) {
  const url = userId 
    ? `${API_BASE_URL}/api/requests/${encodeURIComponent(requestId)}/analysis?user_id=${encodeURIComponent(userId)}`
    : `${API_BASE_URL}/api/requests/${encodeURIComponent(requestId)}/analysis`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      ...(userId ? { 'X-User-Id': userId } : {})
    }
  });

  if (response.status === 404) {
    return null;
  }

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.detail || 'Failed to fetch AI analysis');
  }
  return data;
}

/**
 * Fetches semantically similar requests for a citizen's request.
 */
export async function fetchSimilarRequests(requestId, userId, topK = 10) {
  const url = userId
    ? `${API_BASE_URL}/api/requests/${encodeURIComponent(requestId)}/similar?top_k=${topK}&user_id=${encodeURIComponent(userId)}`
    : `${API_BASE_URL}/api/requests/${encodeURIComponent(requestId)}/similar?top_k=${topK}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      ...(userId ? { 'X-User-Id': userId } : {})
    }
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.detail || 'Failed to fetch similar requests');
  }
  return Array.isArray(data) ? data : [];
}

/**
 * Fetches duplicate or near-duplicate requests.
 */
export async function fetchDuplicateRequests(requestId, userId) {
  const url = userId
    ? `${API_BASE_URL}/api/requests/${encodeURIComponent(requestId)}/duplicates?user_id=${encodeURIComponent(userId)}`
    : `${API_BASE_URL}/api/requests/${encodeURIComponent(requestId)}/duplicates`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      ...(userId ? { 'X-User-Id': userId } : {})
    }
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.detail || 'Failed to fetch duplicate requests');
  }
  return Array.isArray(data) ? data : [];
}

/**
 * Triggers request intelligence calculation.
 */
export async function triggerRequestIntelligence(requestId, userId) {
  const url = userId
    ? `${API_BASE_URL}/api/requests/${encodeURIComponent(requestId)}/intelligence?user_id=${encodeURIComponent(userId)}`
    : `${API_BASE_URL}/api/requests/${encodeURIComponent(requestId)}/intelligence`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(userId ? { 'X-User-Id': userId } : {})
    }
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.detail || 'Failed to trigger intelligence');
  }
  return data;
}

/**
 * Fetches semantic request clusters.
 */
export async function fetchClusters(districtId = null, category = null) {
  let url = `${API_BASE_URL}/api/intelligence/clusters`;
  const params = [];
  if (districtId) params.push(`district_id=${encodeURIComponent(districtId)}`);
  if (category) params.push(`category=${encodeURIComponent(category)}`);
  if (params.length > 0) url += `?${params.join('&')}`;

  const response = await fetch(url, { method: 'GET' });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.detail || 'Failed to fetch clusters');
  }
  return Array.isArray(data) ? data : [];
}

/**
 * Fetches emerging issue signals.
 */
export async function fetchEmergingIssues(districtId = null, category = null, windowDays = 7) {
  let url = `${API_BASE_URL}/api/intelligence/emerging-issues?window_days=${windowDays}`;
  if (districtId) url += `&district_id=${encodeURIComponent(districtId)}`;
  if (category) url += `&category=${encodeURIComponent(category)}`;

  const response = await fetch(url, { method: 'GET' });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.detail || 'Failed to fetch emerging issues');
  }
  return Array.isArray(data) ? data : [];
}


