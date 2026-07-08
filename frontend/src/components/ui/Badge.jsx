const variants = {
  default: "bg-[var(--surface-card)] text-[var(--mute)]",
  success: "bg-[var(--success-pale)] text-[var(--success)]",
  warning: "bg-amber-50 text-amber-700",
  danger: "bg-red-50 text-[var(--error)]",
  info: "bg-blue-50 text-[var(--focus)]",
  purple: "bg-purple-50 text-[var(--accent-purple-deep)]",
};

export default function Badge({ children, variant = "default" }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 text-xs font-bold rounded-full ${variants[variant] || variants.default}`}>
      {children}
    </span>
  );
}
