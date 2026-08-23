import { useState, useEffect } from 'react';
import { useOverdueThreshold, useUpdateOverdueThreshold } from '../../hooks/useAdmin';
import { Card } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { Spinner } from '../../components/ui/Spinner';
import { useToast } from '../../components/ui/Toast';

export function Settings() {
  const { data, isLoading } = useOverdueThreshold();
  const updateThreshold = useUpdateOverdueThreshold();
  const { toast } = useToast();
  const [days, setDays] = useState('');

  useEffect(() => {
    if (data) setDays(String(data.threshold_days));
  }, [data]);

  if (isLoading) return <Spinner />;

  async function handleSave() {
    const num = parseInt(days, 10);
    if (isNaN(num) || num < 1 || num > 365) {
      toast('Must be between 1 and 365 days', 'error');
      return;
    }
    try {
      await updateThreshold.mutateAsync(num);
      toast('Threshold updated', 'success');
    } catch {
      toast('Failed to update threshold', 'error');
    }
  }

  return (
    <div style={{ maxWidth: '500px' }}>
      <h2 style={{ marginBottom: 'var(--sp-4)' }}>SETTINGS</h2>
      <Card>
        <h3 style={{ fontSize: '16px', marginBottom: 'var(--sp-3)' }}>OVERDUE THRESHOLD</h3>
        <p style={{ fontSize: '14px', color: 'var(--content-secondary)', marginBottom: 'var(--sp-3)' }}>
          A complaint is marked overdue if not resolved within this many days.
        </p>
        <Input
          label="Threshold (days)"
          type="number"
          value={days}
          onChange={(e) => setDays(e.target.value)}
          min={1}
          max={365}
        />
        <div style={{ marginTop: 'var(--sp-3)' }}>
          <Button onClick={handleSave} disabled={updateThreshold.isPending}>
            {updateThreshold.isPending ? 'SAVING...' : 'SAVE'}
          </Button>
        </div>
      </Card>
    </div>
  );
}
