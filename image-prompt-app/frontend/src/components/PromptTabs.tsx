import { useState } from 'react';
import type { BriefValues } from './BriefCard';
import { ResearchBoard } from './ResearchBoard';
import { GalleryGrid } from './GalleryGrid';
import type {
  ImageResult,
  ResearchOutput,
  SynthesisOutput,
  SynthesisPrompt,
} from '../types/pipeline';

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
    depth: brief.depth,
  });
}

async function runSynthesis(brief: BriefValues, research: ResearchOutput): Promise<SynthesisOutput> {
  return postJson<SynthesisOutput>('/api/synthesize', {
    research,
    audience: brief.audience,
    age: brief.age,
    variants: brief.variants,
  });
}

async function runImageGeneration(prompt: SynthesisPrompt, count: number): Promise<ImageResult[]> {
  const payload = await postJson<{ data: ImageResult[] }>('/api/images', {
    prompt_positive: prompt.positive,
    prompt_negative: prompt.negative,
    n: count,
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
}: PromptTabsProps) {
  const [activeTab, setActiveTab] = useState<TabName>('research');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPromptIndex, setSelectedPromptIndex] = useState(0);

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
      const result = await runImageGeneration(prompt, brief.imagesPerPrompt);
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
                      <strong>{prompt.title || `Prompt ${index + 1}`}:</strong> {prompt.positive}
                    </li>
                  ))}
                </ul>
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
                {synthesis?.prompts.map((prompt, index) => (
                  <option key={`prompt-option-${index}`} value={index}>
                    {prompt.title || `Prompt ${index + 1}`}
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
