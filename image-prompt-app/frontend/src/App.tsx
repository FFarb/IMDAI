import { useEffect, useState } from 'react';
import { BriefCard, type BriefValues } from './components/BriefCard';
import { PromptTabs } from './components/PromptTabs';
import type { ImageResult, ResearchOutput, SynthesisOutput } from './types/pipeline';

const defaultBrief: BriefValues = {
  topic: 'Friendly dinosaurs for classroom posters',
  audience: 'Elementary school children',
  age: '6-9 years',
  depth: 3,
  variants: 2,
  imagesPerPrompt: 1,
};

function App() {
  const [brief, setBrief] = useState<BriefValues>(() => {
    const saved = localStorage.getItem('brief');
    return saved ? JSON.parse(saved) : defaultBrief;
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
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>IMDAI Image Prompt Lab</h1>
          <p>A streamlined workflow for generating creative image prompts.</p>
        </div>
        <button onClick={handleReset} className="secondary">Reset State</button>
      </header>

      <main className="app-main">
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
        />
      </main>
    </div>
  );
}

export default App;
