import { useEffect, useState } from 'react';

type BybitSpecsResponse = {
  contract_size: number;
  tick_size: number;
  min_qty: number;
  step_size: number;
  max_leverage: number;
  maintenance_margin_rate: number;
  initial_margin_rate: number;
  taker_fee: number;
  maker_fee: number;
  funding_interval_minutes: number;
};

type MarketPriceResponse = {
  index_price: number;
  mark_price: number;
};

type FundingRateResponse = {
  funding_rate: number;
};

async function fetchBybitSpecs(symbol: string): Promise<BybitSpecsResponse> {
  const response = await fetch('/api/crypto/bybit/specs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol }),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch Bybit specs');
  }
  return response.json();
}

async function fetchBybitMarketPrice(symbol: string): Promise<MarketPriceResponse> {
    const response = await fetch(`/api/crypto/bybit/market_price?symbol=${symbol}`);
    if (!response.ok) {
        throw new Error('Failed to fetch Bybit market price');
    }
    return response.json();
}

async function fetchBybitFundingRate(symbol: string): Promise<FundingRateResponse> {
    const response = await fetch(`/api/crypto/bybit/funding_rate?symbol=${symbol}`);
    if (!response.ok) {
        throw new Error('Failed to fetch Bybit funding rate');
    }
    return response.json();
}

async function postEstimateLiqPrice(
    side: string,
    entry_price: number,
    qty: number,
    leverage: number,
    mmr: number,
    contract_value: number,
): Promise<{ liquidation_price: number }> {
    const response = await fetch('/api/crypto/bybit/estimate_liq_price', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ side, entry_price, qty, leverage, mmr, contract_value }),
    });
    if (!response.ok) {
        throw new Error('Failed to estimate liquidation price');
    }
    return response.json();
}

async function postCalculatePnl(
    entry_px: number,
    exit_px: number,
    qty: number,
    side: string,
    contract_value: number,
    taker_fee: number,
): Promise<{ realized_pnl: number }> {
    const response = await fetch('/api/crypto/bybit/calculate_pnl', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entry_px, exit_px, qty, side, contract_value, taker_fee }),
    });
    if (!response.ok) {
        throw new Error('Failed to calculate PnL');
    }
    return response.json();
}

export function BybitCalculator(): JSX.Element {
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [side, setSide] = useState('long');
  const [entryPrice, setEntryPrice] = useState('');
  const [quantity, setQuantity] = useState('');
  const [leverage, setLeverage] = useState('');
  const [exitPrice, setExitPrice] = useState('');

  const [specs, setSpecs] = useState<BybitSpecsResponse | null>(null);
  const [marketPrice, setMarketPrice] = useState<MarketPriceResponse | null>(null);
  const [fundingRate, setFundingRate] = useState<FundingRateResponse | null>(null);
  const [liqPrice, setLiqPrice] = useState('');
  const [pnl, setPnl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

    useEffect(() => {
        const loadData = async () => {
            setIsLoading(true);
            setError('');
            try {
                const [specsData, marketPriceData, fundingRateData] = await Promise.all([
                    fetchBybitSpecs(symbol),
                    fetchBybitMarketPrice(symbol),
                    fetchBybitFundingRate(symbol),
                ]);
                setSpecs(specsData);
                setMarketPrice(marketPriceData);
                setFundingRate(fundingRateData);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'An unknown error occurred');
            } finally {
                setIsLoading(false);
            }
        };
        loadData();
    }, [symbol]);

    useEffect(() => {
        if (entryPrice && quantity && leverage && specs) {
            const calculateLiqPrice = async () => {
                try {
                    const result = await postEstimateLiqPrice(
                        side,
                        parseFloat(entryPrice),
                        parseFloat(quantity),
                        parseInt(leverage),
                        specs.maintenance_margin_rate,
                        specs.contract_size,
                    );
                    setLiqPrice(result.liquidation_price.toFixed(2));
                } catch (err) {
                    // Handle error silently as this is a background calculation
                }
            };
            calculateLiqPrice();
        }
    }, [entryPrice, quantity, leverage, specs, side]);

    useEffect(() => {
        if (entryPrice && quantity && exitPrice && specs) {
            const calculatePnl = async () => {
                try {
                    const result = await postCalculatePnl(
                        parseFloat(entryPrice),
                        parseFloat(exitPrice),
                        parseFloat(quantity),
                        side,
                        specs.contract_size,
                        specs.taker_fee,
                    );
                    setPnl(result.realized_pnl.toFixed(2));
                } catch (err) {
                    // Handle error silently
                }
            };
            calculatePnl();
        }
    }, [entryPrice, quantity, exitPrice, specs, side]);

  return (
    <div className="card">
      <h3>Bybit Trade Calculator</h3>
      <div className="field-grid">
        <label>
          Symbol
          <input type="text" value={symbol} onChange={(e) => setSymbol(e.target.value)} />
        </label>
        <label>
          Side
          <select value={side} onChange={(e) => setSide(e.target.value)}>
            <option value="long">Long</option>
            <option value="short">Short</option>
          </select>
        </label>
        <label>
          Entry Price
          <input type="text" value={entryPrice} onChange={(e) => setEntryPrice(e.target.value)} />
        </label>
        <label>
          Quantity
          <input type="text" value={quantity} onChange={(e) => setQuantity(e.target.value)} />
        </label>
        <label>
          Leverage
          <input type="text" value={leverage} onChange={(e) => setLeverage(e.target.value)} />
        </label>
        <label>
          Exit Price
          <input type="text" value={exitPrice} onChange={(e) => setExitPrice(e.target.value)} />
        </label>
      </div>
      <div>
        <p>Est. Liquidation Price: {isLoading ? '...' : liqPrice}</p>
        <p>Realized PnL: {isLoading ? '...' : pnl}</p>
        <p>Funding Rate: {fundingRate ? (fundingRate.funding_rate * 100).toFixed(4) + '%' : '...'}</p>
        <p>Next Funding: In {specs?.funding_interval_minutes || '...'} mins</p>
        <p>Mark Price: {marketPrice?.mark_price || '...'}</p>
      </div>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
