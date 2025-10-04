import type {
  AutofillResponse,
  OneClickResult,
  ResearchPayload,
  ResearchResult,
} from '../types/autofill';

const API_BASE = import.meta.env.VITE_API_BASE || '';
const AUTOFILL_API = `${API_BASE}/api/autofill`;

async function fetchJson<T>(url: string, init?: RequestInit): Promise<{
  data: T;
  warning: string | null;
}> {
  const response = await fetch(url, init);
  const text = await response.text();
  let parsed: unknown = null;

  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch (error) {
      // Ignore JSON parsing errors; handled via message below.
    }
  }

  if (!response.ok) {
    const body = parsed as Record<string, unknown> | null;
    const detail =
      (body &&
        (typeof body.detail === 'string'
          ? body.detail
          : typeof body.message === 'string'
            ? body.message
            : undefined)) ||
      text ||
      `${response.status} ${response.statusText}`;
    throw new Error(detail);
  }

  if (parsed === null) {
    throw new Error('Autofill API returned an empty response');
  }

  return {
    data: parsed as T,
    warning: response.headers.get('X-Autofill-Warning'),
  };
}

export async function postResearch(payload: ResearchPayload): Promise<ResearchResult> {
  const { data, warning } = await fetchJson<AutofillResponse>(`${AUTOFILL_API}/research`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      topic: payload.topic,
      audience: payload.audience,
      age: payload.age,
      flags: payload.flags,
    }),
  });
  return { data, warning };
}

export async function postOneClickGenerate(payload: ResearchPayload): Promise<OneClickResult> {
  const { data, warning } = await fetchJson<OneClickResult['data']>(
    `${AUTOFILL_API}/one_click_generate`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: payload.topic,
        audience: payload.audience,
        age: payload.age,
        flags: payload.flags,
        images_n: payload.images_n,
      }),
    },
  );
  return { data, warning };
}
