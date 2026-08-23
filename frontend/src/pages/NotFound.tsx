import { Link } from 'react-router-dom';

export function NotFound() {
  return (
    <div style={{ textAlign: 'center', padding: 'var(--sp-8) var(--sp-3)' }}>
      <h1 style={{ fontSize: '120px', lineHeight: 1, marginBottom: 'var(--sp-3)' }}>404</h1>
      <h2 style={{ marginBottom: 'var(--sp-4)' }}>PAGE NOT FOUND</h2>
      <Link to="/" className="btn btn--primary">
        GO HOME
      </Link>
    </div>
  );
}
