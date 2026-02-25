import { useState } from 'react';
import { LOTTERIES } from '../mock/data';

// Game IDs for the lotteriasyapuestas.es API (La Primitiva confirmed; others TBD)
const GAME_IDS: Record<string, string> = {
  'la-primitiva': 'LAPR',
  'euromillones': 'EMIL',   // confirm on site
  'el-gordo': 'GORD',       // confirm on site
};

// YYYY-MM-DD (from date input) → YYYYMMDD (for API)
function toYyyyMmDd(isoDate: string): string {
  if (!isoDate) return '';
  return isoDate.replace(/-/g, '');
}

function todayIso(): string {
  const d = new Date();
  return d.toISOString().slice(0, 10);
}

function daysAgoIso(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

export function Scraping() {
  const [startDate, setStartDate] = useState('2026-02-01');
  const [endDate, setEndDate] = useState('2026-02-23');
  const [useLast3Days, setUseLast3Days] = useState(false);
  const [lottery, setLottery] = useState<string>('la-primitiva');
  const [status, setStatus] = useState<'idle' | 'running' | 'done' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [importJson, setImportJson] = useState('');
  const [importStatus, setImportStatus] = useState<'idle' | 'running' | 'done' | 'error'>('idle');
  const [importMessage, setImportMessage] = useState('');

  const startYyyyMmDd = useLast3Days ? toYyyyMmDd(daysAgoIso(3)) : toYyyyMmDd(startDate);
  const endYyyyMmDd = useLast3Days ? toYyyyMmDd(todayIso()) : toYyyyMmDd(endDate);

  const apiUrl = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

  const handleStart = async () => {
    setStatus('running');
    setMessage('Scraping…');
    try {
      const params = new URLSearchParams({
        start_date: startYyyyMmDd,
        end_date: endYyyyMmDd,
        lottery,
      });
      const res = await fetch(`${apiUrl}/api/scrape?${params}`);
      const data = await res.json();
      if (!res.ok) {
        setStatus('error');
        setMessage(data.detail ?? res.statusText);
        return;
      }
      setStatus('done');
      setMessage(data.message ?? `Saved ${data.saved ?? 0} draws.`);
    } catch (e) {
      setStatus('error');
      setMessage(e instanceof Error ? e.message : 'Request failed. Is the backend running on ' + apiUrl + '?');
    }
  };

  const handleImport = async () => {
    setImportStatus('running');
    setImportMessage('');
    try {
      const parsed = JSON.parse(importJson);
      if (!Array.isArray(parsed)) {
        setImportStatus('error');
        setImportMessage('Pasted content must be a JSON array of draws.');
        return;
      }
      const res = await fetch(`${apiUrl}/api/scrape/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(parsed),
      });
      const data = await res.json();
      if (!res.ok) {
        setImportStatus('error');
        setImportMessage(data.detail ?? res.statusText);
        return;
      }
      setImportStatus('done');
      setImportMessage(data.message ?? `Saved ${data.saved ?? 0} draws.`);
    } catch (e) {
      setImportStatus('error');
      setImportMessage(e instanceof Error ? e.message : 'Invalid JSON or request failed.');
    }
  };

  return (
    <>
      <h1 className="page-title">Scraping</h1>

      <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
        <p style={{ margin: '0 0 var(--space-md)', color: 'var(--color-text-muted)' }}>
          Fetch historical draws from loteriasyapuestas.es and save to MongoDB. Start with La Primitiva; then add Euromillones and El Gordo.
        </p>
        <div className="form-row">
          <label>
            <input type="checkbox" checked={useLast3Days} onChange={(e) => setUseLast3Days(e.target.checked)} />
            Last 3 days to today (for button scrape)
          </label>
        </div>
        <div className="form-row">
          <label htmlFor="scrape-start">Start date</label>
          <input
            id="scrape-start"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            max={endDate}
            disabled={useLast3Days}
          />
        </div>
        <div className="form-row">
          <label htmlFor="scrape-end">End date</label>
          <input
            id="scrape-end"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            min={startDate}
            disabled={useLast3Days}
          />
        </div>
        <div className="form-row">
          <label htmlFor="scrape-lottery">Lottery</label>
          <select id="scrape-lottery" value={lottery} onChange={(e) => setLottery(e.target.value)}>
            {LOTTERIES.map((l) => (
              <option key={l.id} value={l.id}>{l.name}</option>
            ))}
          </select>
        </div>
        <div className="form-row">
          <button
            type="button"
            className="primary"
            disabled={status === 'running'}
            onClick={handleStart}
          >
            {status === 'running' ? 'Scraping…' : 'Start scraping'}
          </button>
        </div>
        <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
          API: <code style={{ wordBreak: 'break-all' }}>buscadorSorteos?game_id={GAME_IDS[lottery] ?? 'LAPR'}&celebrados=true&fechaInicioInclusiva={startYyyyMmDd}&fechaFinInclusiva={endYyyyMmDd}</code>
        </p>
      </div>

      {(status === 'done' || status === 'error' || status === 'running') && (
        <div className={`card ${status === 'error' ? 'status-error' : ''}`}>
          <h2 style={{ margin: '0 0 var(--space-sm)', fontSize: '1rem' }}>Status</h2>
          <p style={{ margin: 0 }}>{message}</p>
        </div>
      )}

      <div className="card" style={{ marginTop: 'var(--space-lg)' }}>
        <h2 style={{ margin: '0 0 var(--space-sm)', fontSize: '1rem' }}>Import from JSON (when API returns 403)</h2>
        <p style={{ margin: '0 0 var(--space-md)', color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
          If the lottery site blocks the server (403), open the API URL in your browser, copy the full JSON array, and paste below to save to MongoDB.
        </p>
        <textarea
          value={importJson}
          onChange={(e) => setImportJson(e.target.value)}
          placeholder='[{"fecha_sorteo":"...", "id_sorteo":"...", ...}, ...]'
          rows={6}
          style={{ width: '100%', resize: 'vertical', marginBottom: 'var(--space-md)' }}
        />
        <button type="button" className="primary" disabled={importStatus === 'running'} onClick={handleImport}>
          {importStatus === 'running' ? 'Saving…' : 'Save to MongoDB'}
        </button>
        {(importStatus === 'done' || importStatus === 'error') && (
          <p style={{ margin: 'var(--space-md) 0 0', color: importStatus === 'error' ? 'var(--color-error)' : undefined }}>
            {importMessage}
          </p>
        )}
      </div>
    </>
  );
}
