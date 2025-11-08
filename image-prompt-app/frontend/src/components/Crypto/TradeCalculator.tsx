import { useEffect, useState, useMemo } from 'react';

// Assuming these types are defined in a central types file, but defining inline for brevity
type BybitSpecsResponse = {
  contract_size: number;
  tick_size: number;
  max_leverage: number;
  maintenance_margin_rate: number;
  taker_fee: number;
};

type MarketPriceResponse = {
  mark_price: number;
};

// API fetching functions (assumed to be in an api.ts file)
async function fetchBybitSpecs(symbol: string): Promise<BybitSpecsResponse> {
  const response = await fetch('/api/crypto/bybit/specs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol }),
  });
  if (!response.ok) throw new Error('Failed to fetch specs');
  return response.json();
}

async function fetchBybitMarketPrice(symbol: string): Promise<MarketPriceResponse> {
  const response = await fetch(`/api/crypto/bybit/market_price?symbol=${symbol}`);
  if (!response.ok) throw new Error('Failed to fetch market price');
  return response.json();
}

async function postEstimateLiqPrice(payload: any): Promise<{ liquidation_price: number }> {
  const response = await fetch('/api/crypto/bybit/estimate_liq_price', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to estimate liquidation price');
  return response.json();
}

async function postCalculatePnl(payload: any): Promise<{ realized_pnl: number }> {
  const response = await fetch('/api/crypto/bybit/calculate_pnl', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to calculate PnL');
  return response.json();
}


export function TradeCalculator() {
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [side, setSide] = useState<'long' | 'short'>('long');
  const [marketPrice, setMarketPrice] = useState<number | null>(null);
  const [specs, setSpecs] = useState<BybitSpecsResponse | null>(null);

  const [entryPrice, setEntryPrice] = useState(0);
  const [exitPrice, setExitPrice] = useState(0);
  const [stopLossPrice, setStopLossPrice] = useState('');
  const [takeProfitPrice, setTakeProfitPrice] = useState('');
  const [quantity, setQuantity] = useState('');
  const [leverage, setLeverage] = useState(10);

  const [liqPrice, setLiqPrice] = useState('');
  const [pnl, setPnl] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const priceRange = useMemo(() => {
    if (!marketPrice) return { min: 0, max: 0, step: 1 };
    const margin = marketPrice * 0.20;
    const step = specs?.tick_size || 1;
    return {
      min: Math.floor((marketPrice - margin) / step) * step,
      max: Math.ceil((marketPrice + margin) / step) * step,
      step,
    };
  }, [marketPrice, specs]);

  useEffect(() => {
    setIsLoading(true);
    Promise.all([fetchBybitSpecs(symbol), fetchBybitMarketPrice(symbol)])
      .then(([specsData, priceData]) => {
        setSpecs(specsData);
        setMarketPrice(priceData.mark_price);
        setEntryPrice(priceData.mark_price);
        setExitPrice(priceData.mark_price);
      })
      .catch(err => setError(err.message))
      .finally(() => setIsLoading(false));
  }, [symbol]);

  useEffect(() => {
    if (entryPrice && quantity && leverage && specs) {
      const payload = {
        side,
        entry_price: entryPrice,
        qty: parseFloat(quantity),
        leverage,
        mmr: specs.maintenance_margin_rate,
        contract_value: specs.contract_size,
      };
      postEstimateLiqPrice(payload)
        .then(data => setLiqPrice(data.liquidation_price.toFixed(2)))
        .catch(() => setLiqPrice('N/A'));
    }
  }, [entryPrice, quantity, leverage, side, specs]);

  useEffect(() => {
    if (entryPrice && exitPrice && quantity && specs) {
      const payload = {
        entry_px: entryPrice,
        exit_px: exitPrice,
        qty: parseFloat(quantity),
        side,
        contract_value: specs.contract_size,
        taker_fee: specs.taker_fee,
      };
      postCalculatePnl(payload)
        .then(data => setPnl(data.realized_pnl.toFixed(2)))
        .catch(() => setPnl('N/A'));
    }
  }, [entryPrice, exitPrice, quantity, side, specs]);

  const handleRrPreset = (ratio: number) => {
    const entry = entryPrice;
    const sl = parseFloat(stopLossPrice);
    if (!sl || !entry) return;

    const risk = side === 'long' ? entry - sl : sl - entry;
    if (risk <= 0) {
        setTakeProfitPrice('');
        return;
    };

    const tp = side === 'long' ? entry + (risk * ratio) : entry - (risk * ratio);
    setTakeProfitPrice(tp.toFixed(2));
  };

  if (isLoading) return <div>Loading Calculator...</div>;
  if (error) return <div className="toast error">{error}</div>;

  return (
    <div className="trade-calculator">
      <div className="field-grid">
        {/* Controls */}
        <div className="field">
            <span>Symbol</span>
            <input type="text" value={symbol} onChange={e => setSymbol(e.target.value.toUpperCase())} />
        </div>
        <div className="field">
            <span>Side</span>
            <select value={side} onChange={e => setSide(e.target.value as 'long' | 'short')}>
                <option value="long">Long</option>
                <option value="short">Short</option>
            </select>
        </div>
        <div className="field">
            <span>Quantity</span>
            <input type="number" value={quantity} onChange={e => setQuantity(e.target.value)} placeholder="e.g., 0.5" />
        </div>
      </div>

      {/* Leverage Slider */}
      <div className="field">
        <span>Leverage: {leverage}x</span>
        <input
            type="range"
            min="1"
            max={specs?.max_leverage || 100}
            value={leverage}
            onChange={e => setLeverage(parseInt(e.target.value))}
            step="1"
        />
        <div className="chip-row">
            {[1, 5, 10, 25, 50, 100].map(val => (
                <button key={val} className="chip" onClick={() => setLeverage(val)}>{val}x</button>
            ))}
        </div>
      </div>

      {/* Price Sliders */}
      <div className="field">
          <span>Entry Price: {entryPrice}</span>
          <input type="range" min={priceRange.min} max={priceRange.max} step={priceRange.step} value={entryPrice} onChange={e => setEntryPrice(parseFloat(e.target.value))} />
      </div>
      <div className="field">
          <span>Exit Price: {exitPrice}</span>
          <input type="range" min={priceRange.min} max={priceRange.max} step={priceRange.step} value={exitPrice} onChange={e => setExitPrice(parseFloat(e.target.value))} />
      </div>

      {/* R:R Calculator */}
      <div className="card">
        <h4>R:R Calculator</h4>
        <div className="field-grid">
            <div className="field">
                <span>Stop Loss Price</span>
                <input type="number" value={stopLossPrice} onChange={e => setStopLossPrice(e.target.value)} />
            </div>
            <div className="field">
                <span>Take Profit Price</span>
                <input type="number" value={takeProfitPrice} onChange={e => setTakeProfitPrice(e.target.value)} />
            </div>
        </div>
        <div className="chip-row">
            <button className="chip" onClick={() => handleRrPreset(1)}>1:1</button>
            <button className="chip" onClick={() => handleRrPreset(2)}>1:2</button>
            <button className="chip" onClick={() => handleRrPreset(3)}>1:3</button>
        </div>
      </div>

      {/* Outputs */}
      <div className="card-actions">
        <p>Est. Liquidation Price: <strong>{liqPrice}</strong></p>
        <p>Realized PnL: <strong style={{ color: parseFloat(pnl) >= 0 ? 'green' : 'red' }}>{pnl}</strong></p>
      </div>
    </div>
  );
}
