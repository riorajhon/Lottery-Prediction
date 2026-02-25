import { useState } from 'react';
import { LOTTERIES, WHEEL_TYPES } from '../mock/data';

export function Settings() {
  const [defaultLottery, setDefaultLottery] = useState('euromillones');
  const [defaultWheel, setDefaultWheel] = useState('Abbreviated Wheel');
  const [agendaView, setAgendaView] = useState<'week' | 'month'>('month');
  const [language, setLanguage] = useState('en');

  return (
    <>
      <h1 className="page-title">Settings</h1>

      <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
        <h2 style={{ margin: '0 0 var(--space-md)', fontSize: '1.1rem' }}>Preferences</h2>
        <div className="form-row">
          <label htmlFor="set-lottery">Default lottery</label>
          <select id="set-lottery" value={defaultLottery} onChange={(e) => setDefaultLottery(e.target.value)}>
            {LOTTERIES.map((l) => (
              <option key={l.id} value={l.id}>{l.name}</option>
            ))}
          </select>
        </div>
        <div className="form-row">
          <label htmlFor="set-wheel">Default wheel</label>
          <select id="set-wheel" value={defaultWheel} onChange={(e) => setDefaultWheel(e.target.value)}>
            {WHEEL_TYPES.map((w) => (
              <option key={w} value={w}>{w}</option>
            ))}
          </select>
        </div>
        <div className="form-row">
          <label>Agenda view</label>
          <label>
            <input type="radio" name="agenda" checked={agendaView === 'week'} onChange={() => setAgendaView('week')} />
            Week
          </label>
          <label>
            <input type="radio" name="agenda" checked={agendaView === 'month'} onChange={() => setAgendaView('month')} />
            Month
          </label>
        </div>
        <div className="form-row">
          <label htmlFor="set-lang">Language</label>
          <select id="set-lang" value={language} onChange={(e) => setLanguage(e.target.value)}>
            <option value="en">English</option>
            <option value="es">Español</option>
          </select>
        </div>
        <div className="form-row">
          <button type="button" className="primary">Save</button>
        </div>
      </div>

      <div className="card">
        <h2 style={{ margin: '0 0 var(--space-md)', fontSize: '1.1rem' }}>Integrations (placeholders)</h2>
        <p style={{ color: 'var(--color-text-muted)', margin: 0 }}>
          Official lottery login: configure in secure backend. No credentials stored in UI.
        </p>
        <p style={{ color: 'var(--color-text-muted)', margin: 'var(--space-sm) 0 0' }}>
          CAPTCHA handling: Manual or external service (info only).
        </p>
      </div>
    </>
  );
}
