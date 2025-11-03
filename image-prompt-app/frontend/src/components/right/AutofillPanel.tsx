import type { ChangeEvent } from 'react';
import { useMemo, useState } from 'react';

import { postOneClickGenerate, postResearch } from '../../api/autofill';
import type { AutofillResponse, ResearchFlags } from '../../types/autofill';
import type { ImageWithPrompt } from '../../types/promptBuilder';

interface AutofillPanelProps {
  onShowToast: (message: string) => void;
  refreshGallery: () => Promise<void> | void;
}

const AUDIENCE_OPTIONS = ['kids', 'teens', 'adults', 'family', 'mama'];
const AGE_OPTIONS = ['0–2', '3–5', '6–8', '9–12', '13+'];

const DEFAULT_FLAGS: ResearchFlags = {
  use_web: true,
  avoid_brands: true,
  kids_safe: true,
};

const PRINT_READY_HINT = 'LLM draft — review before generation';
const RESEARCH_MODEL = 'gpt-4.1-nano';
const IMAGE_MODEL = 'gpt-image-1';

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

const AutofillPanel = ({ onShowToast, refreshGallery }: AutofillPanelProps) => {
  const [topic, setTopic] = useState('');
  const [audience, setAudience] = useState(AUDIENCE_OPTIONS[0]);
  const [age, setAge] = useState(AGE_OPTIONS[0]);
  const [flags, setFlags] = useState<ResearchFlags>({ ...DEFAULT_FLAGS });
  const [imagesCount, setImagesCount] = useState(4);
  const [result, setResult] = useState<AutofillResponse | null>(null);
  const [images, setImages] = useState<ImageWithPrompt[]>([]);
  const [isResearching, setIsResearching] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [jsonExpanded, setJsonExpanded] = useState(false);

  const hasTypography = useMemo(() => Boolean(result?.traits.typography.length), [result]);

  const updateFlag = (key: keyof ResearchFlags) => (event: ChangeEvent<HTMLInputElement>) => {
    setFlags((prev) => ({ ...prev, [key]: event.target.checked }));
  };

  const handleCopy = async (value: string, label: string) => {
    const success = await copyToClipboard(value);
    onShowToast(success ? `${label} copied` : 'Copy failed');
  };

  const handleResearch = async () => {
    if (!topic.trim()) {
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
    if (!topic.trim()) {
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
        <div className="autofill-grid">
          <label htmlFor="autofill-audience">АУДИТОРИЯ</label>
          <select id="autofill-audience" value={audience} onChange={(event) => setAudience(event.target.value)}>
            {AUDIENCE_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
          <label htmlFor="autofill-age">ВОЗРАСТ</label>
          <select id="autofill-age" value={age} onChange={(event) => setAge(event.target.value)}>
            {AGE_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>
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
        <p className="model-hint">
          Research model: <code>{RESEARCH_MODEL}</code> · Image model: <code>{IMAGE_MODEL}</code>
        </p>
        <div className="autofill-actions">
          <button type="button" onClick={handleResearch} disabled={isResearching || isGenerating} className="primary">
            {isResearching ? 'Researching…' : 'Research & Fill'}
          </button>
          <div className="one-click-controls">
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
          <button
            type="button"
            data-testid="one-click-button"
            onClick={handleOneClick}
            disabled={isGenerating || isResearching}
          >
            {isGenerating ? 'Generating…' : `One-Click Image (${imagesCount})`}
          </button>
        </div>
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
              <button type="button" onClick={() => handleCopy(result.master_prompt_text, 'Prompt')}>
                Copy text
              </button>
            </div>
            <textarea readOnly value={result.master_prompt_text} />
            <div className="prompt-header">
              <button type="button" onClick={() => setJsonExpanded((prev) => !prev)}>
                {jsonExpanded ? 'Hide JSON' : 'Show JSON'}
              </button>
              <button type="button" onClick={() => handleCopy(JSON.stringify(result.master_prompt_json, null, 2), 'Prompt JSON')}>
                Copy JSON
              </button>
            </div>
            {jsonExpanded && (
              <pre className="prompt-json">{JSON.stringify(result.master_prompt_json, null, 2)}</pre>
            )}
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
