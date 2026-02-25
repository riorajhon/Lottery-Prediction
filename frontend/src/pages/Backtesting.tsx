import { useState } from 'react';
import { LOTTERIES, MODELS, WHEEL_TYPES } from '../mock/data';

export function Backtesting() {
  const [lottery, setLottery] = useState('euromillones');
  const [model, setModel] = useState('Random Forest');
  const [wheel, setWheel] = useState('Abbreviated Wheel');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [running, setRunning] = useState(false);
  const [hasReport, setHasReport] = useState(false);

  const runBacktest = () => {
    setRunning(true);
    setTimeout(() => { setRunning(false); setHasReport(true); }, 1500);
  };

  return (
    <>
      <h1 className="page-title">Backtesting</h1>

      <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
        <div className="form-row">
          <label htmlFor="bt-lottery">Lottery</label>
          <select id="bt-lottery" value={lottery} onChange={(e) => setLottery(e.target.value)}>
            {LOTTERIES.map((l) => (
              <option key={l.id} value={l.id}>{l.name}</option>
            ))}
          </select>
        </div>
        <div className="form-row">
          <label htmlFor="bt-model">Model</label>
          <select id="bt-model" value={model} onChange={(e) => setModel(e.target.value)}>
            {MODELS.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
          <label htmlFor="bt-wheel">Wheel</label>
          <select id="bt-wheel" value={wheel} onChange={(e) => setWheel(e.target.value)}>
            {WHEEL_TYPES.map((w) => (
              <option key={w} value={w}>{w}</option>
            ))}
          </select>
        </div>
        <div className="form-row">
          <label htmlFor="bt-from">From</label>
          <input id="bt-from" type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
          <label htmlFor="bt-to">To</label>
          <input id="bt-to" type="date" value={to} onChange={(e) => setTo(e.target.value)} />
        </div>
        <div className="form-row">
          <button type="button" className="primary" disabled={running} onClick={runBacktest}>
            {running ? 'Running simulation…' : 'Run backtest'}
          </button>
        </div>
      </div>

      <div className="card">
        <h2 style={{ margin: '0 0 var(--space-md)', fontSize: '1rem' }}>Report (placeholder)</h2>
        {hasReport ? (
          <>
            <p>Summary: X draws, Y tickets total, Z wins, ROI %</p>
            <p>Hit rate: 5+2: n%, 5+1: n%, …</p>
            <p style={{ color: 'var(--color-text-muted)' }}>Chart: placeholder for P&L over time</p>
            <button type="button" style={{ marginTop: 'var(--space-md)' }}>Export report</button>
          </>
        ) : (
          <p style={{ color: 'var(--color-text-muted)' }}>
            Select lottery, model, wheel and date range, then run backtest. Results will appear here when backend is connected.
          </p>
        )}
      </div>
    </>
  );
}
