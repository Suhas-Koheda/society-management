import {
  COMPLAINT_STATUSES,
  COMPLAINT_CATEGORIES,
  COMPLAINT_PRIORITIES,
} from '../types';
import { Chip } from './ui/Chip';
import { Input } from './ui/Input';
import './FilterBar.css';

interface Filters {
  status?: string;
  category?: string;
  priority?: string;
  date_from?: string;
  date_to?: string;
  overdue?: boolean;
}

interface FilterBarProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
}

export function FilterBar({ filters, onChange }: FilterBarProps) {
  function update(key: keyof Filters, value: string | boolean | undefined) {
    onChange({ ...filters, [key]: value || undefined });
  }

  return (
    <div className="filter-bar">
      <div className="filter-bar__row">
        <span className="filter-bar__label">STATUS</span>
        <div className="filter-bar__chips">
          {COMPLAINT_STATUSES.map((s) => (
            <Chip
              key={s.value}
              active={filters.status === s.value}
              onClick={() => update('status', filters.status === s.value ? '' : s.value)}
            >
              {s.label}
            </Chip>
          ))}
        </div>
      </div>

      <div className="filter-bar__row">
        <span className="filter-bar__label">PRIORITY</span>
        <div className="filter-bar__chips">
          {COMPLAINT_PRIORITIES.map((p) => (
            <Chip
              key={p.value}
              active={filters.priority === p.value}
              onClick={() =>
                update('priority', filters.priority === p.value ? '' : p.value)
              }
            >
              {p.label}
            </Chip>
          ))}
        </div>
      </div>

      <div className="filter-bar__row">
        <span className="filter-bar__label">CATEGORY</span>
        <div className="filter-bar__chips">
          {COMPLAINT_CATEGORIES.map((c) => (
            <Chip
              key={c.value}
              active={filters.category === c.value}
              onClick={() =>
                update('category', filters.category === c.value ? '' : c.value)
              }
            >
              {c.label}
            </Chip>
          ))}
        </div>
      </div>

      <div className="filter-bar__row">
        <span className="filter-bar__label">OVERDUE</span>
        <Chip
          active={filters.overdue === true}
          onClick={() => update('overdue', filters.overdue ? false : true)}
        >
          {filters.overdue ? 'SHOWING OVERDUE' : 'SHOW OVERDUE'}
        </Chip>
      </div>

      <div className="filter-bar__row filter-bar__row--dates">
        <Input
          label="From"
          type="date"
          value={filters.date_from || ''}
          onChange={(e) => update('date_from', e.target.value)}
        />
        <Input
          label="To"
          type="date"
          value={filters.date_to || ''}
          onChange={(e) => update('date_to', e.target.value)}
        />
      </div>
    </div>
  );
}
