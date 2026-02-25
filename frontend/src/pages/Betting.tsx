import { useState } from 'react';
import { Link } from 'react-router-dom';
import { MOCK_PENDING_BETS } from '../mock/data';

export function Betting() {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [confirmOpen, setConfirmOpen] = useState(false);

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };
  const selectAll = () => setSelected(new Set(MOCK_PENDING_BETS.map((b) => b.id)));
  const removeSelected = () => setSelected(new Set());

  const total = MOCK_PENDING_BETS.filter((b) => selected.has(b.id)).length * 2.5;
  const openConfirm = () => selected.size > 0 && setConfirmOpen(true);

  return (
    <>
      <h1 className="page-title">Betting</h1>

      <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
        <p style={{ margin: '0 0 var(--space-md)' }}>
          Balance: <strong>€---</strong> (placeholder)
        </p>
        <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
          <button type="button">Refresh</button>
          <button type="button">Login to official</button>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
        <h2 style={{ margin: '0 0 var(--space-md)', fontSize: '1rem' }}>Pending bets</h2>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {MOCK_PENDING_BETS.map((b) => (
            <li key={b.id} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)', padding: 'var(--space-sm) 0', borderBottom: '1px solid var(--color-border)' }}>
              <input type="checkbox" checked={selected.has(b.id)} onChange={() => toggle(b.id)} aria-label={`Select bet ${b.id}`} />
              <span>{b.lottery}</span>
              <span>{b.drawDate}</span>
              <span>Line: {b.line.join(' ')} ({b.stars.join(' ')})</span>
              <span>{b.amount}</span>
            </li>
          ))}
        </ul>
        <div style={{ display: 'flex', gap: 'var(--space-sm)', marginTop: 'var(--space-md)' }}>
          <button type="button" onClick={selectAll}>Select all</button>
          <button type="button" onClick={removeSelected}>Remove selected</button>
          <button type="button" className="primary" disabled={selected.size === 0} onClick={openConfirm}>
            Place selected bets
          </button>
        </div>
      </div>

      {confirmOpen && (
        <div role="dialog" aria-modal="true" aria-labelledby="confirm-title" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10 }}>
          <div className="card" style={{ maxWidth: 400, margin: 16 }}>
            <h2 id="confirm-title" style={{ margin: '0 0 var(--space-md)' }}>Confirm placement</h2>
            <p>You are about to place {selected.size} bet(s) for €{total.toFixed(2)}. Confirm?</p>
            <div style={{ display: 'flex', gap: 'var(--space-sm)', justifyContent: 'flex-end' }}>
              <button type="button" onClick={() => setConfirmOpen(false)}>Cancel</button>
              <button type="button" className="primary" onClick={() => setConfirmOpen(false)}>Confirm and place</button>
            </div>
          </div>
        </div>
      )}

      <p>
        Recent: <Link to="/betting/history">Betting history</Link>
      </p>
    </>
  );
}
