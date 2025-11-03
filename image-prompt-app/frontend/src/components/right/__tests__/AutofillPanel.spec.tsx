import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { MockedFunction } from 'vitest';
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';

import AutofillPanel from '../AutofillPanel';
import type { AutofillResponse } from '../../../types/autofill';
import { postOneClickGenerate, postResearch } from '../../../api/autofill';

vi.mock('../../../api/autofill', () => ({
  postResearch: vi.fn(),
  postOneClickGenerate: vi.fn(),
}));

const writeText = vi.fn();

beforeAll(() => {
  Object.defineProperty(navigator, 'clipboard', {
    value: { writeText },
    configurable: true,
  });
});

beforeEach(() => {
  vi.clearAllMocks();
  writeText.mockClear();
});

const sampleAutofill: AutofillResponse = {
  traits: {
    palette: [
      { hex: '#FFAA00', weight: 0.2 },
      { hex: '#FFEEDD', weight: 0.2 },
      { hex: '#112233', weight: 0.2 },
      { hex: '#445566', weight: 0.2 },
      { hex: '#778899', weight: 0.2 },
    ],
    motifs: ['cloud', 'moon', 'star', 'sparkle', 'planet', 'animal', 'pattern', 'kawaii'],
    line_weight: 'thin',
    outline: 'clean',
    typography: ['rounded sans'],
    composition: ['centered'],
    audience: 'kids',
    age: '0–2',
    mood: ['soft', 'calm'],
    negative: ['photo-realism'],
    seed_examples: ['example one', 'example two'],
    sources: [
      { title: 'Example Source', url: 'https://example.com' },
      { title: 'Gallery Link', url: 'https://gallery.example.com' },
    ],
  },
  master_prompt_text:
    'Minimal safari nursery scene, transparent background, no shadows, no gradients, no textures, clean vector edges, centered standalone composition',
  master_prompt_json: {
    subject: 'Minimal safari nursery scene',
    palette: ['#FFAA00'],
    motifs: ['cloud', 'moon'],
    line: 'thin',
    outline: 'clean',
    typography: ['rounded sans'],
    composition: ['centered'],
    mood: ['soft', 'calm'],
    negative: ['photo-realism'],
  },
};

describe('AutofillPanel', () => {
  it('runs research and renders traits with copy actions', async () => {
    (postResearch as MockedFunction<typeof postResearch>).mockResolvedValue({
      data: sampleAutofill,
      warning: null,
    });
    const onShowToast = vi.fn();

    render(<AutofillPanel onShowToast={onShowToast} refreshGallery={vi.fn()} />);

    fireEvent.change(screen.getByLabelText(/тема/i), { target: { value: 'baby safari' } });
    fireEvent.click(screen.getByRole('button', { name: /research & fill/i }));

    await screen.findByText(/line weight/i);
    expect(postResearch).toHaveBeenCalledWith({
      topic: 'baby safari',
      audience: 'kids',
      age: '0–2',
      flags: { use_web: true, avoid_brands: true, kids_safe: true },
      images_n: 4,
    });

    expect(screen.getByText('#FFAA00')).toBeInTheDocument();
    expect(screen.getByText('cloud')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Example Source' })).toHaveAttribute('href', 'https://example.com');

    fireEvent.click(screen.getByRole('button', { name: /copy text/i }));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(sampleAutofill.master_prompt_text));
    expect(onShowToast).toHaveBeenCalled();
  });

});
