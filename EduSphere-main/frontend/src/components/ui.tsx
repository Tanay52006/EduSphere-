import { ReactNode, useEffect } from "react";
type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "destructive";
  loading?: boolean;
};
export function Button({
  variant = "primary",
  loading,
  children,
  disabled,
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button
      className={`button button-${variant} ${className}`.trim()}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading && <span className="button-loader" aria-label="Loading" />}
      {children}
    </button>
  );
}
export function Input({
  label,
  error,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string;
}) {
  const id = props.id ?? props.name;
  return (
    <label className="field" htmlFor={id}>
      <span>{label}</span>
      <input
        id={id}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : undefined}
        {...props}
      />
      {error && (
        <small id={`${id}-error`} className="field-error">
          {error}
        </small>
      )}
    </label>
  );
}
export function Textarea({
  label,
  error,
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label: string;
  error?: string;
}) {
  const id = props.id ?? props.name;
  return (
    <label className="field" htmlFor={id}>
      <span>{label}</span>
      <textarea
        id={id}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : undefined}
        {...props}
      />
      {error && (
        <small id={`${id}-error`} className="field-error">
          {error}
        </small>
      )}
    </label>
  );
}
export function Select({
  label,
  children,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement> & { label: string }) {
  return (
    <label className="field" htmlFor={props.id ?? props.name}>
      <span>{label}</span>
      <select {...props}>{children}</select>
    </label>
  );
}
export function Switch({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="switch">
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
      >
        <span />
      </button>
      <span>{label}</span>
    </label>
  );
}
export function Tag({
  children,
  tone = "blue",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return <span className={`tag tag-${tone}`}>{children}</span>;
}
export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`card ${className}`}>{children}</div>;
}
export function Callout({
  children,
  tone = "blue",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return <div className={`callout callout-${tone}`}>{children}</div>;
}
export function ProgressBar({
  value,
  label,
}: {
  value: number;
  label?: string;
}) {
  return (
    <div className="progress-wrap" aria-label={label}>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton ${className}`} aria-hidden="true" />;
}
export function EmptyState({
  icon,
  title,
  children,
  action,
}: {
  icon: string;
  title: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <span className="empty-icon">{icon}</span>
      <h2>{title}</h2>
      <p>{children}</p>
      {action}
    </div>
  );
}
export function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onMouseDown={(event) => event.target === event.currentTarget && onClose()}
    >
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <button className="modal-close" onClick={onClose} aria-label="Close">
          ×
        </button>
        <h2 id="modal-title">{title}</h2>
        {children}
      </div>
    </div>
  );
}
export function Toast({
  message,
  onClose,
}: {
  message: string;
  onClose: () => void;
}) {
  return (
    <div className="toast" role="status">
      <span>✓</span>
      {message}
      <button onClick={onClose} aria-label="Dismiss">
        ×
      </button>
    </div>
  );
}
