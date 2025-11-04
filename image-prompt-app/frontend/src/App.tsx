import { useState } from 'react';
import usePipelineStore from './store/pipeline';
import { BriefCard, type BriefValues } from './components/BriefCard';
import { PromptTabs } from './components/PromptTabs';

// Set the initial state for the brief
const defaultBrief: BriefValues = {
  topic: 'Friendly dinosaurs for classroom posters',
  audience: 'Elementary school children',
  age: '6-9 years',
  depth: 3,
  variants: 2,
  imagesPerPrompt: 1,
};

function App() {
  // The brief's state is managed locally in the App component
  const [brief, setBrief] = useState<BriefValues>(defaultBrief);
  const [isBriefLoading, setIsBriefLoading] = useState(false);

  // All other pipeline state is now managed by the Zustand store
  const { clearState } = usePipelineStore();

  const handleBriefChange = (changes: Partial<BriefValues>) => {
    setBrief((prev) => ({ ...prev, ...changes }));
  };

  const handleReset = () => {
    setBrief(defaultBrief);
    clearState();
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
        <BriefCard
          values={brief}
          onChange={handleBriefChange}
          isLoading={isBriefLoading}
        />

        {/* The PromptTabs component now orchestrates the entire pipeline UI */}
        <PromptTabs
          brief={brief}
          isBriefLoading={isBriefLoading}
        />
      </main>
    </div>
  );
}

export default App;
