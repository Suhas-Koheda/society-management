import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useCreateNotice, useUpdateNotice } from '../../hooks/useAdmin';
import { Card } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Textarea } from '../../components/ui/Textarea';
import { Button } from '../../components/ui/Button';
import { useToast } from '../../components/ui/Toast';

export function NoticeForm() {
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id;
  const navigate = useNavigate();
  const createNotice = useCreateNotice();
  const updateNotice = useUpdateNotice();
  const { toast } = useToast();

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [isImportant, setIsImportant] = useState(false);
  const [errors, setErrors] = useState<{ title?: string; content?: string }>({});

  useEffect(() => {
    if (isEdit && id) {
      fetch(`/api/v1/admin/notices?page=1&page_size=100`)
        .then((r) => r.json())
        .then((data) => {
          const notice = data.items?.find((n: { id: number }) => n.id === Number(id));
          if (notice) {
            setTitle(notice.title);
            setContent(notice.content);
            setIsImportant(notice.is_important);
          }
        })
        .catch(() => {});
    }
  }, [isEdit, id]);

  function validate() {
    const errs: typeof errors = {};
    if (!title.trim()) errs.title = 'Required';
    if (!content.trim()) errs.content = 'Required';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    try {
      if (isEdit && id) {
        await updateNotice.mutateAsync({
          id: Number(id),
          data: { title, content, is_important: isImportant },
        });
        toast('Notice updated', 'success');
      } else {
        await createNotice.mutateAsync({ title, content, is_important: isImportant });
        toast('Notice created', 'success');
      }
      navigate('/admin/notices');
    } catch {
      toast('Failed to save notice', 'error');
    }
  }

  const pending = createNotice.isPending || updateNotice.isPending;

  return (
    <div style={{ maxWidth: '600px' }}>
      <h2 style={{ marginBottom: 'var(--sp-4)' }}>{isEdit ? 'EDIT NOTICE' : 'NEW NOTICE'}</h2>
      <Card>
        <form onSubmit={handleSubmit}>
          <Input
            label="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            error={!!errors.title}
            helperText={errors.title}
            maxLength={200}
          />
          <div style={{ marginTop: 'var(--sp-3)' }}>
            <Textarea
              label="Content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              error={!!errors.content}
              helperText={errors.content}
              rows={8}
              maxLength={5000}
            />
          </div>
          <div style={{ marginTop: 'var(--sp-3)', display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
            <input
              type="checkbox"
              id="important"
              checked={isImportant}
              onChange={(e) => setIsImportant(e.target.checked)}
              style={{ width: '20px', height: '20px', border: '3px solid var(--black)', accentColor: 'var(--black)' }}
            />
            <label htmlFor="important" style={{ fontFamily: 'var(--font-headline)', fontSize: '14px', textTransform: 'uppercase' }}>
              IMPORTANT (sends email to all users)
            </label>
          </div>
          <div style={{ marginTop: 'var(--sp-4)', display: 'flex', gap: 'var(--sp-2)' }}>
            <Button type="submit" disabled={pending}>
              {pending ? 'SAVING...' : isEdit ? 'UPDATE NOTICE' : 'CREATE NOTICE'}
            </Button>
            <Button variant="secondary" type="button" onClick={() => navigate('/admin/notices')}>
              CANCEL
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
