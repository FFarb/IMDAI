import { useState } from 'react';
import usePipelineStore from '../store/pipeline';
import type { BriefValues } from './BriefCard';
import { ResearchBoard } from './ResearchBoard';
import { GalleryGrid } from './GalleryGrid';
import { SynthesisPrompt } from '../types/pipeline';

// API call functions (could be moved to a dedicated api.ts file)
async function runResearch(brief: BriefValues) {
  const response = await fetch('/api/research', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      topic: brief.topic,
      audience: brief.audience,
      age: brief.age,
      depth: brief.depth,
    }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Research request failed');
  }
  return response.json();
}

async function runSynthesis(brief: BriefValues, researchData: any) {
  const response = await fetch('/api/synthesize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      research: researchData,
      audience: brief.audience,
      age: brief.age,
      variants: brief.variants,
    }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Synthesis request failed');
  }
  return response.json();
}

async function runImageGeneration(prompt: SynthesisPrompt, count: number) {
  const response = await fetch('/api/images', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt_positive: prompt.positive,
      prompt_negative: prompt.negative,
      n: count,
    }),
  });
   if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Image generation failed');
  }
  return response.json();
}


interface PromptTabsProps {
  brief: BriefValues;
  isBriefLoading: boolean;
}

type TabName = 'research' | 'synthesis' | 'images';

export function PromptTabs({ brief, isBriefLoading }: PromptTabsProps) {
  const [activeTab, setActiveTab] = useState<TabName>('research');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { research, synthesis, images, setResearch, setSynthesis, setImages } = usePipelineStore();
  const [selectedPromptIndex, setSelectedPromptIndex] = useState(0);

  const handleRunResearch = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await runResearch(brief);
      setResearch(result);
      setActiveTab('synthesis'); // Move to next tab on success
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSynthesize = async () => {
    if (!research) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await runSynthesis(brief, research);
      setSynthesis(result);
      setActiveTab('images'); // Move to next tab
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!synthesis || !synthesis.prompts[selectedPromptIndex]) return;
    setIsLoading(true);
    setError(null);
    try {
      const prompt = synthesis.prompts[selectedPromptIndex];
      const result = await runImageGeneration(prompt, brief.imagesPerPrompt);
      // Assuming result.images is an array of {url} or {b64_json}
      const imageUrls = result.images.map((img: any) => img.url || `data:image/jpeg;base64,${img.b64_json}`);
      const newImages = [...images];
      newImages[selectedPromptIndex] = imageUrls;
      setImages(newImages);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const TABS: { id: TabName; label: string }[] = [
    { id: 'research', label: '1. Research' },
    { id: 'synthesis', label: '2. Prompt Builder' },
    { id: 'images', label: '3. Image Generation' },
  ];

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
      </div>

      {error && <div className="error-box">{error}</div>}

      <div className="tab-content">
        {activeTab === 'research' && (
          <div>
            <div className="card-actions">
              <button onClick={handleRunResearch} disabled={isLoading || isBriefLoading || !brief.topic.trim()} className="primary">
                {isLoading ? 'Researching...' : 'Run Research'}
              </button>
            </div>
            {research && <ResearchBoard research={research} />}
          </div>
        )}

        {activeTab === 'synthesis' && (
          <div>
            <div className="card-actions">
               <button onClick={handleSynthesize} disabled={isLoading || !research} className="primary">
                {isLoading ? 'Synthesizing...' : 'Synthesize Prompts'}
              </button>
            </div>
            {research && <textarea readOnly value={JSON.stringify(research, null, 2)} rows={10} style={{ width: '100%', resize: 'vertical' }} />}
            {synthesis && (
              <div>
                <h3>Synthesized Prompts:</h3>
                <ul>
                  {synthesis.prompts.map((p, i) => <li key={i}><strong>{p.title || `Prompt ${i+1}`}:</strong> {p.positive}</li>)}
                </ul>
              </div>
            )}
          </div>
        )}

        {activeTab === 'images' && (
          <div>
            <div className="card-actions">
               <button onClick={handleGenerate} disabled={isLoading || !synthesis?.prompts.length} className="primary">
                 {isLoading ? 'Generating...' : `Generate Images (${brief.imagesPerPrompt})`}
              </button>
            </div>
             {synthesis && synthesis.prompts.length > 0 && (
              <select value={selectedPromptIndex} onChange={(e) => setSelectedPromptIndex(Number(e.target.value))} disabled={isLoading}>
                {synthesis.prompts.map((p, i) => <option key={i} value={i}>{p.title || `Prompt ${i+1}`}</option>)}
              </select>
            )}
            <GalleryGrid images={images} />
          </div>
        )}
      </div>
    </section>
  );
}
