import { useEffect, useState } from 'react';

type IndicatorSignal = {
  name: string;
  params: string;
  signal: 'LONG' | 'SHORT' | 'NEUTRAL';
  streak: number;
};

async function fetchIndicatorDashboard(symbol: string, interval: string): Promise<{ indicators: IndicatorSignal[] }> {
  const response = await fetch(`/api/crypto/indicator_dashboard?symbol=${symbol}&interval=${interval}`);
  if (!response.ok) {
    throw new Error('Failed to fetch indicator dashboard');
  }
  return response.json();
}

const ASSET_OPTIONS = ['BTCUSDT', 'ETHUSDT', 'DOGEUSDT'];
const TIMEFRAME_OPTIONS = ['15m', '30m', '1h', '2h', '3h'];

export function IndicatorDashboard() {
  const [symbol, setSymbol] = useState(ASSET_OPTIONS[0]);
  const [interval, setInterval] = useState(TIMEFRAME_OPTIONS[0]);
  const [indicators, setIndicators] = useState<IndicatorSignal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setIsLoading(true);
    fetchIndicatorDashboard(symbol, interval)
      .then(data => setIndicators(data.indicators))
      .catch(err => setError(err.message))
      .finally(() => setIsLoading(false));
  }, [symbol, interval]);

  const getSignalClass = (signal: string) => {
    switch (signal) {
      case 'LONG': return 'signal-long';
      case 'SHORT': return 'signal-short';
      default: return 'signal-neutral';
    }
  };

  if (error) return <div className="toast error">{error}</div>;

  return (
    <div className="indicator-dashboard">
      <div className="tab-row">
        {ASSET_OPTIONS.map(opt => (
          <button key={opt} className={`tab ${symbol === opt ? 'active' : ''}`} onClick={() => setSymbol(opt)}>{opt}</button>
        ))}
      </div>
      <div className="tab-row">
        {TIMEFRAME_OPTIONS.map(opt => (
          <button key={opt} className={`tab ${interval === opt ? 'active' : ''}`} onClick={() => setInterval(opt)}>{opt}</button>
        ))}
      </div>

      {isLoading ? (
        <div>Loading Indicators...</div>
      ) : (
        <div className="indicator-grid">
          {indicators.map((item, index) => (
            <div key={index} className="indicator-item">
              <div className="indicator-name">{item.name}({item.params})</div>
              <div className={`indicator-signal ${getSignalClass(item.signal)}`}>
                {item.signal} ({item.streak})
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
