import { type ReactNode } from 'react';
import './Card.css';

interface CardProps {
  variant?: 'default' | 'elevated';
  children: ReactNode;
  className?: string;
}

export function Card({ variant = 'default', children, className = '' }: CardProps) {
  return (
    <div className={`card card--${variant} ${className}`}>
      {children}
    </div>
  );
}
