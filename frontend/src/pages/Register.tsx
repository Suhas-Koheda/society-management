import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';

export function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(name, email, password);
      navigate('/');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Registration failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <Card className="auth-card">
        <h1 className="auth-title">REGISTER</h1>
        <form onSubmit={handleSubmit}>
          <Input
            label="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            autoComplete="name"
          />
          <div style={{ marginTop: 'var(--sp-3)' }}>
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>
          <div style={{ marginTop: 'var(--sp-3)' }}>
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
            />
          </div>
          {error && (
            <div style={{ marginTop: 'var(--sp-2)', color: 'var(--error)', fontFamily: 'var(--font-mono)', fontSize: '13px' }}>
              {error}
            </div>
          )}
          <div style={{ marginTop: 'var(--sp-4)' }}>
            <Button type="submit" disabled={loading} fullWidth>
              {loading ? 'CREATING ACCOUNT...' : 'REGISTER'}
            </Button>
          </div>
        </form>
        <div style={{ marginTop: 'var(--sp-3)', textAlign: 'center' }}>
          <Link to="/login" className="btn btn--ghost">
            ALREADY HAVE AN ACCOUNT? LOGIN
          </Link>
        </div>
      </Card>
    </div>
  );
}
