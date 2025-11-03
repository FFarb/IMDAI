import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from 'react';

import type { SynthPrompt, SynthesisOutput } from '../types/pipeline';

interface PromptTabsProps {
  synthesis: SynthesisOutput | null;
  imagesPerPrompt: number;
  onPromptChange: (index: number, prompt: SynthPrompt) => void;
  onGenerateImages: (index: number, append?: boolean) => void;
  onCopyPrompt: (index: number) => void;
  onSavePrompt: (index: number) => void;
  isLoading: boolean;
}

export function PromptTabs({
  synthesis,
  imagesPerPrompt,
  onPromptChange,
  onGenerateImages,
  onCopyPrompt,
  onSavePrompt,
  isLoading,
}: PromptTabsProps) {
  const prompts = synthesis?.prompts ?? [];
  const [activeIndex, setActiveIndex] = useState(0);
  const [newNegative, setNewNegative] = useState('');

  useEffect(() => {
    setActiveIndex(0);
  }, [prompts.length]);

  useEffect(() => {
    setNewNegative('');
  }, [activeIndex]);

  const activePrompt = useMemo(() => prompts[activeIndex], [prompts, activeIndex]);

  if (!prompts.length) {
    return (
      <section className="card">
        <header className="card-header">
          <div>
            <h2>Assembled Prompts</h2>
            <p className="card-subtitle">Synthesise prompts to edit and generate images.</p>
          </div>
        </header>
        <p className="muted">No prompts yet. Run synthesis to begin.</p>
      </section>
    );
  }

  const updatePrompt = (changes: Partial<SynthPrompt>) => {
    if (!activePrompt) return;
    onPromptChange(activeIndex, { ...activePrompt, ...changes });
  };

  const handleFieldChange = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = event.target;
    if (name === 'title') {
      updatePrompt({ title: value });
    }
    if (name === 'positive') {
      updatePrompt({ positive: value });
    }
    if (name === 'notes') {
      updatePrompt({ notes: value });
    }
  };

  const handleAddNegative = (event: FormEvent) => {
    event.preventDefault();
    const value = newNegative.trim();
    if (!value || !activePrompt) return;
    if (activePrompt.negative.includes(value)) {
      setNewNegative('');
      return;
    }
    updatePrompt({ negative: [...activePrompt.negative, value] });
    setNewNegative('');
  };

  const handleRemoveNegative = (index: number) => {
    if (!activePrompt) return;
    const updated = activePrompt.negative.filter((_, idx) => idx !== index);
    updatePrompt({ negative: updated });
  };

  const tabLabel = (idx: number) => String.fromCharCode(65 + idx);

  return (
    <section className="card">
      <header className="card-header">
        <div>
          <h2>Assembled Prompts</h2>
          <p className="card-subtitle">Fine-tune before sending to the Images stage.</p>
        </div>
      </header>

      <div className="tab-row">
        {prompts.map((prompt, idx) => (
          <button
            key={idx}
            type="button"
            className={`tab ${idx === activeIndex ? 'active' : ''}`}
            onClick={() => setActiveIndex(idx)}
          >
            {tabLabel(idx)}
            {prompt.title ? ` · ${prompt.title}` : ''}
          </button>
        ))}
      </div>

      {activePrompt ? (
        <div className="prompt-editor">
          <label className="field">
            <span>Prompt title</span>
            <input name="title" value={activePrompt.title ?? ''} onChange={handleFieldChange} placeholder="Optional label" />
          </label>

          <label className="field">
            <span>Positive prompt</span>
            <textarea
              name="positive"
              rows={6}
              value={activePrompt.positive}
              onChange={handleFieldChange}
            />
          </label>

          <div className="field">
            <span>Negative tags</span>
            <div className="pill-row">
              {activePrompt.negative.map((item, idx) => (
                <span className="pill removable" key={`${item}-${idx}`}>
                  {item}
                  <button type="button" onClick={() => handleRemoveNegative(idx)} aria-label={`Remove ${item}`}>
                    ×
                  </button>
                </span>
              ))}
            </div>
            <form className="inline-form" onSubmit={handleAddNegative}>
              <input
                value={newNegative}
                onChange={(event) => setNewNegative(event.target.value)}
                placeholder="Add negative tag"
              />
              <button type="submit" disabled={!newNegative.trim()}>
                Add
              </button>
            </form>
          </div>

          <label className="field">
            <span>Notes</span>
            <textarea name="notes" rows={3} value={activePrompt.notes ?? ''} onChange={handleFieldChange} />
          </label>

          <div className="card-actions">
            <button type="button" onClick={() => onGenerateImages(activeIndex, false)} disabled={isLoading} className="primary">
              Generate Images ({imagesPerPrompt})
            </button>
            <button type="button" onClick={() => onCopyPrompt(activeIndex)} disabled={isLoading}>
              Copy Prompt
            </button>
            <button type="button" onClick={() => onSavePrompt(activeIndex)} disabled={isLoading}>
              Save Prompt
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}
