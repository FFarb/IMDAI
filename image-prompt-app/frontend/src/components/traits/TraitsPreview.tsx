import { useState } from 'react';
import type { DatasetTraits } from '../../types/discovery';

interface TraitsPreviewProps {
  traits: DatasetTraits | null;
  loading?: boolean;
}

const MOTIF_LIMIT = 12;

export default function TraitsPreview({ traits, loading = false }: TraitsPreviewProps) {
  const [copiedHex, setCopiedHex] = useState<string | null>(null);

  if (loading) {
    return <div className="traits-panel">Analyzing traits…</div>;
  }

  if (!traits) {
    return <div className="traits-panel empty">Traits not available yet.</div>;
  }

  const handleCopyHex = async (hex: string) => {
    try {
      await navigator.clipboard.writeText(hex);
      setCopiedHex(hex);
      setTimeout(() => setCopiedHex(null), 1500);
    } catch (error) {
      console.warn('Clipboard copy failed', error);
    }
  };

  return (
    <div className="traits-panel">
      <div className="traits-group">
        <h4>Palette</h4>
        <div className="palette-grid">
          {traits.palette.map((entry) => (
            <button
              key={entry.hex}
              type="button"
              className="palette-chip"
              title={`Copy ${entry.hex}`}
              onClick={() => handleCopyHex(entry.hex)}
              style={{ backgroundColor: entry.hex }}
            >
              <span>{entry.hex}</span>
              <small>{entry.weight.toFixed(2)}</small>
              {copiedHex === entry.hex && <em>Copied</em>}
            </button>
          ))}
        </div>
      </div>
      <div className="traits-group">
        <h4>Motifs</h4>
        <div className="motif-grid">
          {traits.motifs.slice(0, MOTIF_LIMIT).map((motif) => (
            <span className="motif-pill" key={motif}>
              {motif}
            </span>
          ))}
        </div>
      </div>
      <div className="traits-group">
        <h4>Line &amp; Outline</h4>
        <p>
          <strong>{traits.line_weight}</strong> lines, <strong>{traits.outline}</strong> outlines
        </p>
      </div>
      <div className="traits-group">
        <h4>Typography</h4>
        {traits.typography.length > 0 ? (
          <ul>
            {traits.typography.map((hint) => (
              <li key={hint}>{hint}</li>
            ))}
          </ul>
        ) : (
          <p>avoid text</p>
        )}
      </div>
      <div className="traits-group">
        <h4>Composition</h4>
        {traits.composition.length > 0 ? (
          <ul>
            {traits.composition.map((hint) => (
              <li key={hint}>{hint}</li>
            ))}
          </ul>
        ) : (
          <p>centered</p>
        )}
      </div>
    </div>
  );
}
