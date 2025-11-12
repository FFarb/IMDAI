import { useState } from 'react';
import { TradeCalculator, IndicatorDashboard } from '../components/Crypto';

type CryptoTab = 'calculator' | 'dashboard';

export function CryptoPage() {
  const [activeTab, setActiveTab] = useState<CryptoTab>('calculator');

  return (
    <div className="crypto-page">
      <div className="card">
        <div className="card-header">
          <h2>Crypto Analysis Tools</h2>
          <div className="tab-row">
            <button
              className={`tab ${activeTab === 'calculator' ? 'active' : ''}`}
              onClick={() => setActiveTab('calculator')}
            >
              Trade Calculator
            </button>
            <button
              className={`tab ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveTab('dashboard')}
            >
              Indicator Dashboard
            </button>
          </div>
        </div>
        <div className="tab-content">
          {activeTab === 'calculator' && <TradeCalculator />}
          {activeTab === 'dashboard' && <IndicatorDashboard />}
        </div>
      </div>
    </div>
  );
}
