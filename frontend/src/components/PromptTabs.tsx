import { useState } from 'react';
import { generatePipeline } from '../api/generate';
import { GalleryGrid } from './GalleryGrid';
import type { BriefValues, ImageResult, AgentGenerateResponse } from '../types/pipeline';

interface PromptTabsProps {
  brief: BriefValues;
  isBriefLoading: boolean;
  onClearPipeline: () => void;
  autosave: boolean;
  setAutosave: (value: boolean) => void;
}

export function PromptTabs({
  brief,
  isBriefLoading,
  onClearPipeline,
  autosave,
}: PromptTabsProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AgentGenerateResponse | null>(null);
  const [images, setImages] = useState<ImageResult[][]>([]);

  const downloadTextFile = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadImageFile = (b64Json: string, filename: string) => {
    const byteCharacters = atob(b64Json);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: 'image/png' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleResetPipeline = () => {
    setResult(null);
    setImages([]);
    setError(null);
    onClearPipeline();
  };

  const handleGenerate = async (skipResearch = false) => {
    setIsLoading(true);
    setError(null);
    try {
      // Call the multi-agent generate endpoint
      const response = await generatePipeline({
        topic: brief.topic,
        audience: brief.audience,
        age: brief.age,
        variants: brief.variants,
        images_per_prompt: brief.images_per_prompt,
        mode: 'full',
        use_agents: true, // Enable multi-agent system
        visual_references: [], // TODO: Add image upload support
        max_iterations: 3,
        image_model: brief.image_model,
        image_quality: brief.image_quality,
        image_size: brief.image_size,
        research_model: brief.research_model,
        research_mode: brief.research_mode,
        reasoning_effort: brief.reasoning_effort,
        synthesis_mode: brief.synthesis_mode,
        // New controls
        trend_count: brief.trend_count,
        history_count: brief.history_count,
        skip_research: skipResearch,
        provided_strategy: skipResearch && result?.agent_system?.master_strategy
          ? JSON.parse(result.agent_system.master_strategy)
          : undefined,
      }) as AgentGenerateResponse;

      setResult(response);
      setImages(response.images || []);

      // Auto-save prompts if enabled
      if (autosave && response.prompts) {
        response.prompts.forEach((prompt, index) => {
          const content = `Positive Prompt:\n${prompt.positive}\n\nNegative Prompts:\n${prompt.negative?.join('\n') || 'None'}`;
          downloadTextFile(content, `prompt_${index + 1}.txt`);
        });
      }

      // Auto-save images if enabled
      if (autosave && response.images) {
        response.images.forEach((promptImages, promptIndex) => {
          promptImages.forEach((item, imageIndex) => {
            if (item.b64_json) {
              downloadImageFile(item.b64_json, `image_p${promptIndex + 1}_${imageIndex + 1}.png`);
            }
          });
        });
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unable to generate designs');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="card">
      <div className="tab-row">
        <h2>POD Design Generation</h2>
        <button type="button" className="secondary" onClick={handleResetPipeline} disabled={isLoading}>
          Clear Results
        </button>
      </div>

      {error ? <div className="error-box">{error}</div> : null}

      <div className="tab-content">
        {/* Generation Controls */}
        <div className="card-actions">
          <button
            type="button"
            className="primary"
            onClick={() => handleGenerate(false)}
            disabled={isLoading || isBriefLoading || !brief.topic.trim()}
          >
            {isLoading ? '🤖 AI Swarm Working...' : '🚀 Generate POD Designs'}
          </button>

          {result && (
            <button
              type="button"
              className="secondary"
              onClick={() => handleGenerate(true)}
              disabled={isLoading}
              style={{ marginLeft: '1rem' }}
            >
              ✨ Generate More Variants
            </button>
          )}
        </div>

        {/* Agent System Info */}
        {result?.agent_system && (
          <div className="agent-info">
            <h3>🎯 Multi-Agent Analysis</h3>
            <div className="info-grid">
              {result.agent_system.market_trends && (
                <div className="info-card">
                  <strong>📈 Market Trends:</strong>
                  <p>{result.agent_system.market_trends.substring(0, 200)}...</p>
                </div>
              )}
              {result.agent_system.master_strategy && (
                <div className="info-card">
                  <strong>🧠 Strategy:</strong>
                  <p>{result.agent_system.master_strategy.substring(0, 200)}...</p>
                </div>
              )}
              <div className="info-card">
                <strong>⭐ Quality Score:</strong>
                <p>{result.agent_system.critique_score}/10</p>
              </div>
              <div className="info-card">
                <strong>🔄 Iterations:</strong>
                <p>{result.agent_system.iteration_count}</p>
              </div>
            </div>
          </div>
        )}

        {/* Generated Prompts */}
        {result?.prompts && result.prompts.length > 0 && (
          <div className="prompts-section">
            <h3>✨ Generated Prompts</h3>
            <div className="prompts-grid">
              {result.prompts.map((prompt, index) => (
                <div key={`prompt-${index}`} className="prompt-card">
                  <h4>Prompt {index + 1}</h4>
                  <div className="prompt-content">
                    <strong>Positive:</strong>
                    <p>{prompt.positive}</p>
                    {prompt.negative && prompt.negative.length > 0 && (
                      <>
                        <strong>Negative:</strong>
                        <p>{prompt.negative.join(', ')}</p>
                      </>
                    )}
                    {prompt.notes && (
                      <>
                        <strong>Notes:</strong>
                        <p>{prompt.notes}</p>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Generated Images */}
        {images.length > 0 && (
          <div className="images-section">
            <h3>🎨 Generated Images</h3>
            <GalleryGrid
              prompts={result?.prompts ?? null}
              images={images}
              isLoading={isLoading}
            />
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>🤖 AI Agents are collaborating...</p>
            <p className="loading-detail">Vision → Trend → Historian → Analyst → Promptsmith → Critic → Post-Process</p>
          </div>
        )}
      </div>

      <style>{`
        .agent-info {
          margin: 2rem 0;
          padding: 1.5rem;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border-radius: 12px;
          color: white;
        }

        .agent-info h3 {
          margin-top: 0;
          font-size: 1.5rem;
        }

        .info-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 1rem;
          margin-top: 1rem;
        }

        .info-card {
          background: rgba(255, 255, 255, 0.1);
          padding: 1rem;
          border-radius: 8px;
          backdrop-filter: blur(10px);
        }

        .info-card strong {
          display: block;
          margin-bottom: 0.5rem;
          font-size: 0.9rem;
        }

        .info-card p {
          margin: 0;
          font-size: 0.95rem;
          line-height: 1.5;
        }

        .prompts-section {
          margin: 2rem 0;
        }

        .prompts-section h3 {
          margin-bottom: 1rem;
        }

        .prompts-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 1.5rem;
        }

        .prompt-card {
          border: 2px solid #e2e8f0;
          border-radius: 8px;
          padding: 1.5rem;
          background: #f8fafc;
        }

        .prompt-card h4 {
          margin-top: 0;
          color: #667eea;
        }

        .prompt-content strong {
          display: block;
          margin-top: 1rem;
          margin-bottom: 0.5rem;
          color: #4a5568;
          font-size: 0.9rem;
        }

        .prompt-content p {
          margin: 0;
          color: #2d3748;
          line-height: 1.6;
        }

        .images-section {
          margin: 2rem 0;
        }

        .images-section h3 {
          margin-bottom: 1rem;
        }

        .loading-state {
          text-align: center;
          padding: 3rem;
        }

        .spinner {
          border: 4px solid #f3f4f6;
          border-top: 4px solid #667eea;
          border-radius: 50%;
          width: 50px;
          height: 50px;
          animation: spin 1s linear infinite;
          margin: 0 auto 1rem;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .loading-detail {
          font-size: 0.9rem;
          color: #6b7280;
          margin-top: 0.5rem;
        }
      `}</style>
    </section>
  );
}
