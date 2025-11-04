import type { ImageResult, SynthesisPrompt } from '../types/pipeline';

interface GalleryGridProps {
  prompts: SynthesisPrompt[] | null;
  images: ImageResult[][];
  isLoading: boolean;
}

function resolveImageSource(image: ImageResult): string | null {
  if (image.url) {
    return image.url;
  }
  if (image.b64_json) {
    return `data:image/png;base64,${image.b64_json}`;
  }
  return null;
}

export function GalleryGrid({ prompts, images, isLoading }: GalleryGridProps) {
  if (!prompts?.length) {
    return (
      <section className="card">
        <header className="card-header">
          <div>
            <h2>Gallery</h2>
            <p className="card-subtitle">Generate prompts to review image outputs.</p>
          </div>
        </header>
        <p className="muted">No prompts available yet.</p>
      </section>
    );
  }

  return (
    <section className="card">
      <header className="card-header">
        <div>
          <h2>Gallery</h2>
          <p className="card-subtitle">Review generated prompts and their image variations.</p>
        </div>
      </header>

      <div className="gallery-grid">
        {prompts.map((prompt, promptIndex) => {
          const promptImages = images[promptIndex] ?? [];
          return (
            <article className="gallery-column" key={`prompt-${promptIndex}`}>
              <header className="gallery-header">
                <h3>Prompt {promptIndex + 1}</h3>
                <button
                  type="button"
                  className="secondary"
                  disabled={isLoading}
                  onClick={() => {
                    void navigator.clipboard?.writeText?.(prompt.positive);
                  }}
                >
                  Copy Prompt
                </button>
              </header>

              <pre className="prompt-text">{prompt.positive}</pre>
              {prompt.negative.length ? (
                <p className="muted">Negative: {prompt.negative.join(', ')}</p>
              ) : null}

              <div className="image-stack">
                {promptImages.length ? (
                  promptImages.map((image, imageIndex) => {
                    const src = resolveImageSource(image);
                    if (!src) {
                      return (
                        <p className="muted" key={`image-${promptIndex}-${imageIndex}`}>
                          No preview available.
                        </p>
                      );
                    }
                    return (
                      <figure className="image-card" key={`image-${promptIndex}-${imageIndex}`}>
                        <img src={src} alt={`Prompt ${promptIndex + 1} result ${imageIndex + 1}`} />
                      </figure>
                    );
                  })
                ) : (
                  <p className="muted">Generate images to see results here.</p>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
