import { useRef } from 'react';
import { useUploadPhoto } from '../hooks/useComplaints';
import { useToast } from './ui/Toast';

interface PhotoUploadProps {
  complaintId: number;
}

export function PhotoUpload({ complaintId }: PhotoUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadPhoto(complaintId);
  const { toast } = useToast();

  async function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      toast('File too large. Max 5MB.', 'error');
      return;
    }

    try {
      await uploadMutation.mutateAsync(file);
      toast('Photo uploaded', 'success');
      if (inputRef.current) inputRef.current.value = '';
    } catch {
      toast('Upload failed', 'error');
    }
  }

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={handleChange}
        style={{ display: 'none' }}
      />
      <button
        className="btn btn--secondary btn--small"
        onClick={() => inputRef.current?.click()}
        disabled={uploadMutation.isPending}
      >
        {uploadMutation.isPending ? 'UPLOADING...' : 'UPLOAD PHOTO'}
      </button>
    </div>
  );
}
