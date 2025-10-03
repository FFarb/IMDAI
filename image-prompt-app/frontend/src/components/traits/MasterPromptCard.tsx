import { useState } from 'react';
import type { MasterPromptPayload } from '../../types/discovery';

interface MasterPromptCardProps {
  prompt: MasterPromptPayload | null;
}

export default function MasterPromptCard({ prompt }: MasterPromptCardProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!prompt) return;
    try {
      await navigator.clipboard.writeText(prompt.prompt_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (error) {
      console.warn('Failed to copy prompt', error);
    }
  };

  return (
    <div className="master-prompt-card">
      <div className="card-header">
        <h4>Master Prompt</h4>
        <button type="button" onClick={handleCopy} disabled={!prompt}>
          {copied ? 'Copied' : 'Copy text'}
        </button>
      </div>
      <textarea readOnly value={prompt ? prompt.prompt_text : ''} placeholder="Autofill to preview master prompt" />
      <details>
        <summary>Prompt JSON</summary>
        <pre>{prompt ? JSON.stringify(prompt.prompt_json, null, 2) : '// run Autofill to render JSON'}</pre>
      </details>
    </div>
  );
}
