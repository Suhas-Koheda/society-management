import { useUsers, useUpdateUserRole } from '../../hooks/useAdmin';
import { Spinner } from '../../components/ui/Spinner';
import { EmptyState } from '../../components/ui/EmptyState';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { useToast } from '../../components/ui/Toast';
import { useAuth } from '../../hooks/useAuth';
import { useState } from 'react';
import { formatDateTime } from '../../lib/formatters';

export function AdminUsersList() {
  const { data: users, isLoading } = useUsers();
  const updateRole = useUpdateUserRole();
  const { toast } = useToast();
  const { user: currentUser } = useAuth();
  const [confirmUser, setConfirmUser] = useState<{ id: number; name: string; currentRole: string } | null>(null);

  if (isLoading) return <Spinner />;
  if (!users) return <EmptyState message="Failed to load users." />;

  async function handleRoleToggle(userId: number, currentRole: string) {
    const newRole = currentRole === 'admin' ? 'resident' : 'admin';
    try {
      await updateRole.mutateAsync({ userId, role: newRole });
      toast(`User role changed to ${newRole}`, 'success');
      setConfirmUser(null);
    } catch {
      toast('Failed to update role', 'error');
    }
  }

  return (
    <div>
      <h2 style={{ marginBottom: 'var(--sp-4)' }}>USER MANAGEMENT</h2>

      {users.length === 0 ? (
        <EmptyState message="No users found." />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
          {users.map((u) => (
            <div
              key={u.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--sp-3)',
                padding: 'var(--sp-3)',
                border: `3px solid ${u.role === 'admin' ? 'var(--blue)' : 'var(--black)'}`,
              }}
            >
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--content-secondary)', minWidth: '40px' }}>
                #{u.id}
              </span>
              <span style={{ flex: 1 }}>
                <span style={{ fontWeight: 600, textTransform: 'uppercase', fontSize: '14px' }}>
                  {u.name}
                </span>
                <br />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--content-secondary)' }}>
                  {u.email}
                </span>
              </span>
              <span
                style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: '11px',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                  padding: '2px 10px',
                  border: `2px solid ${u.role === 'admin' ? 'var(--blue)' : 'var(--black)'}`,
                  color: u.role === 'admin' ? 'var(--blue)' : 'var(--black)',
                }}
              >
                {u.role}
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--content-secondary)' }}>
                {formatDateTime(u.created_at)}
              </span>
              {u.id !== currentUser?.id && (
                <Button
                  variant={u.role === 'admin' ? 'destructive' : 'primary'}
                  size="small"
                  onClick={() => setConfirmUser({ id: u.id, name: u.name, currentRole: u.role })}
                >
                  {u.role === 'admin' ? 'DEMOTE' : 'PROMOTE'}
                </Button>
              )}
            </div>
          ))}
        </div>
      )}

      <Modal
        open={confirmUser !== null}
        onClose={() => setConfirmUser(null)}
        title="CONFIRM ROLE CHANGE"
      >
        {confirmUser && (
          <>
            <p style={{ marginBottom: 'var(--sp-3)' }}>
              {confirmUser.currentRole === 'admin'
                ? `Demote "${confirmUser.name}" to resident?`
                : `Promote "${confirmUser.name}" to admin?`}
            </p>
            <div style={{ display: 'flex', gap: 'var(--sp-2)' }}>
              <Button
                onClick={() => handleRoleToggle(confirmUser.id, confirmUser.currentRole)}
                disabled={updateRole.isPending}
              >
                {updateRole.isPending ? 'UPDATING...' : 'CONFIRM'}
              </Button>
              <Button variant="secondary" onClick={() => setConfirmUser(null)}>
                CANCEL
              </Button>
            </div>
          </>
        )}
      </Modal>
    </div>
  );
}
