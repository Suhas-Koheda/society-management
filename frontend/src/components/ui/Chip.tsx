import './Chip.css';

type ChipVariant = 'default' | 'active' | 'status';
type ChipColor = 'default' | 'success' | 'warning' | 'error' | 'info';

interface ChipProps {
  variant?: ChipVariant;
  color?: ChipColor;
  active?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
}

export function Chip({
  variant = 'default',
  color = 'default',
  active = false,
  children,
  onClick,
  className = '',
}: ChipProps) {
  const Tag = onClick ? 'button' : 'span';
  return (
    <Tag
      className={`chip chip--${variant} chip--${color} ${active ? 'chip--active' : ''} ${className}`}
      onClick={onClick}
      type={onClick ? 'button' : undefined}
    >
      {children}
    </Tag>
  );
}
