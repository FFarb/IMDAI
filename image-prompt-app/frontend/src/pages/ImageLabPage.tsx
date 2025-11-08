import { useEffect, useState } from 'react';

import { BriefCard } from '../components/BriefCard';
import { PromptTabs } from '../components/PromptTabs';
import type { BriefValues, ImageResult, ResearchOutput, SynthesisOutput } from '../types/pipeline';

const defaultBrief: BriefValues = {
  topic: 'Friendly dinosaurs for classroom posters',
  audience: 'Elementary school children',
  age: '6-9 years',
  variants: 2,
  images_per_prompt: 1,

  // Research
  research_model: 'gpt-4o-mini-2024-07-18',
  research_mode: 'quick',
  reasoning_effort: 'auto',

  // Synthesis
  synthesis_mode: 'creative',

  // Image
  image_model: 'dall-e-3',
  image_quality: 'standard',
  image_size: '1024x1024',
};

export function ImageLabPage(): JSX.Element {
  const [brief, setBrief] = useState<BriefValues>(() => {
    const saved = localStorage.getItem('brief');
    const parsed = saved ? JSON.parse(saved) : {};
    return { ...defaultBrief, ...parsed };
  });
  const [isBriefLoading] = useState(false);
  const [research, setResearch] = useState<ResearchOutput | null>(() => {
    const saved = localStorage.getItem('research');
    return saved ? JSON.parse(saved) : null;
  });
  const [synthesis, setSynthesis] = useState<SynthesisOutput | null>(() => {
    const saved = localStorage.getItem('synthesis');
    return saved ? JSON.parse(saved) : null;
  });
  const [images, setImages] = useState<ImageResult[][]>(() => {
    const saved = localStorage.getItem('images');
    return saved ? JSON.parse(saved) : [];
  });
  const [autosave, setAutosave] = useState<boolean>(() => {
    const saved = localStorage.getItem('autosave');
    return saved ? JSON.parse(saved) : false;
  });

  useEffect(() => {
    localStorage.setItem('brief', JSON.stringify(brief));
  }, [brief]);

  useEffect(() => {
    localStorage.setItem('research', JSON.stringify(research));
  }, [research]);

  useEffect(() => {
    localStorage.setItem('synthesis', JSON.stringify(synthesis));
  }, [synthesis]);

  useEffect(() => {
    localStorage.setItem('images', JSON.stringify(images));
  }, [images]);

  useEffect(() => {
    localStorage.setItem('autosave', JSON.stringify(autosave));
  }, [autosave]);

  const handleBriefChange = (changes: Partial<BriefValues>) => {
    setBrief((prev) => ({ ...prev, ...changes }));
  };

  const resetPipelineState = () => {
    setResearch(null);
    setSynthesis(null);
    setImages([]);
  };

  const handleReset = () => {
    setBrief(defaultBrief);
    resetPipelineState();
  };

  return (
    <div className="image-lab-page">
      <header className="app-header">
        <div>
          <h1>IMDAI Image Prompt Lab</h1>
          <p>A streamlined workflow for generating creative image prompts.</p>
        </div>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div className="autosave-group">
            <label className="autosave-toggle">
              <input
                type="checkbox"
                checked={autosave}
                onChange={(e) => setAutosave(e.target.checked)}
              />
              Autosave
            </label>
            <p className="field-hint">Saves generated files to your browser's Downloads folder.</p>
          </div>
          <button onClick={handleReset} className="secondary">Reset State</button>
        </div>
      </header>

      <div className="image-lab-content">
        <BriefCard values={brief} onChange={handleBriefChange} isLoading={isBriefLoading} />

        <PromptTabs
          brief={brief}
          isBriefLoading={isBriefLoading}
          research={research}
          synthesis={synthesis}
          images={images}
          setResearch={setResearch}
          setSynthesis={setSynthesis}
          setImages={setImages}
          onClearPipeline={resetPipelineState}
          autosave={autosave}
          setAutosave={setAutosave}
        />
      </div>
    </div>
  );
}
