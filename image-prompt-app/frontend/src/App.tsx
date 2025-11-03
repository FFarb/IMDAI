import { useCallback, useEffect, useMemo, useState } from 'react';

import { generatePipeline } from './api/generate';
import { BriefCard, type BriefValues } from './components/BriefCard';
import { GalleryGrid } from './components/GalleryGrid';
import { PromptTabs } from './components/PromptTabs';
import { ResearchBoard } from './components/ResearchBoard';
import type {
  GenerateMode,
  GenerateRequest,
  GenerateResponse,
  ImageResult,
  ResearchOutput,
  SynthPrompt,
  SynthesisOutput,
} from './types/pipeline';

const defaultBrief: BriefValues = {
  topic: '',
  audience: 'kids',
  age: '6-9',
  depth: 3,
  variants: 2,
  imagesPerPrompt: 1,
};

function App() {
  const [brief, setBrief] = useState<BriefValues>(defaultBrief);
  const [research, setResearch] = useState<ResearchOutput | null>(null);
  const [synthesis, setSynthesis] = useState<SynthesisOutput | null>(null);
  const [images, setImages] = useState<ImageResult[][] | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!message && !error) return;
    const timer = window.setTimeout(() => {
      setMessage(null);
      setError(null);
    }, 4000);
    return () => window.clearTimeout(timer);
  }, [message, error]);

  const handleBriefChange = (changes: Partial<BriefValues>) => {
    setBrief((prev) => ({ ...prev, ...changes }));
  };

  const ensureImagesArray = useCallback(
    (promptCount: number) => Array.from({ length: promptCount }, (_, idx) => images?.[idx] ?? []),
    [images],
  );

  const applyPipelineResponse = useCallback(
    (response: GenerateResponse, mode: GenerateMode, promptIndex?: number, appendImages?: boolean) => {
      if (mode === 'research_only') {
        setResearch(response.research);
        setSynthesis(null);
        setImages(null);
        setMessage('Research refreshed.');
        return;
      }

      if (mode === 'synthesis_only') {
        if (response.research) {
          setResearch(response.research);
        }
        setSynthesis(response.synthesis);
        setImages(null);
        setMessage('Synthesis ready.');
        return;
      }

      if (mode === 'images_only') {
        if (!synthesis && response.synthesis) {
          setSynthesis(response.synthesis);
        }
        if (!synthesis && !response.synthesis) {
          return;
        }
        const effectivePrompts = response.synthesis?.prompts ?? synthesis?.prompts ?? [];
        const updated = ensureImagesArray(effectivePrompts.length);
        const newImages = response.images?.[0] ?? [];
        if (typeof promptIndex === 'number') {
          updated[promptIndex] = appendImages ? [...updated[promptIndex], ...newImages] : newImages;
        }
        setImages(updated);
        setMessage('Images generated.');
        return;
      }

      setResearch(response.research);
      setSynthesis(response.synthesis);
      setImages(response.images);
      setMessage('Full pipeline complete.');
    },
    [ensureImagesArray, synthesis],
  );

  const handlePipeline = useCallback(
    async (mode: GenerateMode, promptIndex?: number, appendImages?: boolean) => {
      setIsLoading(true);
      setError(null);
      try {
        const payload: GenerateRequest = {
          topic: brief.topic,
          audience: brief.audience,
          age: brief.age,
          depth: brief.depth,
          variants: brief.variants,
          images_per_prompt: brief.imagesPerPrompt,
          mode,
        };

        if (['synthesis_only', 'images_only', 'full'].includes(mode) && research) {
          payload.research = research;
        }
        if (mode === 'images_only') {
          if (synthesis) {
            payload.synthesis = synthesis;
          }
          if (typeof promptIndex === 'number') {
            payload.selected_prompt_index = promptIndex;
          } else {
            throw new Error('Select a prompt before requesting images.');
          }
        }

        const response = await generatePipeline(payload);
        applyPipelineResponse(response, mode, promptIndex, appendImages);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unexpected error';
        setError(message);
      } finally {
        setIsLoading(false);
      }
    },
    [applyPipelineResponse, brief, research, synthesis],
  );

  const handlePromptChange = (index: number, prompt: SynthPrompt) => {
    setSynthesis((prev) => {
      if (!prev) return prev;
      const updated = [...prev.prompts];
      updated[index] = prompt;
      return { prompts: updated };
    });
  };

  const handleCopyPrompt = async (index: number) => {
    const prompt = synthesis?.prompts[index];
    if (!prompt) return;
    const text = `${prompt.title ? `${prompt.title}\n` : ''}${prompt.positive}\n\nNegative: ${prompt.negative.join(', ')}`;
    await navigator.clipboard.writeText(text);
    setMessage('Prompt copied to clipboard.');
  };

  const handleSavePrompt = (index: number) => {
    const prompt = synthesis?.prompts[index];
    if (!prompt) return;
    const key = `imdai_prompt_${index}`;
    window.localStorage.setItem(key, JSON.stringify(prompt));
    setMessage('Prompt saved locally.');
  };

  const handleDownloadImage = (promptIndex: number, imageIndex: number) => {
    const image = images?.[promptIndex]?.[imageIndex];
    if (!image) return;
    const filename = `imdai_prompt${promptIndex + 1}_image${imageIndex + 1}.png`;
    const link = document.createElement('a');
    if (image.url) {
      link.href = image.url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.click();
      return;
    }
    if (image.b64_json) {
      link.href = `data:image/png;base64,${image.b64_json}`;
      link.download = filename;
      link.click();
    }
  };

  const synthesisPrompts = useMemo(() => synthesis?.prompts ?? [], [synthesis]);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>IMDAI Image Prompt Lab</h1>
          <p>Research → Synthesis → Images in a single streamlined flow.</p>
        </div>
        {(message || error) && <div className={`toast ${error ? 'error' : 'success'}`}>{error ?? message}</div>}
      </header>

      <main className="app-main">
        <BriefCard values={brief} onChange={handleBriefChange} onSubmit={(mode) => handlePipeline(mode)} isLoading={isLoading} />
        <ResearchBoard research={research} />
        <PromptTabs
          synthesis={synthesis}
          imagesPerPrompt={brief.imagesPerPrompt}
          onPromptChange={handlePromptChange}
          onGenerateImages={(index, append) => handlePipeline('images_only', index, append)}
          onCopyPrompt={handleCopyPrompt}
          onSavePrompt={handleSavePrompt}
          isLoading={isLoading}
        />
        <GalleryGrid
          images={images}
          prompts={synthesisPrompts}
          onGenerateImages={(index, append) => handlePipeline('images_only', index, append)}
          onCopyPrompt={handleCopyPrompt}
          onDownloadImage={handleDownloadImage}
          isLoading={isLoading}
        />
      </main>
    </div>
  );
}

export default App;
