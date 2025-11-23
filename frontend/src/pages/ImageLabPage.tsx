import { useEffect, useState } from 'react';

import { AgentThoughtChain } from '../components/AgentThoughtChain';
import { BriefCard } from '../components/BriefCard';
import { ImageUpload } from '../components/ImageUpload';
import { PromptTabs } from '../components/PromptTabs';
import type { BriefValues, ResearchOutput, StreamEvent, SynthesisOutput } from '../types/pipeline';

const defaultBrief: BriefValues = {
  topic: 'Friendly dinosaurs for classroom posters',
  audience: 'Elementary school children',
  age: '6-9 years',
  variants: 3,
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

  // Multi-agent state
  const [agentEvents, setAgentEvents] = useState<StreamEvent[]>([]);
  const [isAgentActive, setIsAgentActive] = useState(false);

  useEffect(() => {
    // Exclude visual_references (large base64 data) from localStorage to avoid quota errors
    const { visual_references, ...rest } = brief;
    localStorage.setItem('brief', JSON.stringify(rest));
  }, [brief]);

  useEffect(() => {
    localStorage.setItem('research', JSON.stringify(research));
  }, [research]);

  useEffect(() => {
    localStorage.setItem('synthesis', JSON.stringify(synthesis));
  }, [synthesis]);

  const handleBriefChange = (changes: Partial<BriefValues>) => {
    setBrief((prev) => ({ ...prev, ...changes }));
  };

  const handleImagesChange = (newImages: string[]) => {
    setBrief((prev) => ({ ...prev, visual_references: newImages }));
  };

  const resetPipelineState = () => {
    setResearch(null);
    setSynthesis(null);
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
          onClearPipeline={resetPipelineState}
        />
      </div>
    </div>
  );
}
