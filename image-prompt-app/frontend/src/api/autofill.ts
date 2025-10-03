import type {
  AutofillResponse,
  OneClickResult,
  ResearchPayload,
  ResearchResult,
} from '../types/autofill';

const AUTOFILL_API = '/api/autofill';

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail: string | undefined;
    try {
      const data = await response.json();
      detail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data);
    } catch (error) {
      detail = await response.text();
    }
    throw new Error(detail || 'Autofill API request failed');
  }
  return response.json() as Promise<T>;
}

function extractWarning(response: Response): string | null {
  return response.headers.get('X-Autofill-Warning');
}

export async function postResearch(payload: ResearchPayload): Promise<ResearchResult> {
  const response = await fetch(`${AUTOFILL_API}/research`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      topic: payload.topic,
      audience: payload.audience,
      age: payload.age,
      flags: payload.flags,
    }),
  });
  const data = await parseResponse<AutofillResponse>(response);
  return { data, warning: extractWarning(response) };
}

export async function postOneClickGenerate(payload: ResearchPayload): Promise<OneClickResult> {
  const response = await fetch(`${AUTOFILL_API}/one_click_generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      topic: payload.topic,
      audience: payload.audience,
      age: payload.age,
      flags: payload.flags,
      images_n: payload.images_n,
    }),
  });
  const data = await parseResponse<OneClickResult['data']>(response);
  return { data, warning: extractWarning(response) };
}
