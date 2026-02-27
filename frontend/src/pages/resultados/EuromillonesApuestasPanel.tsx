import { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import type { ApuestasWindow } from './useApuestasSeries';
import { useApuestasSeries } from './useApuestasSeries';

const WINDOWS: { key: ApuestasWindow; label: string }[] = [
  { key: '3m', label: '3 meses' },
  { key: '6m', label: '6 meses' },
  { key: '1y', label: '1 año' },
  { key: 'all', label: 'Todo' },
];

export function EuromillonesApuestasPanel() {
  const [windowKey, setWindowKey] = useState<ApuestasWindow>('3m');
  const { points: allPoints, loading, error } = useApuestasSeries('euromillones', windowKey);
  const [weekdayFilter, setWeekdayFilter] = useState<'all' | 'martes' | 'viernes'>('all');

  const filteredPoints = (() => {
    if (!allPoints.length || weekdayFilter === 'all') return allPoints;
    return allPoints.filter((p) => {
      const [y, m, d] = p.date.split('-').map((v) => Number(v));
      const jsDate = new Date(y, m - 1, d);
      const day = jsDate.getDay(); // 0=Sun,1=Mon,...,2=Tue,5=Fri
      if (weekdayFilter === 'martes') return day === 2;
      if (weekdayFilter === 'viernes') return day === 5;
      return true;
    });
  })();

  const hasData = filteredPoints.length > 0;

  const combinedData = (() => {
    if (!hasData) return [];
    const maxApuestas = filteredPoints.reduce(
      (max, p) => (p.apuestas != null && p.apuestas > max ? p.apuestas : max),
      0,
    );
    const maxPremios = filteredPoints.reduce(
      (max, p) => (p.premios != null && p.premios > max ? p.premios : max),
      0,
    );
    const maxBote = filteredPoints.reduce(
      (max, p) => (p.premio_bote != null && p.premio_bote > max ? p.premio_bote : max),
      0,
    );
    return filteredPoints.map((p) => ({
      ...p,
      apuestas_norm:
        p.apuestas != null && maxApuestas > 0 ? (p.apuestas / maxApuestas) * 100 : null,
      premios_norm:
        p.premios != null && maxPremios > 0 ? (p.premios / maxPremios) * 100 : null,
      bote_norm:
        p.premio_bote != null && maxBote > 0 ? (p.premio_bote / maxBote) * 100 : null,
    }));
  })();

  return (
    <section className="card resultados-apuestas-card">
      <div className="resultados-apuestas-header">
        <h2 style={{ margin: 0, fontSize: '1rem' }}>Gráficos Euromillones</h2>
        <div className="resultados-apuestas-controls">
          <div className="resultados-apuestas-window-toggle" aria-label="Rango temporal">
            {WINDOWS.map((w) => (
              <button
                key={w.key}
                type="button"
                className={`resultados-apuestas-window-btn ${
                  windowKey === w.key ? 'resultados-apuestas-window-btn--active' : ''
                }`}
                onClick={() => setWindowKey(w.key)}
              >
                {w.label}
              </button>
            ))}
          </div>
          <div className="resultados-apuestas-weekday-toggle" aria-label="Filtrar por día de la semana">
            <button
              type="button"
              className={`resultados-apuestas-window-btn ${
                weekdayFilter === 'all' ? 'resultados-apuestas-window-btn--active' : ''
              }`}
              onClick={() => setWeekdayFilter('all')}
            >
              Todos
            </button>
            <button
              type="button"
              className={`resultados-apuestas-window-btn ${
                weekdayFilter === 'martes' ? 'resultados-apuestas-window-btn--active' : ''
              }`}
              onClick={() => setWeekdayFilter('martes')}
            >
              Martes
            </button>
            <button
              type="button"
              className={`resultados-apuestas-window-btn ${
                weekdayFilter === 'viernes' ? 'resultados-apuestas-window-btn--active' : ''
              }`}
              onClick={() => setWeekdayFilter('viernes')}
            >
              Viernes
            </button>
          </div>
        </div>
      </div>

      {error && <p style={{ color: 'var(--color-error)', marginTop: 'var(--space-sm)' }}>{error}</p>}
      {loading && !hasData && <p style={{ marginTop: 'var(--space-sm)' }}>Cargando histórico de apuestas…</p>}
      {!loading && !error && !hasData && (
        <p style={{ marginTop: 'var(--space-sm)' }}>No hay datos de apuestas para este rango.</p>
      )}

      {hasData && (
        <>
          <h3 className="resultados-apuestas-subtitle">Comparación normalizada</h3>
          <div style={{ width: '100%', height: 320, marginTop: 'var(--space-sm)' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={combinedData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 10 }}
                  tickMargin={8}
                  minTickGap={20}
                />
                <YAxis
                  tick={{ fontSize: 10 }}
                  domain={[0, 100]}
                  tickFormatter={(v: number) => `${v.toFixed(0)}%`}
                />
                <Tooltip
                  formatter={(value: any, name: string, props: any) => {
                    const p = props?.payload as {
                      apuestas?: number | null;
                      premios?: number | null;
                      premio_bote?: number | null;
                    };
                    if (name.startsWith('Apuestas')) {
                      const n = Number(p?.apuestas);
                      return [
                        Number.isNaN(n) ? p?.apuestas : n.toLocaleString('es-ES'),
                        'Apuestas',
                      ];
                    }
                    if (name.startsWith('Premios')) {
                      const n = Number(p?.premios);
                      return [
                        Number.isNaN(n)
                          ? p?.premios
                          : `${n.toLocaleString('es-ES', {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })} €`,
                        'Premios',
                      ];
                    }
                    if (name.startsWith('Bote')) {
                      const n = Number(p?.premio_bote);
                      return [
                        Number.isNaN(n)
                          ? p?.premio_bote
                          : `${n.toLocaleString('es-ES', {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })} €`,
                        'Bote',
                      ];
                    }
                    return [value, name];
                  }}
                  labelFormatter={(label) => `Fecha: ${label}`}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="apuestas_norm"
                  name="Apuestas (norm.)"
                  stroke="#2563eb"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="premios_norm"
                  name="Premios (norm.)"
                  stroke="#16a34a"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="bote_norm"
                  name="Bote (norm.)"
                  stroke="#eab308"
                  dot={false}
                  strokeDasharray="4 4"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <h3 className="resultados-apuestas-subtitle" style={{ marginTop: 'var(--space-lg)' }}>
            Apuestas recibidas
          </h3>
          <div style={{ width: '100%', height: 320, marginTop: 'var(--space-sm)' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={filteredPoints} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 10 }}
                  tickMargin={8}
                  minTickGap={20}
                />
                <YAxis
                  tick={{ fontSize: 10 }}
                  tickFormatter={(v: number) =>
                    v >= 1_000_000 ? `${(v / 1_000_000).toFixed(0)}M` : `${(v / 1_000).toFixed(0)}k`
                  }
                />
                <Tooltip
                  formatter={(value: any, name: string) => {
                    const n = Number(value);
                    return [
                      Number.isNaN(n) ? value : n.toLocaleString('es-ES'),
                      'Apuestas',
                    ];
                  }}
                  labelFormatter={(label) => `Fecha: ${label}`}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="apuestas"
                  name="Apuestas"
                  stroke="#2563eb"
                  dot={{ r: 2 }}
                  activeDot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <h3 className="resultados-apuestas-subtitle" style={{ marginTop: 'var(--space-lg)' }}>
            Premios
          </h3>
          <div style={{ width: '100%', height: 320, marginTop: 'var(--space-sm)' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={filteredPoints} margin={{ top: 10, right: 40, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 10 }}
                  tickMargin={8}
                  minTickGap={20}
                />
                <YAxis
                  orientation="right"
                  tick={{ fontSize: 10 }}
                  tickFormatter={(v: number) =>
                    v >= 1_000_000 ? `${(v / 1_000_000).toFixed(0)}M €` : `${v.toFixed(0)} €`
                  }
                />
                <Tooltip
                  formatter={(value: any, name: string) => {
                    const n = Number(value);
                    return [
                      Number.isNaN(n)
                        ? value
                        : `${n.toLocaleString('es-ES', {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })} €`,
                      name,
                    ];
                  }}
                  labelFormatter={(label) => `Fecha: ${label}`}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="premios"
                  name="Premios"
                  stroke="#16a34a"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <h3 className="resultados-apuestas-subtitle" style={{ marginTop: 'var(--space-lg)' }}>
            Bote
          </h3>
          <div style={{ width: '100%', height: 320, marginTop: 'var(--space-sm)' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={filteredPoints} margin={{ top: 10, right: 40, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 10 }}
                  tickMargin={8}
                  minTickGap={20}
                />
                <YAxis
                  orientation="right"
                  tick={{ fontSize: 10 }}
                  tickFormatter={(v: number) =>
                    v >= 1_000_000 ? `${(v / 1_000_000).toFixed(0)}M €` : `${v.toFixed(0)} €`
                  }
                />
                <Tooltip
                  formatter={(value: any, name: string) => {
                    const n = Number(value);
                    return [
                      Number.isNaN(n)
                        ? value
                        : `${n.toLocaleString('es-ES', {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })} €`,
                      name,
                    ];
                  }}
                  labelFormatter={(label) => `Fecha: ${label}`}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="premio_bote"
                  name="Bote"
                  stroke="#eab308"
                  dot={false}
                  strokeDasharray="4 4"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </section>
  );
}

