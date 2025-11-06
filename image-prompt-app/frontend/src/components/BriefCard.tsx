import { useState, useEffect, type ChangeEvent } from 'react';
import type { BriefValues } from '../types/pipeline';

// Constants for UI options
const RESEARCH_MODES = [
  { id: 'quick', label: 'Quick' },
  { id: 'deep', label: 'Deep' },
  { id: 'expert', label: 'Expert' },
];

const SYNTHESIS_MODES = [
  { id: 'creative', label: 'Creative' },
  { id: 'technical', label: 'Technical' },
  { id: 'minimal', label: 'Minimal' },
];

const RESEARCH_MODELS = [
  { id: 'gpt-4o-mini-2024-07-18', label: 'GPT-4o Mini' },
  { id: 'gpt-5', label: 'GPT-5' },
  { id: 'gpt-5-mini', label: 'GPT-5 Mini' },
  { id: 'gpt-5-nano', label: 'GPT-5 Nano' },
];

const REASONING_EFFORT = [
  { id: 'auto', label: 'Auto' },
  { id: 'low', label: 'Low' },
  { id: 'medium', label: 'Medium' },
  { id: 'high', label: 'High' },
];

const IMAGE_MODELS = [
  { id: 'dall-e-3', label: 'DALL-E 3' },
  { id: 'dall-e-2', label: 'DALL-E 2' },
];

const IMAGE_CONSTRAINTS = {
  'dall-e-3': {
    quality: ['standard', 'hd'],
    size: ['1024x1024', '1792x1024', '1024x1792'],
  },
  'dall-e-2': {
    quality: ['standard'],
    size: ['256x256', '512x512', '1024x1024'],
  },
};


interface BriefCardProps {
  values: BriefValues;
  onChange: (changes: Partial<BriefValues>) => void;
  isLoading: boolean;
}

export function BriefCard({ values, onChange, isLoading }: BriefCardProps) {
  // State for dynamic dropdowns
  const [imageQualityOptions, setImageQualityOptions] = useState<string[]>([]);
  const [imageSizeOptions, setImageSizeOptions] = useState<string[]>([]);

  useEffect(() => {
    const model = values.image_model || 'dall-e-3';
    if (model in IMAGE_CONSTRAINTS) {
      const constraints = IMAGE_CONSTRAINTS[model as keyof typeof IMAGE_CONSTRAINTS];
      setImageQualityOptions(constraints.quality);
      setImageSizeOptions(constraints.size);

      // Reset to default if current value is not supported
      if (!constraints.quality.includes(values.image_quality || '')) {
        onChange({ image_quality: constraints.quality[0] });
      }
      if (!constraints.size.includes(values.image_size || '')) {
        onChange({ image_size: constraints.size[0] });
      }
    }
  }, [values.image_model, values.image_quality, values.image_size, onChange]);


  const handleInput = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = event.target;
    // Check if the element is a number input
    const isNumber = type === 'number' || (event.target as HTMLInputElement).type === 'range';
    onChange({ [name]: isNumber ? Number(value) : value });
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
            value={values.age || ''}
            onChange={handleInput}
            placeholder="e.g., 6-9 years"
            disabled={isLoading}
          />
        </label>

        {/* New Research Mode Selector */}
        <label className="field">
          <span>Research Mode</span>
          <select
            name="research_mode"
            value={values.research_mode}
            onChange={handleInput}
            disabled={isLoading}
          >
            {RESEARCH_MODES.map((mode) => (
              <option key={mode.id} value={mode.id}>{mode.label}</option>
            ))}
          </select>
        </label>

        {/* Updated Research Model Selector */}
        <label className="field">
          <span>Research Model</span>
          <select
            name="research_model"
            value={values.research_model}
            onChange={handleInput}
            disabled={isLoading}
          >
            {RESEARCH_MODELS.map((model) => (
              <option key={model.id} value={model.id}>{model.label}</option>
            ))}
          </select>
        </label>

        {/* Conditional Reasoning Effort Selector */}
        {values.research_model?.includes('gpt-5') && (
          <label className="field">
            <span>Reasoning Effort</span>
            <select
              name="reasoning_effort"
              value={values.reasoning_effort}
              onChange={handleInput}
              disabled={isLoading}
            >
              {REASONING_EFFORT.map((effort) => (
                <option key={effort.id} value={effort.id}>{effort.label}</option>
              ))}
            </select>
          </label>
        )}

        {/* New Synthesis Mode Selector */}
        <label className="field">
          <span>Synthesis Mode</span>
          <select
            name="synthesis_mode"
            value={values.synthesis_mode}
            onChange={handleInput}
            disabled={isLoading}
          >
            {SYNTHESIS_MODES.map((mode) => (
              <option key={mode.id} value={mode.id}>{mode.label}</option>
            ))}
          </select>
        </label>

        {/* New Image Model Selector */}
        <label className="field">
          <span>Image Model</span>
          <select
            name="image_model"
            value={values.image_model}
            onChange={handleInput}
            disabled={isLoading}
          >
            {IMAGE_MODELS.map((model) => (
              <option key={model.id} value={model.id}>{model.label}</option>
            ))}
          </select>
        </label>

        {/* Dynamic Image Quality Selector */}
        <label className="field">
          <span>Image Quality</span>
          <select
            name="image_quality"
            value={values.image_quality}
            onChange={handleInput}
            disabled={isLoading}
          >
            {imageQualityOptions.map((quality) => (
              <option key={quality} value={quality}>{quality}</option>
            ))}
          </select>
        </label>

        {/* Dynamic Image Size Selector */}
        <label className="field">
          <span>Image Size</span>
          <select
            name="image_size"
            value={values.image_size}
            onChange={handleInput}
            disabled={isLoading}
          >
            {imageSizeOptions.map((size) => (
              <option key={size} value={size}>{size}</option>
            ))}
          </select>
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
            name="images_per_prompt"
            min={1}
            max={4}
            value={values.images_per_prompt}
            onChange={handleInput}
            disabled={isLoading}
          />
        </label>
      </div>
    </section>
  );
}
