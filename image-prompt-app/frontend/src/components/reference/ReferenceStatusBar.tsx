import type { DiscoverStats } from '../../types/discovery';

interface ReferenceStatusBarProps {
  stats: DiscoverStats | null;
  selectedCount: number;
  rps: number;
  lastUpdated?: Date | null;
}

export default function ReferenceStatusBar({ stats, selectedCount, rps, lastUpdated }: ReferenceStatusBarProps) {
  return (
    <div className="reference-status">
      <div>
        <strong>Found:</strong> {stats ? stats.found : '—'}
      </div>
      <div>
        <strong>Unique:</strong> {stats ? stats.unique : '—'}
      </div>
      <div>
        <strong>Selected:</strong> {selectedCount}
      </div>
      <div>
        <strong>Dup rate:</strong> {stats ? `${Math.round(stats.dup_rate * 100)}%` : '—'}
      </div>
      <div>
        <strong>Rate limit:</strong> {rps} rps
      </div>
      {lastUpdated && (
        <div className="reference-status-updated">Updated {lastUpdated.toLocaleTimeString()}</div>
      )}
    </div>
  );
}
