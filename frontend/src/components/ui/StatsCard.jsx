export default function StatsCard({ label, value, icon: Icon }) {
  return (
    <div className="bg-[var(--canvas)] border border-[var(--hairline)] rounded-md p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-bold text-[var(--ash)] uppercase tracking-wider">{label}</span>
        {Icon && <Icon className="w-4 h-4 text-[var(--ash)]" strokeWidth={1.8} />}
      </div>
      <p className="text-2xl font-bold text-[var(--ink)] tracking-tight">{value}</p>
    </div>
  );
}
