import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ColorType,
  LineStyle,
  createChart,
  type CandlestickData,
  type HistogramData,
  type IChartApi,
  type ISeriesApi,
  type LineData,
  type UTCTimestamp,
} from 'lightweight-charts';
import { BollingerBands, EMA, MACD, RSI } from 'technicalindicators';

const SYMBOL_OPTIONS = [
  { label: 'BTC/USDT', value: 'BTCUSDT' },
  { label: 'ETH/USDT', value: 'ETHUSDT' },
  { label: 'DOGE/USDT', value: 'DOGEUSDT' },
] as const;

const INTERVAL_OPTIONS = ['1m', '3m', '5m', '15m'] as const;

type SymbolValue = (typeof SYMBOL_OPTIONS)[number]['value'];
type IntervalValue = (typeof INTERVAL_OPTIONS)[number];

type CandlestickPoint = CandlestickData & { time: UTCTimestamp };

type IndicatorLine = LineData & { time: UTCTimestamp };

type MacdHistogramPoint = HistogramData<UTCTimestamp>;

function mapCandle(raw: unknown[]): CandlestickPoint {
  return {
    time: Math.floor(Number(raw[0]) / 1000) as UTCTimestamp,
    open: Number(raw[1]),
    high: Number(raw[2]),
    low: Number(raw[3]),
    close: Number(raw[4]),
  };
}

