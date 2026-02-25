import { useState } from 'react';
import { Link } from 'react-router-dom';
import { LOTTERIES, WHEEL_TYPES } from '../mock/data';

export function Wheeling() {
  const [lottery, setLottery] = useState('euromillones');
  const [wheelType, setWheelType] = useState('Abbreviated Wheel');
  const [source, setSource] = useState<'manual' | 'prediction'>('prediction');
  const [manualInput, setManualInput] = useState('1 5 12 18 23 31 42 7 9');
  const [keyNumbers, setKeyNumbers] = useState('7 9');
  const [lines] = useState<{ main: number[]; stars: number[] }[]>([]);

  return (
    <>
      <h1 className="page-title">Wheeling</h1>

      <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
        <div className="form-row">
          <label htmlFor="wheel-lottery">Lottery</label>
          <select id="wheel-lottery" value={lottery} onChange={(e) => setLottery(e.target.value)}>
            {LOTTERIES.map((l) => (
              <option key={l.id} value={l.id}>{l.name}</option>
            ))}
          </select>
        </div>
        <div className="form-row">
          <label htmlFor="wheel-type">Wheel type</label>
          <select id="wheel-type" value={wheelType} onChange={(e) => setWheelType(e.target.value)}>
            {WHEEL_TYPES.map((w) => (
              <option key={w} value={w}>{w}</option>
            ))}
          </select>
        </div>
        <div className="form-row">
          <label>Numbers source</label>
          <label>
            <input type="radio" name="source" checked={source === 'manual'} onChange={() => setSource('manual')} />
            Manual
          </label>
          <label>
            <input type="radio" name="source" checked={source === 'prediction'} onChange={() => setSource('prediction')} />
            From last prediction
          </label>
        </div>
        {source === 'manual' && (
          <div className="form-row">
            <label htmlFor="wheel-manual">Manual input</label>
            <input id="wheel-manual" type="text" value={manualInput} onChange={(e) => setManualInput(e.target.value)} style={{ minWidth: 280 }} placeholder="1 5 12 18 23 31 42 7 9" />
          </div>
        )}
        {wheelType === 'Key Number Wheel' && (
          <div className="form-row">
            <label htmlFor="wheel-key">Key numbers</label>
            <input id="wheel-key" type="text" value={keyNumbers} onChange={(e) => setKeyNumbers(e.target.value)} placeholder="7 9" />
          </div>
        )}
        <div className="form-row">
          <button type="button" className="primary">Generate lines</button>
        </div>
      </div>

      <div className="card">
        <h2 style={{ margin: '0 0 var(--space-md)', fontSize: '1rem' }}>Generated lines (placeholder)</h2>
        {lines.length === 0 ? (
          <p style={{ color: 'var(--color-text-muted)' }}>
            Line 1: — — — — — (— —)<br />
            Line 2: — — — — — (— —)<br />
            … Generate lines when backend is connected.
          </p>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {lines.map((line, i) => (
              <li key={i}>Line {i + 1}: {line.main.join(' ')} ({line.stars.join(' ')})</li>
            ))}
          </ul>
        )}
        <p style={{ marginTop: 'var(--space-md)', color: 'var(--color-text-muted)' }}>
          Summary: X lines, estimated cost €Y
        </p>
        <div style={{ display: 'flex', gap: 'var(--space-sm)', marginTop: 'var(--space-md)' }}>
          <button type="button">Copy all</button>
          <button type="button">Export CSV</button>
          <Link to="/betting"><button type="button">Send to Betting</button></Link>
        </div>
      </div>
    </>
  );
}
