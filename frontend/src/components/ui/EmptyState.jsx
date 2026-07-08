export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="text-center py-16">
      {Icon && <Icon className="w-10 h-10 text-[var(--ash)] mx-auto mb-4" strokeWidth={1.5} />}
      <h3 className="text-base font-semibold text-[var(--ink)] mb-1">{title}</h3>
      {description && <p className="text-sm text-[var(--mute)] mb-4">{description}</p>}
      {action}
    </div>
  );
}
