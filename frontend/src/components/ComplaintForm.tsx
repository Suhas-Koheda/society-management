import { useState } from 'react';
import { COMPLAINT_CATEGORIES } from '../types';
import { Select } from './ui/Select';
import { Textarea } from './ui/Textarea';
import { Button } from './ui/Button';

interface ComplaintFormProps {
  onSubmit: (data: { category: string; description: string }) => Promise<void>;
  isPending?: boolean;
}

export function ComplaintForm({ onSubmit, isPending }: ComplaintFormProps) {
  const [category, setCategory] = useState('');
  const [description, setDescription] = useState('');
  const [errors, setErrors] = useState<{ category?: string; description?: string }>({});

  function validate() {
    const errs: typeof errors = {};
    if (!category) errs.category = 'Required';
    if (!description.trim()) errs.description = 'Required';
    else if (description.length > 2000) errs.description = 'Max 2000 characters';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    await onSubmit({ category, description });
  }

  return (
    <form onSubmit={handleSubmit}>
      <Select
        label="Category"
        options={COMPLAINT_CATEGORIES}
        value={category}
        onChange={(e) => setCategory(e.target.value)}
        placeholder="Select category"
        error={!!errors.category}
        helperText={errors.category}
      />
      <div style={{ marginTop: 'var(--sp-3)' }}>
        <Textarea
          label="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe the issue..."
          error={!!errors.description}
          helperText={errors.description || `${description.length}/2000`}
          maxLength={2000}
        />
      </div>
      <div style={{ marginTop: 'var(--sp-4)' }}>
        <Button type="submit" disabled={isPending} fullWidth>
          {isPending ? 'SUBMITTING...' : 'SUBMIT COMPLAINT'}
        </Button>
      </div>
    </form>
  );
}
