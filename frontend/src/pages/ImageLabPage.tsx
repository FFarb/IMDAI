import { useEffect, useState } from 'react';

import { AgentThoughtChain } from '../components/AgentThoughtChain';
import { BriefCard } from '../components/BriefCard';
import { ImageUpload } from '../components/ImageUpload';
import { PromptTabs } from '../components/PromptTabs';
import type { BriefValues, ImageResult, ResearchOutput, StreamEvent, SynthesisOutput } from '../types/pipeline';

const defaultBrief: BriefValues = {
  topic: 'Friendly dinosaurs for classroom posters',
  audience: 'Elementary school children',
  age: '6-9 years',
  variants: 2,
  images_per_prompt: 1,

  // Multi-agent
  use_agents: false,
  visual_references: [],
  max_iterations: 3,

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

  // Multi-agent state
  const [agentEvents, setAgentEvents] = useState<StreamEvent[]>([]);
  const [isAgentActive, setIsAgentActive] = useState(false);

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

  const handleImagesChange = (newImages: string[]) => {
    setBrief((prev) => ({ ...prev, visual_references: newImages }));
  };

  const resetPipelineState = () => {
    setResearch(null);
    setSynthesis(null);
    setImages([]);
    setAgentEvents([]);
    setIsAgentActive(false);
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
          <p>AI-Powered Image Generation with Multi-Agent Intelligence</p>
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
        {/* Multi-Agent Toggle */}
        <div className="agent-toggle-card">
          <label className="agent-toggle">
            <input
              type="checkbox"
              checked={brief.use_agents || false}
              onChange={(e) => handleBriefChange({ use_agents: e.target.checked })}
            />
            <div className="toggle-content">
              <strong>🤖 Use Multi-Agent System</strong>
              <p>Enable collaborative AI agents for enhanced prompt generation</p>
            </div>
          </label>
        </div>

        {/* Image Upload (only shown when agents are enabled) */}
        {brief.use_agents && (
          <ImageUpload
            images={brief.visual_references || []}
            onImagesChange={handleImagesChange}
          />
        )}

        {/* Agent Thought Chain (only shown when agents are active or have events) */}
        {brief.use_agents && (agentEvents.length > 0 || isAgentActive) && (
          <AgentThoughtChain events={agentEvents} isActive={isAgentActive} />
        )}

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
          agentEvents={agentEvents}
          setAgentEvents={setAgentEvents}
          isAgentActive={isAgentActive}
          setIsAgentActive={setIsAgentActive}
        />
      </div>
    </div>
  );
}

