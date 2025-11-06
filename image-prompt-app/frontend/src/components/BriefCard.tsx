import type { ChangeEvent } from 'react';

export type BriefValues = {
  topic: string;
  audience: string;
  age: string;
  depth: number;
  variants: number;
  imagesPerPrompt: number;
  research_model: string;
  reasoning_effort: string;
};

interface BriefCardProps {
  values: BriefValues;
  onChange: (changes: Partial<BriefValues>) => void;
  isLoading: boolean;
}

export function BriefCard({ values, onChange, isLoading }: BriefCardProps) {
  const handleInput = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = event.target;
    const isNumber = type === 'number' || type === 'range';
    onChange({ [name]: isNumber ? Number(value) : value });
  };

  const handleSelect = (event: ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = event.target;
    onChange({ [name]: value });
  };

  return (
    <section className="card">
      <header className="card-header">
        <div>
          <h2>Creative Brief</h2>
          <p className="card-subtitle">Define the core concept for the project.</p>
        </div>
      </header>

      <div className="field-grid">
        <label className="field">
          <span>Topic</span>
          <textarea
            name="topic"
            value={values.topic}
            onChange={handleInput}
            placeholder="e.g., Friendly dinosaurs for classroom posters"
            rows={3}
            disabled={isLoading}
          />
        </label>

        <label className="field">
          <span>Audience</span>
          <input
            type="text"
            name="audience"
            value={values.audience}
            onChange={handleInput}
            placeholder="e.g., Elementary school children"
            disabled={isLoading}
          />
        </label>

        <label className="field">
          <span>Age</span>
          <input
            type="text"
            name="age"
            value={values.age}
            onChange={handleInput}
            placeholder="e.g., 6-9 years"
            disabled={isLoading}
          />
        </label>

        <label className="field slider">
          <span>Research Depth: {values.depth}</span>
          <input
            type="range"
            name="depth"
            min={1}
            max={5}
            step={1}
            value={values.depth}
            onChange={handleInput}
            disabled={isLoading}
          />
        </label>

        <label className="field">
          <span>Prompt Variants</span>
           <input
            type="number"
            name="variants"
            min={1}
            max={5}
            value={values.variants}
            onChange={handleInput}
            disabled={isLoading}
          />
        </label>

        <label className="field">
          <span>Images per Prompt</span>
          <input
            type="number"
            name="imagesPerPrompt"
            min={1}
            max={4}
            value={values.imagesPerPrompt}
            onChange={handleInput}
            disabled={isLoading}
          />
        </label>

        <label className="field">
          <span>Research Model</span>
          <select
            name="research_model"
            value={values.research_model}
            onChange={handleSelect}
            disabled={isLoading}
          >
            <option value="gpt-4o-mini-2024-07-18">GPT-4o Mini</option>
            <option value="gpt-5">GPT-5</option>
            <option value="gpt-5-mini">GPT-5 Mini</option>
            <option value="gpt-5-nano">GPT-5 Nano</option>
          </select>
        </label>

        <label className="field">
          <span>Reasoning Effort</span>
          <select
            name="reasoning_effort"
            value={values.reasoning_effort}
            onChange={handleSelect}
            disabled={isLoading}
          >
            <option value="auto">Auto</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </label>
      </div>
    </section>
  );
}
