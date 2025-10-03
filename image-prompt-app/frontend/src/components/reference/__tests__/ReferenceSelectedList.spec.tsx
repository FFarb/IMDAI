import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import ReferenceSelectedList from '../ReferenceSelectedList';
import type { Reference } from '../../../types/discovery';

const baseReference: Reference = {
  id: 'ref-1',
  session_id: 'session',
  site: 'local',
  url: 'http://example.com',
  thumb_url: 'data:image/png;base64,',
  title: 'Sample reference',
  license: null,
  author: null,
  width: 100,
  height: 100,
  p_hash: null,
  flags: { watermark: false, nsfw: false, brand_risk: false, busy_bg: false },
  scores: { quality: 1, risk: 0, outline: 0, flatness: 0 },
  status: 'selected',
  weight: 1.0,
};

function Harness() {
  const [references, setReferences] = useState<Reference[]>([baseReference]);
  const handleStar = (reference: Reference) => {
    const next = reference.weight === 1 ? 1.5 : reference.weight === 1.5 ? 2.0 : 1.0;
    setReferences((prev) => prev.map((item) => (item.id === reference.id ? { ...item, weight: next } : item)));
  };
  const remove = (reference: Reference) => {
    setReferences((prev) => prev.filter((item) => item.id !== reference.id));
  };
  return (
    <ReferenceSelectedList
      references={references}
      focusedId={references[0]?.id ?? null}
      onFocusChange={() => undefined}
      onHide={remove}
      onDelete={remove}
      onStar={handleStar}
      onMove={() => undefined}
      onInfo={() => undefined}
      onCopyPalette={() => undefined}
    />
  );
}

it('cycles star weight through presets', async () => {
  render(<Harness />);
  const user = userEvent.setup();
  const starButton = screen.getByRole('button', { name: /★ 1.0/ });

  await user.click(starButton);
  expect(screen.getByRole('button', { name: /★ 1.5/ })).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: /★ 1.5/ }));
  expect(screen.getByRole('button', { name: /★ 2.0/ })).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: /★ 2.0/ }));
  expect(screen.getByRole('button', { name: /★ 1.0/ })).toBeInTheDocument();
});

it('removes reference when hide is clicked', async () => {
  render(<Harness />);
  const user = userEvent.setup();
  await user.click(screen.getByRole('button', { name: /Hide/i }));
  expect(screen.queryByText(/Sample reference/)).not.toBeInTheDocument();
});

it('removes reference when delete is clicked', async () => {
  render(<Harness />);
  const user = userEvent.setup();
  await user.click(screen.getByRole('button', { name: /Delete/i }));
  expect(screen.queryByText(/Sample reference/)).not.toBeInTheDocument();
});
