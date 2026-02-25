import { Link } from 'react-router-dom';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import { CALENDAR_EVENTS, MOCK_DRAWS, MOCK_DATA_STATUS, NEXT_DRAWS } from '../mock/data';

export function Dashboard() {
  return (
    <>
      <h1 className="page-title">Dashboard</h1>

      <div className="cards-grid">
        <section className="card">
          <h2 style={{ margin: '0 0 var(--space-md)', fontSize: '1rem' }}>Next draws</h2>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {NEXT_DRAWS.map((d) => (
              <li key={d.lottery} style={{ padding: 'var(--space-xs) 0' }}>
                {d.lottery} — {d.day}
              </li>
            ))}
          </ul>
        </section>
        <section className="card">
          <h2 style={{ margin: '0 0 var(--space-md)', fontSize: '1rem' }}>Data status</h2>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {MOCK_DATA_STATUS.map((row) => (
              <li key={row.lottery} style={{ padding: 'var(--space-xs) 0' }}>
                {row.lottery} <span className="status-ok">✓</span>
              </li>
            ))}
          </ul>
        </section>
        <section className="card">
          <h2 style={{ margin: '0 0 var(--space-md)', fontSize: '1rem' }}>Quick actions</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
            <Link to="/predictions"><button type="button" className="primary">New prediction</button></Link>
            <Link to="/wheeling"><button type="button">Open wheel</button></Link>
            <Link to="/backtesting"><button type="button">Backtest</button></Link>
          </div>
        </section>
      </div>

      <div className="calendar-wrap">
        <FullCalendar
          plugins={[dayGridPlugin]}
          initialView="dayGridMonth"
          events={CALENDAR_EVENTS}
          headerToolbar={{ left: 'prev,next', center: 'title', right: '' }}
          height="auto"
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-lg)', marginTop: 'var(--space-lg)' }}>
        <section className="card">
          <h2 style={{ margin: '0 0 var(--space-md)', fontSize: '1rem' }}>Recent results</h2>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {MOCK_DRAWS.slice(0, 3).map((d) => (
              <li key={d.id} style={{ padding: 'var(--space-sm) 0', borderBottom: '1px solid var(--color-border)' }}>
                <strong>{d.date}</strong> {d.lottery}: {d.mainNumbers.join(' ')}
                {d.starsOrBonus.length ? ` (${d.starsOrBonus.join(' ')})` : ''} — {d.jackpot}
              </li>
            ))}
          </ul>
        </section>
        <section className="card">
          <h2 style={{ margin: '0 0 var(--space-md)', fontSize: '1rem' }}>Last predictions / Backtest</h2>
          <p style={{ color: 'var(--color-text-muted)', margin: 0 }}>
            Placeholder. Generate a prediction or run a backtest to see summary here.
          </p>
        </section>
      </div>
    </>
  );
}
