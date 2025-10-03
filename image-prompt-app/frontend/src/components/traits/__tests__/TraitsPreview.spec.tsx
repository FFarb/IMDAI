import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import TraitsPreview from '../TraitsPreview';
import type { DatasetTraits } from '../../../types/discovery';

const sampleTraits: DatasetTraits = {
  session_id: 'session',
  palette: [
    { hex: '#FFAA00', weight: 0.3 },
    { hex: '#3366FF', weight: 0.2 },
    { hex: '#55CC88', weight: 0.15 },
    { hex: '#FF6699', weight: 0.15 },
    { hex: '#AA55FF', weight: 0.1 },
    { hex: '#223344', weight: 0.1 },
  ],
  motifs: ['stars', 'clouds', 'sparkles', 'playful', 'pastel', 'geometric', 'butterflies', 'rainbows'],
  line_weight: 'regular',
  outline: 'clean',
  typography: ['rounded lettering accents'],
  composition: ['centered', 'subtle lattice'],
  audience_modes: [],
};

test('renders palette and motifs and copies hex to clipboard', async () => {
  const writeText = vi.fn();
  Object.assign(navigator, { clipboard: { writeText } });

  render(<TraitsPreview traits={sampleTraits} />);
  const paletteButton = screen.getByRole('button', { name: /#FFAA00/i });
  await userEvent.click(paletteButton);
  expect(writeText).toHaveBeenCalledWith('#FFAA00');
  expect(screen.getByText(/stars/)).toBeInTheDocument();
});

test('shows loading and empty states', () => {
  render(<TraitsPreview traits={null} loading />);
  expect(screen.getByText(/Analyzing traits/)).toBeInTheDocument();
  render(<TraitsPreview traits={null} />);
  expect(screen.getByText(/Traits not available yet/)).toBeInTheDocument();
});

test('renders typography fallback when absent', () => {
  const traits = { ...sampleTraits, typography: [] };
  render(<TraitsPreview traits={traits} />);
  expect(screen.getByText(/avoid text/i)).toBeInTheDocument();
});
