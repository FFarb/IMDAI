import { useState } from 'react';
import type { BriefValues } from './BriefCard';
import { ResearchBoard } from './ResearchBoard';
import { GalleryGrid } from './GalleryGrid';
import type { ImageResult, ResearchOutput, SynthesisOutput, SynthesisPrompt } from '../types/pipeline';

async function postJson<T>(url: string, payload: unknown): Promise<T> {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : 'Request failed';
    throw new Error(detail);
  }
  return data as T;
}

async function runResearch(brief: BriefValues): Promise<ResearchOutput> {
  return postJson<ResearchOutput>('/api/research', {
    topic: brief.topic,
    audience: brief.audience,
    age: brief.age,
    research_mode: brief.research_mode,
    model: brief.research_model,
    reasoning_effort: brief.reasoning_effort,
  });
}

async function runSynthesis(brief: BriefValues, research: ResearchOutput): Promise<SynthesisOutput> {
  return postJson<SynthesisOutput>('/api/synthesize', {
    research_text: research.analysis,
    audience: brief.audience,
    age: brief.age,
    variants: brief.variants,
    synthesis_mode: brief.synthesis_mode,
  });
}

async function runImageGeneration(brief: BriefValues, prompt: SynthesisPrompt): Promise<ImageResult[]> {
  const payload = await postJson<{ data: ImageResult[] }>('/api/images', {
    prompt_positive: prompt.positive,
    prompt_negative: prompt.negative,
    n: brief.images_per_prompt,
    model: brief.image_model,
    quality: brief.image_quality,
    size: brief.image_size,
  });
  return payload.data;
}

interface PromptTabsProps {
  brief: BriefValues;
  isBriefLoading: boolean;
  research: ResearchOutput | null;
  synthesis: SynthesisOutput | null;
  images: ImageResult[][];
  setResearch: (research: ResearchOutput | null) => void;
  setSynthesis: (synthesis: SynthesisOutput | null) => void;
  setImages: (images: ImageResult[][]) => void;
  onClearPipeline: () => void;
  autosave: boolean;
  setAutosave: (value: boolean) => void;
}

type TabName = 'research' | 'synthesis' | 'images';

const TABS: { id: TabName; label: string }[] = [
  { id: 'research', label: '1. Research' },
  { id: 'synthesis', label: '2. Prompt Builder' },
  { id: 'images', label: '3. Image Generation' },
];

export function PromptTabs({
  brief,
  isBriefLoading,
  research,
  synthesis,
  images,
  setResearch,
  setSynthesis,
  setImages,
  onClearPipeline,
  autosave,
}: PromptTabsProps) {
  const [activeTab, setActiveTab] = useState<TabName>('research');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPromptIndex, setSelectedPromptIndex] = useState(0);

  const downloadTextFile = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadImageFile = (b64Json: string, filename: string) => {
    const byteCharacters = atob(b64Json);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: 'image/png' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleResetPipeline = () => {
    onClearPipeline();
    setSelectedPromptIndex(0);
  };

  const handleRunResearch = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await runResearch(brief);
      setResearch(result);
      setSynthesis(null);
      setImages([]);
      setSelectedPromptIndex(0);
      setActiveTab('synthesis');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unable to run research');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSynthesize = async () => {
    if (!research) {
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const result = await runSynthesis(brief, research);
      setSynthesis(result);
      if (autosave) {
        result.prompts.forEach((prompt, index) => {
          const content = `Positive Prompt:\n${prompt.positive}\n\nNegative Prompts:\n${prompt.negative.join('\n')}`;
          downloadTextFile(content, `prompt_${index + 1}.txt`);
        });
      }
      setImages([]);
      setSelectedPromptIndex(0);
      setActiveTab('images');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unable to synthesize prompts');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateImages = async () => {
    if (!synthesis?.prompts.length) {
      return;
    }
    const prompt = synthesis.prompts[selectedPromptIndex];
    if (!prompt) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const result = await runImageGeneration(brief, prompt);
      if (autosave) {
        const promptNum = selectedPromptIndex + 1;
        const existingImageCount = images[selectedPromptIndex]?.length ?? 0;
        result.forEach((item, index) => {
          if (item.b64_json) {
            const imageNum = existingImageCount + index + 1;
            downloadImageFile(item.b64_json, `image_p${promptNum}_${imageNum}.png`);
          }
        });
      }
      const nextImages = images.slice();
      nextImages[selectedPromptIndex] = result;
      setImages(nextImages);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unable to generate images');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="card">
      <div className="tab-row">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
            disabled={isLoading}
          >
            {tab.label}
          </button>
        ))}
        <button type="button" className="secondary" onClick={handleResetPipeline} disabled={isLoading}>
          Clear Results
        </button>
      </div>

      {error ? <div className="error-box">{error}</div> : null}

      <div className="tab-content">
        {activeTab === 'research' && (
          <div>
            <div className="card-actions">
              <button
                type="button"
                className="primary"
                onClick={handleRunResearch}
                disabled={isLoading || isBriefLoading || !brief.topic.trim()}
              >
                {isLoading ? 'Researching…' : 'Run Research'}
              </button>
            </div>
            <ResearchBoard research={research} />
          </div>
        )}

        {activeTab === 'synthesis' && (
          <div>
            <div className="card-actions">
              <button
                type="button"
                className="primary"
                onClick={handleSynthesize}
                disabled={isLoading || !research}
              >
                {isLoading ? 'Synthesizing…' : 'Synthesize Prompts'}
              </button>
            </div>
            <ResearchBoard research={research} />
            {synthesis ? (
              <div className="synthesis-preview">
                <h3>Prompt Variants</h3>
                <ul>
                  {synthesis.prompts.map((prompt, index) => (
                    <li key={`prompt-${index}`}>
                      <strong>{`Prompt ${index + 1}`}:</strong> {prompt.positive}
                    </li>
                  ))}
                </ul>
                <details className="raw-text-preview">
                  <summary>View raw prompt text</summary>
                  <pre>{synthesis.raw_text}</pre>
                </details>
              </div>
            ) : null}
          </div>
        )}

        {activeTab === 'images' && (
          <div>
            <div className="card-actions">
              <select
                value={selectedPromptIndex}
                onChange={(event) => setSelectedPromptIndex(Number(event.target.value))}
                disabled={isLoading || !synthesis?.prompts.length}
              >
                {synthesis?.prompts.map((_, index) => (
                  <option key={`prompt-option-${index}`} value={index}>
                    {`Prompt ${index + 1}`}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="primary"
                onClick={handleGenerateImages}
                disabled={isLoading || !synthesis?.prompts.length}
              >
                {isLoading ? 'Generating…' : `Generate Images (${brief.imagesPerPrompt})`}
              </button>
            </div>
            <GalleryGrid prompts={synthesis?.prompts ?? null} images={images} isLoading={isLoading} />
          </div>
        )}
      </div>
    </section>
  );
}
