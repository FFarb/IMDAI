import type { MasterPromptPayload, TraitWeights } from '../types/discovery';

const PROMPT_API = '/api/prompt';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || 'Prompt API request failed');
  }
  return response.json() as Promise<T>;
}

export interface AutofillPayload {
  sessionId: string;
  audienceModes: string[];
  traitWeights: Partial<TraitWeights>;
}

export async function autofillMasterPrompt(payload: AutofillPayload): Promise<MasterPromptPayload> {
  const response = await fetch(`${PROMPT_API}/autofill`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: payload.sessionId,
      audience_modes: payload.audienceModes,
      trait_weights: payload.traitWeights,
    }),
  });
  return handleResponse<MasterPromptPayload>(response);
}
