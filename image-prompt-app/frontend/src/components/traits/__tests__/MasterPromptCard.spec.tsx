import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import MasterPromptCard from '../MasterPromptCard';
import type { MasterPromptPayload } from '../../../types/discovery';

const payload: MasterPromptPayload = {
  prompt_text: 'transparent background, Subject & Motifs: test',
  prompt_json: {
    audience_modes: ['Baby'],
    palette: [{ hex: '#FFFFFF', weight: 1 }],
    motifs: ['stars'],
    line: 'regular',
    outline: 'clean',
    typography: ['rounded lettering accents'],
    composition: ['centered'],
    constraints: ['transparent background'],
    mood: 'soft',
    negative: 'photo-realism, photographic textures, noise, background patterns, brand logos, trademark words',
  },
};

test('renders prompt text and json', () => {
  render(<MasterPromptCard prompt={payload} />);
  expect(screen.getByRole('textbox')).toHaveValue(expect.stringContaining('transparent background'));
  expect(screen.getByText(/Prompt JSON/)).toBeInTheDocument();
});

test('copies prompt text to clipboard', async () => {
  const writeText = vi.fn();
  Object.assign(navigator, { clipboard: { writeText } });

  render(<MasterPromptCard prompt={payload} />);
  await userEvent.click(screen.getByRole('button', { name: /Copy text/i }));
  expect(writeText).toHaveBeenCalledWith(payload.prompt_text);
});

test('shows placeholder when prompt missing', () => {
  render(<MasterPromptCard prompt={null} />);
  expect(screen.getByRole('textbox')).toHaveValue('');
});
