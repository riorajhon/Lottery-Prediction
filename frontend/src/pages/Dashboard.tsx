import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import { CALENDAR_EVENTS, MOCK_DRAWS, MOCK_DATA_STATUS, NEXT_DRAWS } from '../mock/data';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

interface EuromillonesFrequencySummary {
  draw_date: string;
  main_frequency_counts?: number[];
  star_frequency_counts?: number[];
}

export function Dashboard() {
  const [euromillonesFreq, setEuromillonesFreq] = useState<EuromillonesFrequencySummary | null>(null);
  const [freqLoading, setFreqLoading] = useState(false);
  const [freqError, setFreqError] = useState('');

  useEffect(() => {
    const load = async () => {
      setFreqLoading(true);
      setFreqError('');
      try {
        const res = await fetch(`${API_URL}/api/euromillones/features?limit=1&skip=0`);
        const data = await res.json();
        if (!res.ok) {
          setFreqError(data.detail ?? res.statusText);
          setEuromillonesFreq(null);
          return;
        }
        const row = (data.features ?? [])[0] as EuromillonesFrequencySummary | undefined;
        setEuromillonesFreq(row ?? null);
      } catch (e) {
        setFreqError(e instanceof Error ? e.message : 'Failed to load Euromillones frequencies');
        setEuromillonesFreq(null);
      } finally {
        setFreqLoading(false);
      }
    };
    load();
  }, []);

  const topMain = (() => {
    if (!euromillonesFreq?.main_frequency_counts) return [];
    return euromillonesFreq.main_frequency_counts
      .map((count, idx) => ({ number: idx + 1, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  })();

  const topStars = (() => {
    if (!euromillonesFreq?.star_frequency_counts) return [];
    return euromillonesFreq.star_frequency_counts
      .map((count, idx) => ({ number: idx + 1, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 6);
  })();

  const maxMainCount = topMain.reduce((max, x) => (x.count > max ? x.count : max), 0) || 1;
  const maxStarCount = topStars.reduce((max, x) => (x.count > max ? x.count : max), 0) || 1;

  return (
    <>
      <h1 className="page-title">Panel</h1>

      <div className="cards-grid">
        <section className="card">
          <h2 style={{ margin: '0 0 var(--space-md)', fontSize: '1rem' }}>Próximos sorteos</h2>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {NEXT_DRAWS.map((d) => (
              <li key={d.lottery} style={{ padding: 'var(--space-xs) 0' }}>
                {d.lottery} — {d.day}
              </li>
            ))}
          </ul>
        </section>
        <section className="card">
          <h2 style={{ margin: '0 0 var(--space-md)', fontSize: '1rem' }}>Estado de datos</h2>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {MOCK_DATA_STATUS.map((row) => (
              <li key={row.lottery} style={{ padding: 'var(--space-xs) 0' }}>
                {row.lottery} <span className="status-ok">✓</span>
              </li>
            ))}
          </ul>
        </section>
        <section className="card">
          <h2 style={{ margin: '0 0 var(--space-md)', fontSize: '1rem' }}>Resultados</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
            <Link to="/resultados/la-primitiva"><button type="button" className="primary">La Primitiva</button></Link>
            <Link to="/resultados/euromillones"><button type="button">Euromillones</button></Link>
            <Link to="/resultados/el-gordo"><button type="button">El Gordo</button></Link>
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

      <section className="card" style={{ marginTop: 'var(--space-lg)' }}>
        <h2 style={{ margin: '0 0 var(--space-md)', fontSize: '1rem' }}>Frecuencias Euromillones (test)</h2>
        {freqError && (
          <p style={{ color: 'var(--color-error)', marginTop: 0 }}>{freqError}</p>
        )}
        {freqLoading && !euromillonesFreq && (
          <p style={{ marginTop: 0 }}>Cargando frecuencias…</p>
        )}
        {!freqLoading && !freqError && !euromillonesFreq && (
          <p style={{ marginTop: 0 }}>No hay datos de predicción para Euromillones.</p>
        )}
        {euromillonesFreq && (
          <>
            <p style={{ marginTop: 0, marginBottom: 'var(--space-md)', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
              Basado en el último sorteo con datos de predicción ({euromillonesFreq.draw_date}).
            </p>
            <div className="resultados-features-chart-grid">
              <div>
                <h3 className="resultados-features-chart-title">Top 10 números principales</h3>
                <ul className="resultados-features-chart-list">
                  {topMain.map((f) => (
                    <li key={f.number} className="resultados-features-chart-item">
                      <span className="resultados-features-chart-label">{f.number}</span>
                      <div className="resultados-features-chart-bar-wrap">
                        <div
                          className="resultados-features-chart-bar"
                          style={{ width: `${(f.count / maxMainCount) * 100 || 0}%` }}
                        />
                      </div>
                      <span className="resultados-features-chart-count">{f.count}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="resultados-features-chart-title">Top 6 estrellas</h3>
                <ul className="resultados-features-chart-list">
                  {topStars.map((f) => (
                    <li key={f.number} className="resultados-features-chart-item">
                      <span className="resultados-features-chart-label">{f.number}</span>
                      <div className="resultados-features-chart-bar-wrap">
                        <div
                          className="resultados-features-chart-bar resultados-features-chart-bar--star"
                          style={{ width: `${(f.count / maxStarCount) * 100 || 0}%` }}
                        />
                      </div>
                      <span className="resultados-features-chart-count">{f.count}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </>
        )}
      </section>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-lg)', marginTop: 'var(--space-lg)' }}>
        <section className="card">
          <h2 style={{ margin: '0 0 var(--space-md)', fontSize: '1rem' }}>Últimos resultados</h2>
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
          <h2 style={{ margin: '0 0 var(--space-md)', fontSize: '1rem' }}>Resultados</h2>
          <p style={{ color: 'var(--color-text-muted)', margin: 0 }}>
            Ver sorteos de La Primitiva, Euromillones y El Gordo en el menú.
          </p>
        </section>
      </div>
    </>
  );
}
