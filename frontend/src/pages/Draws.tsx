import { useState, useEffect, useCallback } from 'react';
import { LOTTERIES } from '../mock/data';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

interface DrawRow {
  id_sorteo: string;
  fecha_sorteo: string;
  game_id: string;
  game_name: string;
  combinacion: string;
  numbers?: number[];
  complementario?: number | null;
  reintegro?: number | null;
  joker_combinacion?: string | null;
  premio_bote: string;
}

function formatDate(fecha: string): string {
  if (!fecha) return '—';
  const d = fecha.split(' ')[0];
  if (!d) return fecha;
  const [y, m, day] = d.split('-');
  return new Date(Number(y), Number(m) - 1, Number(day)).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function formatJackpot(premio: string): string {
  if (!premio) return '—';
  const n = Number(premio);
  if (Number.isNaN(n)) return premio;
  if (n >= 1_000_000) return `€${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `€${(n / 1_000).toFixed(1)}K`;
  return `€${n}`;
}

const PAGE_SIZE = 20;

export function Draws() {
  const [lottery, setLottery] = useState('');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [draws, setDraws] = useState<DrawRow[]>([]);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchDraws = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      if (lottery) params.set('lottery', lottery);
      if (from) params.set('from_date', from);
      if (to) params.set('to_date', to);
      params.set('limit', String(PAGE_SIZE));
      params.set('skip', String(skip));
      const res = await fetch(`${API_URL}/api/draws?${params}`);
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail ?? res.statusText);
        setDraws([]);
        setTotal(0);
        return;
      }
      setDraws(data.draws ?? []);
      setTotal(data.total ?? 0);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load draws');
      setDraws([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [lottery, from, to, skip]);

  useEffect(() => {
    fetchDraws();
  }, [fetchDraws]);

  const handleApply = () => setSkip(0);

  const totalPages = Math.ceil(total / PAGE_SIZE) || 1;
  const currentPage = Math.floor(skip / PAGE_SIZE) + 1;

  return (
    <>
      <h1 className="page-title">Draw results</h1>

      <div className="form-row" style={{ marginBottom: 'var(--space-lg)' }}>
        <label htmlFor="draws-lottery">Lottery</label>
        <select id="draws-lottery" value={lottery} onChange={(e) => setLottery(e.target.value)}>
          <option value="">All</option>
          {LOTTERIES.map((l) => (
            <option key={l.id} value={l.id}>{l.name}</option>
          ))}
        </select>
        <label htmlFor="draws-from">From</label>
        <input id="draws-from" type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
        <label htmlFor="draws-to">To</label>
        <input id="draws-to" type="date" value={to} onChange={(e) => setTo(e.target.value)} />
        <button type="button" onClick={handleApply} disabled={loading}>Apply</button>
        <button type="button" disabled>Export</button>
      </div>

      {error && (
        <p style={{ color: 'var(--color-error)', marginBottom: 'var(--space-md)' }}>{error}</p>
      )}

      {loading && draws.length === 0 && (
        <p style={{ color: 'var(--color-text-muted)' }}>Loading draws…</p>
      )}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Lottery</th>
              <th>Numbers</th>
              <th>C</th>
              <th>R</th>
              <th>Joker</th>
              <th>Jackpot</th>
            </tr>
          </thead>
          <tbody>
            {draws.length === 0 && !loading && (
              <tr>
                <td colSpan={7} style={{ color: 'var(--color-text-muted)', padding: 'var(--space-lg)' }}>
                  No draws found. Scrape data from the Scraping page first.
                </td>
              </tr>
            )}
            {draws.map((d) => (
              <tr key={d.id_sorteo}>
                <td>{formatDate(d.fecha_sorteo)}</td>
                <td>{d.game_name}</td>
                <td>{d.numbers?.length ? d.numbers.join(' ') : (d.combinacion || '—')}</td>
                <td>{d.complementario != null ? d.complementario : '—'}</td>
                <td>{d.reintegro != null ? d.reintegro : '—'}</td>
                <td>{d.joker_combinacion ?? '—'}</td>
                <td>{formatJackpot(d.premio_bote)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {total > 0 && (
        <p style={{ marginTop: 'var(--space-md)', color: 'var(--color-text-muted)' }}>
          Page {currentPage} of {totalPages} ({total} total).{' '}
          <button type="button" disabled={skip === 0} onClick={() => setSkip((s) => Math.max(0, s - PAGE_SIZE))}>
            Previous
          </button>
          {' '}
          <button type="button" disabled={skip + PAGE_SIZE >= total} onClick={() => setSkip((s) => s + PAGE_SIZE)}>
            Next
          </button>
        </p>
      )}
    </>
  );
}
