import { useState } from 'react';
import { Link, NavLink, Outlet } from 'react-router-dom';

const navItems = [
  { to: '/resultados/la-primitiva', label: 'La Primitiva', icon: '/images/la-primitiva.png' },
  { to: '/resultados/euromillones', label: 'Euromillones', icon: '/images/euromillones.png' },
  { to: '/resultados/el-gordo', label: 'El Gordo', icon: '/images/el-gordo.png' },
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
          <img src="/images/logo_loterias.svg" alt="Predicción Lotería" className="app-logo-img" />
        </Link>
        <nav className={`app-nav ${menuOpen ? 'open' : ''}`} aria-label="Navegación principal">
          {navItems.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              end={to === '/'}
              onClick={() => setMenuOpen(false)}
              title={label}
              aria-label={label}
            >
              <img src={icon} alt="" className="nav-link-icon" aria-hidden />
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
          aria-label="Abrir o cerrar menú"
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
