import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Login failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <Card className="auth-card">
        <h1 className="auth-title">LOGIN</h1>
        <form onSubmit={handleSubmit}>
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
          <div style={{ marginTop: 'var(--sp-3)' }}>
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>
          {error && (
            <div style={{ marginTop: 'var(--sp-2)', color: 'var(--error)', fontFamily: 'var(--font-mono)', fontSize: '13px' }}>
              {error}
            </div>
          )}
          <div style={{ marginTop: 'var(--sp-4)' }}>
            <Button type="submit" disabled={loading} fullWidth>
              {loading ? 'LOGGING IN...' : 'LOGIN'}
            </Button>
          </div>
        </form>
        <div style={{ marginTop: 'var(--sp-3)', textAlign: 'center' }}>
          <Link to="/register" className="btn btn--ghost">
            CREATE ACCOUNT
          </Link>
        </div>
      </Card>
    </div>
  );
}
