import { useState } from 'react';
import { Link } from 'react-router-dom';
import { LOTTERIES, MODELS } from '../mock/data';

export function Predictions() {
  const [lottery, setLottery] = useState('euromillones');
  const [model, setModel] = useState('Random Forest');
  const [hotCold, setHotCold] = useState(true);
  const [lastN, setLastN] = useState(52);
  const [loading, setLoading] = useState(false);

  return (
    <>
      <h1 className="page-title">Predictions</h1>

      <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
        <div className="form-row">
          <label htmlFor="pred-lottery">Lottery</label>
          <select id="pred-lottery" value={lottery} onChange={(e) => setLottery(e.target.value)}>
            {LOTTERIES.map((l) => (
              <option key={l.id} value={l.id}>{l.name}</option>
            ))}
          </select>
        </div>
        <div className="form-row">
          <label>Model</label>
          <div style={{ display: 'flex', gap: 'var(--space-sm)', flexWrap: 'wrap' }}>
            {MODELS.map((m) => (
              <button
                key={m}
                type="button"
                className={model === m ? 'primary' : ''}
                onClick={() => setModel(m)}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
        <div className="form-row">
          <label>
            <input type="checkbox" checked={hotCold} onChange={(e) => setHotCold(e.target.checked)} />
            Hot/cold filter
          </label>
          <label>
            Use last N draws: <input type="number" min={1} max={200} value={lastN} onChange={(e) => setLastN(Number(e.target.value))} style={{ width: 60 }} />
          </label>
        </div>
        <div className="form-row">
          <button type="button" className="primary" disabled={loading} onClick={() => setLoading(true)}>
            {loading ? 'Generating…' : 'Generate prediction'}
          </button>
        </div>
      </div>

      <div className="card">
        <h2 style={{ margin: '0 0 var(--space-md)', fontSize: '1rem' }}>Result (placeholder)</h2>
        <p style={{ color: 'var(--color-text-muted)' }}>
          Recommended numbers: — — — — — (stars: — —)
        </p>
        <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
          Select lottery and model, then generate. Backend will be connected later.
        </p>
        <div style={{ display: 'flex', gap: 'var(--space-sm)', marginTop: 'var(--space-md)' }}>
          <button type="button">Copy</button>
          <Link to="/wheeling"><button type="button">Send to Wheeling</button></Link>
        </div>
      </div>
    </>
  );
}
