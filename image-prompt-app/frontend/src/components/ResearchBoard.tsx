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
            <p className="card-subtitle">Run research to populate references, concepts, and guidance.</p>
          </div>
        </header>
        <p className="muted">No research available yet.</p>
      </section>
    );
  }

  const { references, designs, color_distribution, light_distribution, gradient_distribution, notes } = research;

  return (
    <section className="card">
      <header className="card-header">
        <div>
          <h2>Research Board</h2>
          <p className="card-subtitle">Synthesised insights that guide prompt crafting and art direction.</p>
        </div>
      </header>

      <div className="research-grid">
        <div className="panel">
          <h3>References</h3>
          {references.length ? (
            <ul className="reference-list">
              {references.map((ref) => (
                <li key={ref.url}>
                  <span className="reference-type">{ref.type}</span>
                  <a href={ref.url} target="_blank" rel="noopener noreferrer">
                    {ref.title || ref.url}
                  </a>
                  {ref.summary ? <p>{ref.summary}</p> : null}
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">No references provided.</p>
          )}
        </div>

        <div className="panel">
          <h3>Design Concepts</h3>
          {designs.length ? (
            <div className="design-list">
              {designs.map((design, index) => (
                <article className="design-card" key={`design-${index}`}>
                  <h4>Concept {index + 1}</h4>
                  {design.motifs.length ? (
                    <div className="pill-row">
                      {design.motifs.map((motif) => (
                        <span className="pill" key={`motif-${motif}`}>{motif}</span>
                      ))}
                    </div>
                  ) : null}
                  {design.composition.length ? (
                    <div className="pill-row">
                      {design.composition.map((item) => (
                        <span className="pill" key={`composition-${item}`}>{item}</span>
                      ))}
                    </div>
                  ) : null}
                  <p className="muted">Line: {design.line} · Outline: {design.outline}</p>
                  {design.typography.length ? (
                    <div className="pill-row">
                      {design.typography.map((item) => (
                        <span className="pill" key={`typography-${item}`}>{item}</span>
                      ))}
                    </div>
                  ) : null}
                  {design.mood.length ? (
                    <div className="pill-row">
                      {design.mood.map((item) => (
                        <span className="pill" key={`mood-${item}`}>{item}</span>
                      ))}
                    </div>
                  ) : null}
                  {design.hooks.length ? (
                    <ul className="hook-list">
                      {design.hooks.map((hook, hookIndex) => (
                        <li key={`hook-${hookIndex}`}>{hook}</li>
                      ))}
                    </ul>
                  ) : null}
                  {design.palette.length ? (
                    <div className="palette-row">
                      {design.palette.map((color) => (
                        <div className="swatch" key={`${color.hex}-${color.weight}`}>
                          <span className="swatch-chip" style={{ backgroundColor: color.hex }} />
                          <span className="swatch-label">
                            {color.hex} · {(color.weight * 100).toFixed(0)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : null}
                  {design.notes.length ? <p className="notes">{design.notes.join(' ')}</p> : null}
                </article>
              ))}
            </div>
          ) : (
            <p className="muted">No design concepts provided.</p>
          )}
        </div>

        <div className="panel">
          <h3>Color Distribution</h3>
          {color_distribution.length ? (
            <ul className="palette-list">
              {color_distribution.map((item, index) => (
                <li key={`color-${index}`}>
                  <span className="swatch-chip" style={{ backgroundColor: item.hex }} />
                  <span>{item.area}: {item.hex} · {(item.weight * 100).toFixed(0)}%</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">No color guidance provided.</p>
          )}
        </div>

        <div className="panel">
          <h3>Lighting</h3>
          <p className="muted">Direction: {light_distribution.direction}</p>
          <ul className="metric-list">
            <li>Key: {(light_distribution.key * 100).toFixed(0)}%</li>
            <li>Fill: {(light_distribution.fill * 100).toFixed(0)}%</li>
            <li>Rim: {(light_distribution.rim * 100).toFixed(0)}%</li>
            <li>Ambient: {(light_distribution.ambient * 100).toFixed(0)}%</li>
          </ul>
          {light_distribution.zones.length ? (
            <p className="muted">Zones: {light_distribution.zones.join(', ')}</p>
          ) : null}
          {light_distribution.notes ? <p className="notes">{light_distribution.notes}</p> : null}
        </div>

        <div className="panel">
          <h3>Gradient Guidance</h3>
          {gradient_distribution.length ? (
            <ul className="gradient-list">
              {gradient_distribution.map((gradient, index) => (
                <li key={`gradient-${index}`}>
                  <strong>{gradient.type}</strong> · {gradient.allow ? 'Allowed' : 'Approximate only'}
                  {gradient.areas.length ? <div className="muted">Areas: {gradient.areas.join(', ')}</div> : null}
                  <div className="muted">
                    Stops: {gradient.stops.map((stop) => `${stop.hex} @ ${(stop.pos * 100).toFixed(0)}%`).join(', ')}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">No gradient information provided.</p>
          )}
        </div>
      </div>

      {notes ? <p className="notes-block">{notes}</p> : null}
    </section>
  );
}
