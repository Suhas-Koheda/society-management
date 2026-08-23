import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import './Layout.css';

export function AppLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const isAdmin = user?.role === 'admin';

  const residentLinks = [
    { to: '/', label: 'Dashboard' },
    { to: '/complaints', label: 'My Complaints' },
    { to: '/complaints/new', label: 'New Complaint' },
    { to: '/notices', label: 'Notices' },
  ];

  const adminLinks = [
    { to: '/admin', label: 'Dashboard' },
    { to: '/admin/complaints', label: 'Complaints' },
    { to: '/admin/notices', label: 'Notices' },
    { to: '/admin/users', label: 'Users' },
    { to: '/admin/settings', label: 'Settings' },
  ];

  const links = isAdmin ? adminLinks : residentLinks;

  return (
    <div className="layout">
      <header className="header">
        <div className="header__left">
          <Link to="/" className="header__logo">
            SOCIETY TRACKER
          </Link>
        </div>
        <div className="header__right">
          <span className="header__user">
            {user?.name} ({user?.role})
          </span>
          <button className="header__logout" onClick={logout}>
            LOGOUT
          </button>
        </div>
      </header>
      <div className="layout__body">
        <nav className="sidebar">
          {links.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={`sidebar__link ${
                location.pathname === link.to ? 'sidebar__link--active' : ''
              }`}
            >
              {link.label}
            </Link>
          ))}
          {isAdmin && (
            <>
              <div className="sidebar__divider" />
              <span className="sidebar__section">RESIDENT</span>
              {residentLinks
                .filter((l) => l.to !== '/complaints/new')
                .map((link) => (
                  <Link
                    key={link.to}
                    to={link.to}
                    className={`sidebar__link sidebar__link--muted ${
                      location.pathname === link.to ? 'sidebar__link--active' : ''
                    }`}
                  >
                    {link.label}
                  </Link>
                ))}
            </>
          )}
        </nav>
        <main className="main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
