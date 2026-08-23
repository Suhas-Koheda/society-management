import { type TextareaHTMLAttributes, forwardRef } from 'react';
import './Input.css';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  helperText?: string;
  error?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, helperText, error, className = '', id, ...props }, ref) => {
    const textareaId = id || label?.toLowerCase().replace(/\s+/g, '-');
    return (
      <div className={`field ${className}`}>
        {label && (
          <label className="field__label" htmlFor={textareaId}>
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          className={`input textarea ${error ? 'input--error' : ''}`}
          rows={4}
          {...props}
        />
        {helperText && (
          <span className={`field__helper ${error ? 'field__helper--error' : ''}`}>
            {helperText}
          </span>
        )}
      </div>
    );
  },
);

Textarea.displayName = 'Textarea';

const style = document.createElement('style');
style.textContent = `
.textarea {
  resize: vertical;
  min-height: 100px;
  line-height: 1.5;
}
`;
document.head.appendChild(style);
