import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateComplaint } from '../../hooks/useComplaints';
import { ComplaintForm } from '../../components/ComplaintForm';
import { useToast } from '../../components/ui/Toast';
import { Button } from '../../components/ui/Button';

export function ComplaintNew() {
  const navigate = useNavigate();
  const createMutation = useCreateComplaint();
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files || []);
    const valid = files.filter((f) => {
      if (f.size > 5 * 1024 * 1024) {
        toast(`${f.name} is too large (max 5MB)`, 'error');
        return false;
      }
      return true;
    });
    setSelectedFiles((prev) => [...prev, ...valid]);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  function removeFile(index: number) {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSubmit(data: { category: string; description: string }) {
    try {
      const result = await createMutation.mutateAsync(data);

      if (selectedFiles.length > 0) {
        let uploaded = 0;
        for (const file of selectedFiles) {
          try {
            const formData = new FormData();
            formData.append('file', file);
            const token = localStorage.getItem('auth_token');
            await fetch(`/api/v1/complaints/${result.id}/photos`, {
              method: 'POST',
              headers: token ? { Authorization: `Bearer ${token}` } : {},
              body: formData,
            });
            uploaded++;
          } catch {
            // continue with next file
          }
        }
        if (uploaded > 0) {
          toast(`${uploaded} photo${uploaded > 1 ? 's' : ''} uploaded`, 'success');
        }
      }

      toast('Complaint submitted', 'success');
      navigate(`/complaints/${result.id}`);
    } catch {
      toast('Failed to submit complaint', 'error');
    }
  }

  return (
    <div style={{ maxWidth: '640px' }}>
      <h2 style={{ marginBottom: 'var(--sp-4)' }}>NEW COMPLAINT</h2>
      <div style={{ border: '3px solid var(--black)', padding: 'var(--sp-4)' }}>
        <ComplaintForm onSubmit={handleSubmit} isPending={createMutation.isPending} />

        <div style={{ marginTop: 'var(--sp-4)', borderTop: '3px solid var(--black)', paddingTop: 'var(--sp-4)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-2)' }}>
            <span style={{ fontFamily: 'var(--font-headline)', fontSize: '14px', textTransform: 'uppercase' }}>
              PHOTOS (OPTIONAL)
            </span>
            <Button variant="secondary" size="small" onClick={() => fileInputRef.current?.click()} type="button">
              ADD FILES
            </Button>
          </div>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--content-secondary)', marginBottom: 'var(--sp-2)' }}>
            JPEG, PNG, WebP. Max 5MB each. Photos upload after complaint is created.
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            multiple
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          {selectedFiles.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-1)' }}>
              {selectedFiles.map((f, i) => (
                <div
                  key={`${f.name}-${i}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--sp-2)',
                    padding: '6px 10px',
                    border: '2px solid var(--black)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '12px',
                  }}
                >
                  <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {f.name}
                  </span>
                  <span style={{ color: 'var(--content-secondary)' }}>
                    {(f.size / 1024).toFixed(0)}KB
                  </span>
                  <button
                    type="button"
                    onClick={() => removeFile(i)}
                    style={{
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 700,
                      fontSize: '14px',
                      padding: '0 4px',
                    }}
                  >
                    X
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div style={{
              border: '2px dashed var(--border-default)',
              padding: 'var(--sp-4)',
              textAlign: 'center',
              fontFamily: 'var(--font-mono)',
              fontSize: '12px',
              color: 'var(--content-tertiary)',
              textTransform: 'uppercase',
            }}>
              No photos selected
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
