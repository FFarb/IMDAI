import type { Reference } from '../../types/discovery';

interface ReferenceResultsGridProps {
  references: Reference[];
  loading: boolean;
  hasMore: boolean;
  focusedId: string | null;
  onAdd: (reference: Reference) => void;
  onHide: (reference: Reference) => void;
  onStar: (reference: Reference) => void;
  onLoadMore: () => void;
  onFocusChange: (id: string | null) => void;
}

function siteLabel(site: Reference['site']) {
  switch (site) {
    case 'openverse':
      return 'Openverse';
    case 'unsplash':
      return 'Unsplash';
    case 'generic':
      return 'Generic';
    case 'local':
      return 'Local';
    default:
      return site;
  }
}

export default function ReferenceResultsGrid({
  references,
  loading,
  hasMore,
  focusedId,
  onAdd,
  onHide,
  onStar,
  onLoadMore,
  onFocusChange,
}: ReferenceResultsGridProps) {
  if (!loading && references.length === 0) {
    return <div className="reference-empty">No references yet. Start by searching above.</div>;
  }

  return (
    <div className="reference-results">
      <div className="reference-grid">
        {references.map((reference) => {
          const focused = focusedId === reference.id;
          const watermark = reference.flags.watermark;
          const busy = reference.flags.busy_bg;
          const nsfw = reference.flags.nsfw;
          return (
            <article
              key={reference.id}
              className={`reference-card${focused ? ' focused' : ''}`}
              tabIndex={0}
              onFocus={() => onFocusChange(reference.id)}
              onMouseEnter={() => onFocusChange(reference.id)}
            >
              <div className="reference-thumb">
                <img src={reference.thumb_url} alt={reference.title || reference.site} loading="lazy" />
              </div>
              <div className="reference-meta">
                <div className="reference-meta-row">
                  <span className="reference-chip small">{siteLabel(reference.site)}</span>
                  {reference.license && <span className="reference-chip small">{reference.license}</span>}
                  {watermark && <span className="reference-chip warning">Watermark</span>}
                  {nsfw && <span className="reference-chip warning">NSFW</span>}
                  {busy && <span className="reference-chip warning">Busy BG</span>}
                </div>
                {reference.title && <div className="reference-title">{reference.title}</div>}
                <div className="reference-actions-row">
                  <button type="button" onClick={() => onAdd(reference)}>Add</button>
                  <button type="button" className="ghost" onClick={() => onHide(reference)}>Hide</button>
                  <button type="button" className="ghost" onClick={() => onStar(reference)}>
                    ★ {reference.weight.toFixed(1)}
                  </button>
                </div>
              </div>
            </article>
          );
        })}
      </div>
      {hasMore && (
        <button type="button" className="link-button" onClick={onLoadMore} disabled={loading}>
          {loading ? 'Loading…' : 'Load more'}
        </button>
      )}
    </div>
  );
}
