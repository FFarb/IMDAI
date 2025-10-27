import type { ChangeEvent, KeyboardEvent } from 'react';
import { useEffect, useMemo, useState } from 'react';

import { postOneClickGenerate, postResearch } from '../../api/autofill';
import { getOptions } from '../../api/meta';
import { AUTOFILL_PREFERENCES_KEY } from '../../constants/storage';
import type { AutofillResponse, ResearchFlags } from '../../types/autofill';
import type { MetaOptions } from '../../types/meta';
import type { StoredAutofillPreferences } from '../../types/preferences';
import type { ImageWithPrompt } from '../../types/promptBuilder';

interface AutofillPanelProps {
  onShowToast: (message: string) => void;
  refreshGallery: () => Promise<void> | void;
}

const FALLBACK_AUDIENCES = ['kids', 'teens', 'adults', 'family'];
const FALLBACK_AGES = ['0–2', '3–5', '6–8', '9–12', '13+'];
const FALLBACK_FLAGS: ResearchFlags = {
  use_web: true,
  avoid_brands: true,
  kids_safe: true,
};
const PRINT_READY_HINT = 'LLM draft — review before generation';
const API_BASE = import.meta.env.VITE_API_BASE || '';

async function copyToClipboard(value: string): Promise<boolean> {
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(value);
      return true;
    }
  } catch (error) {
    // Fallback below
  }
  const textarea = document.createElement('textarea');
  textarea.value = value;
  textarea.setAttribute('readonly', '');
  textarea.style.position = 'absolute';
  textarea.style.left = '-9999px';
  document.body.appendChild(textarea);
  textarea.select();
  const success = document.execCommand('copy');
  document.body.removeChild(textarea);
  return success;
}

function formatWeight(weight: number): string {
  return `${Math.round(weight * 100)}%`;
}

function mergeUnique(base: string[], extras: string[]): string[] {
  const seen = new Set<string>();
  const merged: string[] = [];
  for (const value of [...base, ...extras]) {
    if (!value || seen.has(value)) continue;
    seen.add(value);
    merged.push(value);
  }
  return merged;
}

function loadStoredPreferences(): StoredAutofillPreferences | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(AUTOFILL_PREFERENCES_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredAutofillPreferences;
  } catch (error) {
    console.warn('Failed to parse stored autofill preferences', error);
    return null;
  }
}

