import type {
  DiscoverySearchPayload,
  ReferenceListResponse,
  DiscoverStats,
} from '../types/discovery';

const API_PREFIX = '/api/discover';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || 'Discovery API request failed');
  }
  if (response.status === 204) {
    return undefined as unknown as T;
  }
  return response.json() as Promise<T>;
}

export async function searchDiscovery(payload: DiscoverySearchPayload): Promise<string> {
  const response = await fetch(`${API_PREFIX}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await handleResponse<{ session_id: string }>(response);
  return data.session_id;
}

interface FetchReferencesParams {
  status?: 'result' | 'selected' | 'hidden' | 'deleted';
  offset?: number;
  limit?: number;
}

export async function fetchReferences(
  sessionId: string,
  params: FetchReferencesParams = {},
): Promise<ReferenceListResponse> {
  const searchParams = new URLSearchParams();
  if (params.status) searchParams.set('status', params.status);
  if (params.offset !== undefined) searchParams.set('offset', params.offset.toString());
  if (params.limit !== undefined) searchParams.set('limit', params.limit.toString());
  const query = searchParams.toString();
  const response = await fetch(`${API_PREFIX}/${sessionId}/items${query ? `?${query}` : ''}`);
  return handleResponse<ReferenceListResponse>(response);
}

export async function selectReference(
  sessionId: string,
  referenceId: string,
  weight?: number,
): Promise<void> {
  const response = await fetch(`${API_PREFIX}/${sessionId}/select`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reference_id: referenceId, weight }),
  });
  await handleResponse(response);
}

export async function hideReference(sessionId: string, referenceId: string): Promise<void> {
  const response = await fetch(`${API_PREFIX}/${sessionId}/hide`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reference_id: referenceId }),
  });
  await handleResponse(response);
}

export async function deleteReference(sessionId: string, referenceId: string): Promise<void> {
  const response = await fetch(`${API_PREFIX}/${sessionId}/delete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reference_id: referenceId }),
  });
  await handleResponse(response);
}

export async function starReference(sessionId: string, referenceId: string): Promise<number> {
  const response = await fetch(`${API_PREFIX}/${sessionId}/star`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reference_id: referenceId }),
  });
  const data = await handleResponse<{ weight: number }>(response);
  return data.weight;
}

export async function fetchStats(sessionId: string): Promise<DiscoverStats> {
  const response = await fetch(`${API_PREFIX}/${sessionId}/stats`);
  const data = await handleResponse<{ stats: DiscoverStats }>(response);
  return data.stats;
}

export async function uploadLocalReferences(
  sessionId: string,
  files: FileList,
): Promise<number> {
  const form = new FormData();
  Array.from(files).forEach((file) => form.append('files', file));
  const response = await fetch(`${API_PREFIX}/${sessionId}/local`, {
    method: 'POST',
    body: form,
  });
  const data = await handleResponse<{ count: number }>(response);
  return data.count;
}

export function persistSessionId(sessionId: string | null) {
  if (sessionId) {
    sessionStorage.setItem('discoverySessionId', sessionId);
  } else {
    sessionStorage.removeItem('discoverySessionId');
  }
}

export function loadPersistedSessionId(): string | null {
  return sessionStorage.getItem('discoverySessionId');
}
