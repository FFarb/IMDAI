import type { GenerateRequest, GenerateResponse, AgentGenerateResponse, StreamEvent } from '../types/pipeline';

// Helper to convert base64 to Blob safely (Manual implementation for stability)
function b64toBlob(b64Data: string, contentType = 'image/png'): Blob {
  const byteCharacters = atob(b64Data);
  const byteArrays = [];
  const sliceSize = 512;

  for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
    const slice = byteCharacters.slice(offset, offset + sliceSize);
    const byteNumbers = new Array(slice.length);
    for (let i = 0; i < slice.length; i++) {
      byteNumbers[i] = slice.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    byteArrays.push(byteArray);
  }

  return new Blob(byteArrays, { type: contentType });
}

export async function generatePipeline(payload: GenerateRequest): Promise<GenerateResponse | AgentGenerateResponse> {
  const response = await fetch('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => null);
  if (!response.ok || !data) {
    const detail = typeof data?.detail === 'string' ? data.detail : 'Request failed or returned no data';
    throw new Error(detail);
  }

  // Post-process images to use Blob URLs immediately
  // This prevents keeping massive base64  // Post-process images to use Blob URLs immediately
  if (data && data.images) {

    // Process sequentially to avoid memory spikes
    for (let pIndex = 0; pIndex < data.images.length; pIndex++) {
      const promptImages = data.images[pIndex];
      if (!Array.isArray(promptImages)) {
        console.warn('[generatePipeline] Skipping non-array prompt images at index', pIndex);
        continue;
      }


      for (let iIndex = 0; iIndex < promptImages.length; iIndex++) {
        const img = promptImages[iIndex];
        if (img.b64_json) {
          try {

            // Use manual conversion (synchronous but robust)
            const blob = b64toBlob(img.b64_json);
            const url = URL.createObjectURL(blob);


            img.url = url;
            // CRITICAL: Remove the heavy base64 string immediately
            delete img.b64_json;


          } catch (e) {
            console.error(`[generatePipeline] Failed to convert image ${pIndex}-${iIndex}:`, e);
            img.error = 'Failed to process image data';
            delete img.b64_json;
          }
        } else if (img.url) {

        } else {
          console.warn(`[generatePipeline] Image ${pIndex}-${iIndex} has no b64_json or url`);
        }
      }
    }

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

