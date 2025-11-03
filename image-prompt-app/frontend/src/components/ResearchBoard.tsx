import type { ResearchOutput } from '../types/pipeline';

interface ResearchBoardProps {
  research: ResearchOutput | null;
}

export function ResearchBoard({ research }: ResearchBoardProps) {
  if (!research) {
    return (
      <section className="card">
        <header className="card-header">
          <div>
            <h2>Research Board</h2>
            <p className="card-subtitle">Run research to populate references, motifs, palette, and notes.</p>
          </div>
        </header>
        <p className="muted">No research available yet.</p>
      </section>
    );
  }

  return (
    <section className="card">
      <header className="card-header">
        <div>
          <h2>Research Board</h2>
          <p className="card-subtitle">Synthesised market scan highlights ready for prompt crafting.</p>
        </div>
      </header>

      <div className="research-grid">
        <div className="panel">
          <h3>References</h3>
          <ul className="reference-list">
            {research.references.map((ref) => (
              <li key={ref.url}>
                <span className="reference-type">{ref.type}</span>
                <a href={ref.url} target="_blank" rel="noopener noreferrer">
                  {ref.title || ref.url}
                </a>
                {ref.summary ? <p>{ref.summary}</p> : null}
              </li>
            ))}
          </ul>
        </div>

        <div className="panel">
          <h3>Motifs & Composition</h3>
          <div className="pill-row">
            {research.motifs.map((motif) => (
              <span className="pill" key={motif}>
                {motif}
              </span>
            ))}
          </div>
          <div className="pill-row">
            {research.composition.map((item) => (
              <span className="pill" key={item}>
                {item}
              </span>
            ))}
          </div>
          <p className="muted">Line: {research.line} · Outline: {research.outline}</p>
        </div>

        <div className="panel">
          <h3>Typography & Mood</h3>
          <div className="pill-row">
            {research.typography.map((item) => (
              <span className="pill" key={item}>
                {item}
              </span>
            ))}
          </div>
          {research.mood?.length ? (
            <div className="pill-row">
              {research.mood.map((item) => (
                <span className="pill" key={item}>
                  {item}
                </span>
              ))}
            </div>
          ) : null}
          {research.hooks?.length ? (
            <ul className="hook-list">
              {research.hooks.map((hook, index) => (
                <li key={`${hook}-${index}`}>{hook}</li>
              ))}
            </ul>
          ) : null}
        </div>

        <div className="panel">
          <h3>Palette</h3>
          <div className="palette-row">
            {research.palette.map((color) => (
              <div className="swatch" key={color.hex}>
                <span className="swatch-chip" style={{ backgroundColor: color.hex }} />
                <span className="swatch-label">
                  {color.hex} · {(color.weight * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
          {research.notes ? <p className="notes">{research.notes}</p> : null}
        </div>
      </div>
    </section>
  );
}