export function CryptoPage(): JSX.Element {
  const [symbol, setSymbol] = useState<SymbolValue>(SYMBOL_OPTIONS[0].value);
  const [interval, setInterval] = useState<IntervalValue>(INTERVAL_OPTIONS[0]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const chartContainerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const emaSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const bbUpperSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const bbMiddleSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const bbLowerSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const macdSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const rsiSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);

  const symbolLabel = useMemo(() => {
    return SYMBOL_OPTIONS.find((option) => option.value === symbol)?.label ?? symbol;
  }, [symbol]);

  useEffect(() => {
    if (!chartContainerRef.current) {
      return;
    }

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#1f2937',
      },
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      grid: {
        vertLines: { color: '#f3f4f6' },
        horzLines: { color: '#f3f4f6' },
      },
      timeScale: { borderColor: '#e5e7eb' },
      rightPriceScale: { borderColor: '#e5e7eb' },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      borderUpColor: '#22c55e',
      wickUpColor: '#22c55e',
      downColor: '#ef4444',
      borderDownColor: '#ef4444',
      wickDownColor: '#ef4444',
    });

    const emaSeries = chart.addLineSeries({
      color: '#6366f1',
      lineWidth: 2,
    });

    const bbUpperSeries = chart.addLineSeries({
      color: '#10b981',
      lineWidth: 1,
    });

    const bbMiddleSeries = chart.addLineSeries({
      color: '#6b7280',
      lineWidth: 1,
      lineStyle: LineStyle.Dotted,
    });

    const bbLowerSeries = chart.addLineSeries({
      color: '#10b981',
      lineWidth: 1,
    });

    const macdSeries = chart.addHistogramSeries({
      priceScaleId: 'macd',
      scaleMargins: { top: 0.75, bottom: 0 },
      color: '#22c55e',
      baseLineColor: '#9ca3af',
      baseLineVisible: true,
    });

    const rsiSeries = chart.addLineSeries({
      priceScaleId: 'rsi',
      scaleMargins: { top: 0.05, bottom: 0.2 },
      color: '#f97316',
      lineWidth: 2,
    });

    chart.priceScale('macd').applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    chart.priceScale('rsi').applyOptions({
      scaleMargins: { top: 0.15, bottom: 0.1 },
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    emaSeriesRef.current = emaSeries;
    bbUpperSeriesRef.current = bbUpperSeries;
    bbMiddleSeriesRef.current = bbMiddleSeries;
    bbLowerSeriesRef.current = bbLowerSeries;
    macdSeriesRef.current = macdSeries;
    rsiSeriesRef.current = rsiSeries;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        chart.applyOptions({ width, height });
      }
    });

    resizeObserver.observe(chartContainerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      emaSeriesRef.current = null;
      bbUpperSeriesRef.current = null;
      bbMiddleSeriesRef.current = null;
      bbLowerSeriesRef.current = null;
      macdSeriesRef.current = null;
      rsiSeriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const loadData = async () => {
      if (!candleSeriesRef.current) {
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `/api/crypto/kline?symbol=${encodeURIComponent(symbol)}&interval=${encodeURIComponent(interval)}`,
          { signal: controller.signal },
        );

        if (!response.ok) {
          throw new Error(`Unable to load market data (${response.status})`);
        }

        const payload = (await response.json()) as unknown[][];
        if (!Array.isArray(payload)) {
          throw new Error('Unexpected response from server');
        }

        const candles = payload.map(mapCandle);
        const closes = candles.map((item) => item.close);

        candleSeriesRef.current.setData(candles);

        const emaPeriod = 20;
        const emaValues = EMA.calculate({ period: emaPeriod, values: closes });
        const emaOffset = candles.length - emaValues.length;
        const emaData: IndicatorLine[] = emaValues.map((value, index) => ({
          time: candles[index + emaOffset].time,
          value,
        }));
        emaSeriesRef.current?.setData(emaData);

        const bbPeriod = 20;
        const bbStdDev = 2;
        const bbValues = BollingerBands.calculate({ period: bbPeriod, stdDev: bbStdDev, values: closes });
        const bbOffset = candles.length - bbValues.length;
        const upperBand: IndicatorLine[] = [];
        const middleBand: IndicatorLine[] = [];
        const lowerBand: IndicatorLine[] = [];
        bbValues.forEach((band, index) => {
          const time = candles[index + bbOffset].time;
          upperBand.push({ time, value: band.upper });
          middleBand.push({ time, value: band.middle });
          lowerBand.push({ time, value: band.lower });
        });
        bbUpperSeriesRef.current?.setData(upperBand);
        bbMiddleSeriesRef.current?.setData(middleBand);
        bbLowerSeriesRef.current?.setData(lowerBand);

        const macdValues = MACD.calculate({
          fastPeriod: 12,
          slowPeriod: 26,
          signalPeriod: 9,
          SimpleMAOscillator: false,
          SimpleMASignal: false,
          values: closes,
        });
        const macdOffset = candles.length - macdValues.length;
        const macdHistogram: MacdHistogramPoint[] = macdValues.map((point, index) => {
          const histogram = point.histogram ?? 0;
          return {
            time: candles[index + macdOffset].time,
            value: histogram,
            color: histogram >= 0 ? '#22c55e' : '#ef4444',
          };
        });
        macdSeriesRef.current?.setData(macdHistogram);

        const rsiPeriod = 14;
        const rsiValues = RSI.calculate({ period: rsiPeriod, values: closes });
        const rsiOffset = candles.length - rsiValues.length;
        const rsiData: IndicatorLine[] = rsiValues.map((value, index) => ({
          time: candles[index + rsiOffset].time,
          value,
        }));
        rsiSeriesRef.current?.setData(rsiData);

        chartRef.current?.timeScale().fitContent();
      } catch (fetchError) {
        if (fetchError instanceof DOMException && fetchError.name === 'AbortError') {
          return;
        }
        setError(fetchError instanceof Error ? fetchError.message : 'Unknown error');
      } finally {
        setIsLoading(false);
      }
    };

    void loadData();

    return () => {
      controller.abort();
    };
  }, [symbol, interval]);

  return (
    <div className="crypto-page">
      <div className="card">
        <div className="card-header">
          <div>
            <h2>Crypto Market Lab</h2>
            <p className="card-subtitle">Interactive candlesticks and technical indicators.</p>
          </div>
          <div className="crypto-controls">
            <label className="crypto-control">
              <span>Symbol</span>
              <select value={symbol} onChange={(event) => setSymbol(event.target.value as SymbolValue)}>
                {SYMBOL_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="crypto-control">
              <span>Interval</span>
              <select value={interval} onChange={(event) => setInterval(event.target.value as IntervalValue)}>
                {INTERVAL_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
        <div className="chart-meta">
          <span className="pill">{symbolLabel}</span>
          {isLoading && <span className="pill muted">Loading…</span>}
        </div>
        <div className="chart-container" ref={chartContainerRef} role="img" aria-label={`Candlestick chart for ${symbolLabel}`} />
        {error && <div className="toast error">{error}</div>}
      </div>
    </div>
  );
}
