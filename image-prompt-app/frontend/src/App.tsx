import { useState } from 'react';

import { CryptoPage } from './pages/CryptoPage';
import { ImageLabPage } from './pages/ImageLabPage';

type TabKey = 'imageLab' | 'crypto';

const TAB_LABELS: Record<TabKey, string> = {
  imageLab: 'Image Lab',
  crypto: 'Crypto',
};

function App(): JSX.Element {
  const [activeTab, setActiveTab] = useState<TabKey>('imageLab');

  return (
    <div className="app-shell">
      <header className="app-header app-header--global">
        <div>
          <h1>IMDAI Labs</h1>
          <p>Explore creative workflows and live crypto market insights.</p>
        </div>
        <nav className="tab-nav" aria-label="Application sections">
          {Object.entries(TAB_LABELS).map(([key, label]) => (
            <button
              key={key}
              className={`tab-button${activeTab === key ? ' active' : ''}`}
              type="button"
              onClick={() => setActiveTab(key as TabKey)}
              aria-pressed={activeTab === key}
            >
              {label}
            </button>
          ))}
        </nav>
      </header>

      <section className="tab-panel">
        {activeTab === 'imageLab' ? <ImageLabPage /> : <CryptoPage />}
      </section>
    </div>
  );
}

export default App;
