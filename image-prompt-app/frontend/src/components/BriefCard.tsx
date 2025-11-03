import type { ChangeEvent } from 'react';

import type { GenerateMode } from '../types/pipeline';

const audienceOptions: { label: string; value: string }[] = [
  { label: 'Kids', value: 'kids' },
  { label: 'Teens', value: 'teens' },
  { label: 'Adults', value: 'adults' },
  { label: 'Professionals', value: 'professionals' },
];

const ageOptions = ['3-5', '6-9', '10-13', '14-18', '18+'];

export type BriefValues = {
  topic: string;
  audience: string;
  age: string;
  depth: number;
  variants: number;
  imagesPerPrompt: number;
};

interface BriefCardProps {
  values: BriefValues;
  onChange: (changes: Partial<BriefValues>) => void;
  onSubmit: (mode: GenerateMode) => void;
  isLoading: boolean;
}

export function BriefCard({ values, onChange, onSubmit, isLoading }: BriefCardProps) {
  const handleAudienceChip = (value: string) => {
    onChange({ audience: value });
  };

  const handleAgeChip = (value: string) => {
    onChange({ age: value });
  };

  const handleInput = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = event.target;
    if (name === 'topic') {
      onChange({ topic: value });
    }
    if (name === 'audience') {
      onChange({ audience: value });
    }
    if (name === 'age') {
      onChange({ age: value });
    }
    if (name === 'variants') {
      onChange({ variants: Number(value) });
    }
    if (name === 'imagesPerPrompt') {
      onChange({ imagesPerPrompt: Number(value) });
    }
  };

  const handleDepthChange = (event: ChangeEvent<HTMLInputElement>) => {
    onChange({ depth: Number(event.target.value) });
  };

  return (
    <section className="card">
      <header className="card-header">
        <div>
          <h2>Brief</h2>
          <p className="card-subtitle">Define the creative space for research, synthesis, and images.</p>
        </div>
        <div className="card-actions">
          <button
            type="button"
            className="primary"
            onClick={() => onSubmit('full')}
            disabled={isLoading || !values.topic.trim()}
          >
            {isLoading ? 'Working…' : 'Generate'}
          </button>
          <button type="button" onClick={() => onSubmit('research_only')} disabled={isLoading}>
            Re-run Research
          </button>
          <button type="button" onClick={() => onSubmit('synthesis_only')} disabled={isLoading}>
            Synthesize
          </button>
        </div>
      </header>

      <div className="field-grid">
        <label className="field">
          <span>Topic</span>
          <textarea
            name="topic"
            value={values.topic}
            onChange={handleInput}
            placeholder="e.g. Friendly dinosaurs for classroom posters"
            rows={3}
          />
        </label>

        <label className="field">
          <span>Audience</span>
          <div className="chip-row">
            {audienceOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                className={`chip ${values.audience === option.value ? 'active' : ''}`}
                onClick={() => handleAudienceChip(option.value)}
              >
                {option.label}
              </button>
            ))}
          </div>
          <input
            name="audience"
            value={values.audience}
            onChange={handleInput}
            placeholder="Custom audience"
          />
        </label>

        <label className="field">
          <span>Age</span>
          <div className="chip-row">
            {ageOptions.map((option) => (
              <button
                key={option}
                type="button"
                className={`chip ${values.age === option ? 'active' : ''}`}
                onClick={() => handleAgeChip(option)}
              >
                {option}
              </button>
            ))}
          </div>
          <input name="age" value={values.age} onChange={handleInput} placeholder="Custom age" />
        </label>

        <label className="field slider">
          <span>Depth: {values.depth}</span>
          <input type="range" min={1} max={5} step={1} value={values.depth} onChange={handleDepthChange} />
        </label>

        <label className="field">
          <span>Variants</span>
          <input
            type="number"
            min={1}
            max={5}
            name="variants"
            value={values.variants}
            onChange={handleInput}
          />
        </label>

        <label className="field">
          <span>Images per prompt</span>
          <input
            type="number"
            min={1}
            max={4}
            name="imagesPerPrompt"
            value={values.imagesPerPrompt}
            onChange={handleInput}
          />
        </label>
      </div>
    </section>
  );
}
