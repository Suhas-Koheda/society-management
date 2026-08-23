import { Card } from './ui/Card';
import './StatsCard.css';

interface StatsCardProps {
  label: string;
  value: number | string;
  color?: string;
}

export function StatsCard({ label, value, color }: StatsCardProps) {
  return (
    <Card className="stats-card">
      <div className="stats-card__value" style={color ? { color } : undefined}>
        {value}
      </div>
      <div className="stats-card__label">{label}</div>
    </Card>
  );
}
