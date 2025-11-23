import { useState } from 'react';
import { ImageLabPage } from './pages/ImageLabPage';
import { LibraryTab } from './components/LibraryTab';

function App(): JSX.Element {
  const [activeTab, setActiveTab] = useState<'generator' | 'library'>('generator');

  return (
    <div className="app-shell">
      <header className="app-header app-header--global">
        <div>
          <h1>IMDAI Labs</h1>
          <p>AI-Powered Image Generation with Multi-Agent Intelligence</p>
        </div>
      </header>

      <nav style={{
        display: 'flex',
        gap: '1rem',
        padding: '1rem 2rem',
        borderBottom: '1px solid var(--border)',
        background: 'var(--surface)'
      }}>
        <button
          onClick={() => setActiveTab('generator')}
          className={activeTab === 'generator' ? 'btn-primary' : 'btn-secondary'}
        >
          🎨 Generator
        </button>
        <button
          onClick={() => setActiveTab('library')}
          className={activeTab === 'library' ? 'btn-primary' : 'btn-secondary'}
        >
          📚 Library
        </button>
      </nav>

      <section className="tab-panel">
        {activeTab === 'generator' ? <ImageLabPage /> : <LibraryTab />}
      </section>
    </div>
  );
}

export default App;