const AutofillPanel = ({ onShowToast, refreshGallery }: AutofillPanelProps) => {
  const [storedPreferences] = useState<StoredAutofillPreferences | null>(() => loadStoredPreferences());

  const [topic, setTopic] = useState('');
  const [customAudiences, setCustomAudiences] = useState<string[]>(storedPreferences?.customAudiences ?? []);
  const [customAges, setCustomAges] = useState<string[]>(storedPreferences?.customAges ?? []);
  const initialAudienceOptions = mergeUnique(FALLBACK_AUDIENCES, [
    ...(storedPreferences?.audience ? [storedPreferences.audience] : []),
    ...customAudiences,
  ]);
  const initialAgeOptions = mergeUnique(FALLBACK_AGES, [
    ...(storedPreferences?.age ? [storedPreferences.age] : []),
    ...customAges,
  ]);
  const [audienceOptions, setAudienceOptions] = useState<string[]>(initialAudienceOptions);
  const [ageOptions, setAgeOptions] = useState<string[]>(initialAgeOptions);
  const [audience, setAudience] = useState(storedPreferences?.audience ?? initialAudienceOptions[0] ?? '');
  const [age, setAge] = useState(storedPreferences?.age ?? initialAgeOptions[0] ?? '');
  const [flags, setFlags] = useState<ResearchFlags>(storedPreferences?.flags ?? FALLBACK_FLAGS);
  const [researchModel, setResearchModel] = useState(storedPreferences?.researchModel ?? '');
  const [imageModel, setImageModel] = useState(storedPreferences?.imageModel ?? '');
  const [imagesCount, setImagesCount] = useState(4);
  const [options, setOptions] = useState<MetaOptions | null>(null);
  const [optionsLoading, setOptionsLoading] = useState(true);
  const [optionsError, setOptionsError] = useState<string | null>(null);
  const [result, setResult] = useState<AutofillResponse | null>(null);
  const [images, setImages] = useState<ImageWithPrompt[]>([]);
  const [isResearching, setIsResearching] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const hasTypography = useMemo(() => Boolean(result?.traits.typography.length), [result]);
  const topicIsEmpty = !topic.trim();

  useEffect(() => {
    let cancelled = false;
    const fetchOptions = async () => {
      setOptionsLoading(true);
      try {
        const data = await getOptions();
        if (cancelled) return;
        setOptions(data);
        const baseAudiences = data.audiences.filter((option) => option !== 'custom');
        const baseAges = data.ages.filter((option) => option !== 'custom');
        const nextAudiences = mergeUnique(baseAudiences, [
          ...customAudiences,
          ...(storedPreferences?.audience ? [storedPreferences.audience] : []),
        ]);
        const nextAges = mergeUnique(baseAges, [
          ...customAges,
          ...(storedPreferences?.age ? [storedPreferences.age] : []),
        ]);
        setAudienceOptions(nextAudiences);
        setAgeOptions(nextAges);
        setFlags((prev) => ({ ...data.default_flags, ...(storedPreferences?.flags ?? prev) }));
        setAudience((current) => {
          if (current && nextAudiences.includes(current)) return current;
          const preferred = storedPreferences?.audience;
          if (preferred && nextAudiences.includes(preferred)) return preferred;
          return nextAudiences[0] ?? current;
        });
        setAge((current) => {
          if (current && nextAges.includes(current)) return current;
          const preferred = storedPreferences?.age;
          if (preferred && nextAges.includes(preferred)) return preferred;
          return nextAges[0] ?? current;
        });
        setResearchModel((current) =>
          current || storedPreferences?.researchModel || data.defaults?.research_model || data.research_models[0] || '',
        );
        setImageModel((current) => current || storedPreferences?.imageModel || data.image_models[0] || '');
        setOptionsError(null);
      } catch (error) {
        if (cancelled) return;
        console.error('Failed to load autofill options', error);
        setOptionsError('Failed to load options — using defaults');
        setAudienceOptions((prev) => (prev.length ? prev : initialAudienceOptions));
        setAgeOptions((prev) => (prev.length ? prev : initialAgeOptions));
        setResearchModel((current) => current || storedPreferences?.researchModel || 'gpt-4.1');
        setImageModel((current) => current || storedPreferences?.imageModel || 'gpt-image-1');
      } finally {
        if (!cancelled) {
          setOptionsLoading(false);
        }
      }
    };

    fetchOptions();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const payload: StoredAutofillPreferences = {
      audience,
      age,
      flags,
      researchModel,
      imageModel,
      customAudiences,
      customAges,
    };
    window.localStorage.setItem(AUTOFILL_PREFERENCES_KEY, JSON.stringify(payload));
  }, [audience, age, flags, researchModel, imageModel, customAudiences, customAges]);

  const updateFlag = (key: keyof ResearchFlags) => (event: ChangeEvent<HTMLInputElement>) => {
    const { checked } = event.target;
    setFlags((prev) => ({ ...prev, [key]: checked }));
  };

  const handleCopy = async (value: string, label: string) => {
    const success = await copyToClipboard(value);
    onShowToast(success ? `${label} copied` : 'Copy failed');
  };

  const handleCustomAudienceKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key !== 'Enter') return;
    event.preventDefault();
    const value = event.currentTarget.value.trim();
    if (!value) return;
    setAudienceOptions((prev) => mergeUnique(prev, [value]));
    setCustomAudiences((prev) => (prev.includes(value) ? prev : [...prev, value]));
    setAudience(value);
    event.currentTarget.value = '';
  };

  const handleCustomAgeKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key !== 'Enter') return;
    event.preventDefault();
    const value = event.currentTarget.value.trim();
    if (!value) return;
    setAgeOptions((prev) => mergeUnique(prev, [value]));
    setCustomAges((prev) => (prev.includes(value) ? prev : [...prev, value]));
    setAge(value);
    event.currentTarget.value = '';
  };

  const handleResearch = async () => {
    if (topicIsEmpty) {
      onShowToast('Введите тему для ресёрча');
      return;
    }
    setIsResearching(true);
    try {
      const { data, warning } = await postResearch({ topic, audience, age, flags, images_n: imagesCount });
      setResult(data);
      setImages([]);
      if (warning) {
        onShowToast('Web search unavailable — used language model fallback');
      } else {
        onShowToast('Traits ready');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Research failed';
      onShowToast(message);
    } finally {
      setIsResearching(false);
    }
  };

  const handleOneClick = async () => {
    if (topicIsEmpty) {
      onShowToast('Введите тему для генерации');
      return;
    }
    setIsGenerating(true);
    try {
      const { data, warning } = await postOneClickGenerate({
        topic,
        audience,
        age,
        flags,
        images_n: imagesCount,
      });
      setResult(data.autofill);
      setImages(data.images);
      if (typeof refreshGallery === 'function') {
        await Promise.resolve(refreshGallery());
      }
      if (warning) {
        onShowToast('Generated via fallback — review results carefully');
      } else {
        onShowToast(`Generated ${data.images.length} image${data.images.length === 1 ? '' : 's'}`);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'One-click generation failed';
      onShowToast(message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleUseAsPreset = async () => {
    if (!result) return;
    const defaultName = topic.trim() || 'New preset';
    const presetName = window.prompt('Preset name', defaultName);
    if (!presetName || !presetName.trim()) return;

    const masterJson = result.master_prompt_json as Record<string, unknown>;
    const subject = typeof masterJson['subject'] === 'string' ? (masterJson['subject'] as string) : defaultName;
    const style = typeof masterJson['style'] === 'string' ? (masterJson['style'] as string) : '';
    const composition = Array.isArray(masterJson['composition'])
      ? (masterJson['composition'] as string[]).join(', ')
      : result.traits.composition.join(', ');
    const mood = Array.isArray(masterJson['mood'])
      ? (masterJson['mood'] as string[]).join(', ')
      : result.traits.mood.join(', ');
    const details = Array.isArray(result.traits.seed_examples)
      ? result.traits.seed_examples.join('; ')
      : '';
    const lighting = typeof masterJson['lighting'] === 'string' ? (masterJson['lighting'] as string) : '';
    const quality = typeof masterJson['quality'] === 'string' ? (masterJson['quality'] as string) : 'best quality, 4k';

    try {
      const response = await fetch(`${API_BASE}/api/presets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: presetName.trim(),
          slots: {
            subject,
            style,
            composition,
            lighting,
            mood,
            details,
            quality,
          },
        }),
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || 'Failed to save preset');
      }
      onShowToast('Preset saved');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to save preset';
      onShowToast(message);
    }
  };

  return (
    <div className="autofill-panel">
      <section className="autofill-form">
        <label htmlFor="autofill-topic">ТЕМА</label>
        <input
          id="autofill-topic"
          type="text"
          value={topic}
          onChange={(event) => setTopic(event.target.value)}
          placeholder="e.g., baby safari minimal"
        />

        <div className="chip-group">
          <span>АУДИТОРИЯ</span>
          <div className="chip-row">
            {audienceOptions.map((option) => (
              <button
                key={option}
                type="button"
                className={`chip ${option === audience ? 'selected' : ''}`}
                onClick={() => setAudience(option)}
              >
                {option}
              </button>
            ))}
            <input
              type="text"
              placeholder="Custom audience…"
              onKeyDown={handleCustomAudienceKeyDown}
              aria-label="Add custom audience"
            />
          </div>
        </div>

        <div className="chip-group">
          <span>ВОЗРАСТ</span>
          <div className="chip-row">
            {ageOptions.map((option) => (
              <button
                key={option}
                type="button"
                className={`chip ${option === age ? 'selected' : ''}`}
                onClick={() => setAge(option)}
              >
                {option}
              </button>
            ))}
            <input
              type="text"
              placeholder="Custom age…"
              onKeyDown={handleCustomAgeKeyDown}
              aria-label="Add custom age"
            />
          </div>
        </div>

        <div className="autofill-actions">
          <button
            type="button"
            onClick={handleResearch}
            disabled={isResearching || isGenerating || topicIsEmpty}
            className="primary"
          >
            {isResearching ? 'Researching…' : 'Research & Fill'}
          </button>
          <button
            type="button"
            onClick={handleOneClick}
            disabled={isGenerating || isResearching || topicIsEmpty}
          >
            {isGenerating ? 'Generating…' : `One-Click Generate (${imagesCount})`}
          </button>
        </div>

        <details className="autofill-advanced">
          <summary>Advanced</summary>
          <div className="advanced-content">
            <div className="autofill-flags">
              <label>
                <input type="checkbox" checked={flags.use_web} onChange={updateFlag('use_web')} /> Use web
              </label>
              <label>
                <input type="checkbox" checked={flags.avoid_brands} onChange={updateFlag('avoid_brands')} /> Avoid brands
              </label>
              <label>
                <input type="checkbox" checked={flags.kids_safe} onChange={updateFlag('kids_safe')} /> Kids-safe
              </label>
            </div>
            <div className="advanced-row">
              <label htmlFor="autofill-images">Images</label>
              <input
                id="autofill-images"
                type="number"
                min={1}
                max={4}
                value={imagesCount}
                onChange={(event) => {
                  const next = Number(event.target.value);
                  if (Number.isNaN(next)) {
                    setImagesCount(1);
                    return;
                  }
                  setImagesCount(Math.max(1, Math.min(4, next)));
                }}
              />
            </div>
            <div className="advanced-row">
              <label htmlFor="autofill-research-model">Research model</label>
              <select
                id="autofill-research-model"
                value={researchModel}
                onChange={(event) => setResearchModel(event.target.value)}
                disabled={optionsLoading || !options}
              >
                {(options?.research_models ?? []).map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </div>
            <div className="advanced-row">
              <label htmlFor="autofill-image-model">Image model</label>
              <select
                id="autofill-image-model"
                value={imageModel}
                onChange={(event) => setImageModel(event.target.value)}
                disabled={optionsLoading || !options}
              >
                {(options?.image_models ?? []).map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </div>
            {optionsError && <p className="inline-warning">{optionsError}</p>}
          </div>
        </details>
      </section>

      {isResearching && (
        <div className="autofill-skeleton">
          <div className="skeleton-line" />
          <div className="skeleton-line" />
          <div className="skeleton-block" />
        </div>
      )}

      {result && !isResearching && (
        <section className="autofill-results">
          <div className="banner info">{PRINT_READY_HINT}</div>

          <h3>Traits</h3>
          <div className="palette-grid">
            {result.traits.palette.map((color) => (
              <button
                key={color.hex}
                type="button"
                className="palette-chip"
                style={{ backgroundColor: color.hex }}
                onClick={() => handleCopy(color.hex, color.hex)}
              >
                <span>{color.hex}</span>
                <small>{formatWeight(color.weight)}</small>
              </button>
            ))}
          </div>

          <div className="motif-chips">
            {result.traits.motifs.map((motif) => (
              <span key={motif} className="motif-chip">
                {motif}
              </span>
            ))}
          </div>

          <dl className="traits-meta">
            <div>
              <dt>Line Weight</dt>
              <dd>{result.traits.line_weight}</dd>
            </div>
            <div>
              <dt>Outline</dt>
              <dd>{result.traits.outline}</dd>
            </div>
            <div>
              <dt>Typography</dt>
              <dd>{hasTypography ? result.traits.typography.join(', ') : 'avoid text'}</dd>
            </div>
            <div>
              <dt>Composition</dt>
              <dd>{result.traits.composition.join(', ')}</dd>
            </div>
            <div>
              <dt>Mood</dt>
              <dd>{result.traits.mood.join(', ') || 'balanced'}</dd>
            </div>
          </dl>

          <section className="master-prompt">
            <div className="prompt-header">
              <h3>Master Prompt</h3>
              <div className="prompt-actions">
                <button type="button" onClick={() => handleCopy(result.master_prompt_text, 'Prompt')}>
                  Copy text
                </button>
                <button type="button" onClick={handleUseAsPreset}>
                  Use as preset
                </button>
              </div>
            </div>
            <textarea readOnly value={result.master_prompt_text} />
            <details className="prompt-json-details">
              <summary>Prompt JSON</summary>
              <button
                type="button"
                onClick={() => handleCopy(JSON.stringify(result.master_prompt_json, null, 2), 'Prompt JSON')}
              >
                Copy JSON
              </button>
              <pre className="prompt-json">{JSON.stringify(result.master_prompt_json, null, 2)}</pre>
            </details>
          </section>

          <section className="sources">
            <h3>Sources</h3>
            {result.traits.sources?.length ? (
              <ul>
                {result.traits.sources.map((source) => (
                  <li key={source.url}>
                    <a href={source.url} target="_blank" rel="noreferrer">
                      {source.title}
                    </a>
                  </li>
                ))}
              </ul>
            ) : (
              <p>No sources returned</p>
            )}
          </section>
        </section>
      )}

      {images.length > 0 && (
        <section className="autofill-images">
          <h3>Latest Images</h3>
          <ul>
            {images.map((image) => (
              <li key={image.image_path}>{image.image_path}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
};

export default AutofillPanel;
