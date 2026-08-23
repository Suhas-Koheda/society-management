import { formatDateTime } from '../lib/formatters';
import './PhotoGrid.css';

interface Photo {
  id: number;
  url: string;
  created_at: string;
}

export function PhotoGrid({ photos }: { photos: Photo[] }) {
  if (photos.length === 0) return null;

  return (
    <div className="photo-grid">
      {photos.map((photo) => (
        <div key={photo.id} className="photo-grid__item">
          <a href={photo.url} target="_blank" rel="noopener noreferrer">
            <img src={photo.url} alt="" className="photo-grid__img" />
          </a>
          <span className="photo-grid__date">{formatDateTime(photo.created_at)}</span>
        </div>
      ))}
    </div>
  );
}
