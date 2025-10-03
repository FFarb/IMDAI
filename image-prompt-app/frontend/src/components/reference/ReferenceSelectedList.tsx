import type { Reference } from '../../types/discovery';

interface ReferenceSelectedListProps {
  references: Reference[];
  focusedId: string | null;
  onFocusChange: (id: string | null) => void;
  onHide: (reference: Reference) => void;
  onDelete: (reference: Reference) => void;
  onStar: (reference: Reference) => void;
  onMove: (reference: Reference, direction: 'up' | 'down') => void;
  onInfo: (reference: Reference) => void;
  onCopyPalette: (reference: Reference) => void;
}

export default function ReferenceSelectedList({
  references,
  focusedId,
  onFocusChange,
  onHide,
  onDelete,
  onStar,
  onMove,
  onInfo,
  onCopyPalette,
}: ReferenceSelectedListProps) {
  if (references.length === 0) {
    return <div className="reference-empty">No references selected yet.</div>;
  }

  return (
    <div className="selected-list">
      {references.map((reference, index) => {
        const focused = focusedId === reference.id;
        return (
          <article
            key={reference.id}
            className={`selected-card${focused ? ' focused' : ''}`}
            tabIndex={0}
            onFocus={() => onFocusChange(reference.id)}
            onMouseEnter={() => onFocusChange(reference.id)}
          >
            <div className="selected-thumb">
              <img src={reference.thumb_url} alt={reference.title || reference.site} />
            </div>
            <div className="selected-body">
              <div className="selected-title">{reference.title || reference.site}</div>
              <div className="selected-controls">
                <button type="button" onClick={() => onStar(reference)}>★ {reference.weight.toFixed(1)}</button>
                <button type="button" className="ghost" onClick={() => onInfo(reference)}>Info</button>
                <button type="button" className="ghost" onClick={() => onCopyPalette(reference)}>Copy palette</button>
                <button type="button" className="ghost" onClick={() => onHide(reference)}>Hide</button>
                <button type="button" className="ghost" onClick={() => onDelete(reference)}>Delete</button>
              </div>
              <div className="selected-order">
                <button
                  type="button"
                  className="ghost"
                  onClick={() => onMove(reference, 'up')}
                  disabled={index === 0}
                >
                  ↑
                </button>
                <button
                  type="button"
                  className="ghost"
                  onClick={() => onMove(reference, 'down')}
                  disabled={index === references.length - 1}
                >
                  ↓
                </button>
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}
