import type { GenerateRequest, GenerateResponse, AgentGenerateResponse, StreamEvent } from '../types/pipeline';

export async function generatePipeline(payload: GenerateRequest): Promise<GenerateResponse | AgentGenerateResponse> {
  const response = await fetch('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : 'Request failed';
    throw new Error(detail);
  }
  return data as GenerateResponse | AgentGenerateResponse;
}

/**
 * Stream the multi-agent workflow execution via Server-Sent Events.
 * Only works when use_agents=true in the payload.
 */
export async function* streamAgentPipeline(payload: GenerateRequest): AsyncGenerator<StreamEvent> {
  if (!payload.use_agents) {
    throw new Error('Streaming requires use_agents=true');
  }

  const response = await fetch('/api/generate/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    const detail = typeof data?.detail === 'string' ? data.detail : 'Request failed';
    throw new Error(detail);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('Response body is not readable');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      // Decode the chunk and add to buffer
      buffer += decoder.decode(value, { stream: true });

      // Process complete SSE messages
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonStr = line.slice(6); // Remove 'data: ' prefix
          try {
            const event = JSON.parse(jsonStr) as StreamEvent;
            yield event;
          } catch (e) {
            console.error('Failed to parse SSE event:', jsonStr, e);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

