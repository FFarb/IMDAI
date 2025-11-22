import { ImageLabPage } from './pages/ImageLabPage';

function App(): JSX.Element {
  return (
    <div className="app-shell">
      <header className="app-header app-header--global">
        <div>
          <h1>IMDAI Labs</h1>
          <p>AI-Powered Image Generation with Multi-Agent Intelligence</p>
        </div>
      </header>

      <section className="tab-panel">
        <ImageLabPage />
      </section>
    </div>
  );
}

export default App;

