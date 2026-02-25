import { useState } from 'react';
import { Link, NavLink, Outlet } from 'react-router-dom';

const navItems = [
  { to: '/', label: 'Dashboard' },
  { to: '/resultados/la-primitiva', label: 'La Primitiva' },
  { to: '/resultados/euromillones', label: 'Euromillones' },
  { to: '/resultados/el-gordo', label: 'El Gordo' },
  { to: '/predictions', label: 'Predictions' },
  { to: '/wheeling', label: 'Wheeling' },
  { to: '/backtesting', label: 'Backtesting' },
  { to: '/betting', label: 'Betting' },
  { to: '/betting/history', label: 'Betting history' },
  { to: '/data', label: 'Data' },
  { to: '/settings', label: 'Settings' },
];

export function Layout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [theme, setTheme] = useState(() => {
    const t = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', t);
    return t;
  });

  const toggleTheme = () => {
    const next = theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', next);
    document.documentElement.setAttribute('data-theme', next);
    setTheme(next);
  };

  return (
    <div className="app">
      <header className="app-header">
        <Link to="/" className="app-logo">
          <img src="/images/logo_loterias.svg" alt="Lottery Prediction" className="app-logo-img" />
        </Link>
        <nav className={`app-nav ${menuOpen ? 'open' : ''}`} aria-label="Main">
          {navItems.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              end={to === '/'}
              onClick={() => setMenuOpen(false)}
            >
              {label}
            </NavLink>
          ))}
        </nav>
        <button
          type="button"
          className="theme-toggle"
          onClick={toggleTheme}
          aria-label={theme === 'light' ? 'Cambiar a modo oscuro' : 'Cambiar a modo claro'}
          title={theme === 'light' ? 'Modo oscuro' : 'Modo claro'}
        >
          {theme === 'light' ? '🌙' : '☀️'}
        </button>
        <button
          type="button"
          className="menu-toggle"
          aria-label="Toggle menu"
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((prev) => !prev)}
        >
          ☰
        </button>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
