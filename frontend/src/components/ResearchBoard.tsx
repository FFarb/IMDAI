import type { ResearchOutput } from '../types/pipeline';

interface ResearchBoardProps {
  research: ResearchOutput | null;
}

function renderParagraphs(text: string): JSX.Element[] {
  return text
    .split(/\n\n+/)
    .map((segment) => segment.trim())
    .filter(Boolean)
    .map((segment, index) => (
      <p key={`segment-${index}`} className="research-paragraph">
        {segment}
      </p>
    ));
}

export function ResearchBoard({ research }: ResearchBoardProps) {
  if (!research) {
    return (
      <section className="card">
        <header className="card-header">
          <div>
            <h2>Research Board</h2>
            <p className="card-subtitle">Run research to populate creative direction.</p>
          </div>
        </header>
        <p className="muted">No research available yet.</p>
      </section>
    );
  }

  const { analysis, highlights, segments } = research;

  return (
    <section className="card">
      <header className="card-header">
        <div>
          <h2>Research Board</h2>
          <p className="card-subtitle">Narrative brief and key guardrails for prompt design.</p>
        </div>
      </header>

      <div className="research-grid">
        <div className="panel">
          <h3>Highlights</h3>
          {highlights.length ? (
            <ul className="reference-list">
              {highlights.map((item, index) => (
                <li key={`highlight-${index}`}>{item}</li>
              ))}
            </ul>
          ) : (
            <p className="muted">No bullet highlights provided.</p>
          )}
        </div>

        <div className="panel">
          <h3>Brief Narrative</h3>
          <div className="research-text-block">{renderParagraphs(analysis)}</div>
        </div>

        <div className="panel">
          <h3>Segments</h3>
          {segments.length ? (
            <ol className="segment-list">
              {segments.map((segment, index) => (
                <li key={`segment-${index}`}>{segment}</li>
              ))}
            </ol>
          ) : (
            <p className="muted">No additional segments supplied.</p>
          )}
        </div>
      </div>
    </section>
  );
}
