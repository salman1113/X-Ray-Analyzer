import { useState, useEffect } from "react";
import { getUsage } from "../../api/billing";
import { CreditCard, Users, ScanLine, TrendingUp } from "lucide-react";
import StatsCard from "../../components/ui/StatsCard";
import LoadingSpinner from "../../components/ui/LoadingSpinner";

export default function Billing() {
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { (async () => { try { setUsage(await getUsage()); } catch { /* ignore */ } finally { setLoading(false); } })(); }, []);

  if (loading) return <div className="flex items-center justify-center py-32"><LoadingSpinner text="Loading usage..." /></div>;
  if (!usage) return <div className="text-center py-20 text-mute">Unable to load usage data.</div>;

  const scanPct = usage.max_scans_per_month > 0 ? Math.round((usage.current_month_scans / usage.max_scans_per_month) * 100) : 0;
  const userPct = usage.max_users > 0 ? Math.round((usage.current_users / usage.max_users) * 100) : 0;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl sm:text-[28px] font-bold text-ink tracking-[-1.2px] leading-tight">Usage & Plan</h1>
        <p className="text-sm text-mute mt-1">Resource consumption this month.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard label="Plan" value={usage.plan?.toUpperCase()} icon={CreditCard} />
        <StatsCard label="Doctors" value={`${usage.current_users}/${usage.max_users}`} icon={Users} />
        <StatsCard label="Scans" value={`${usage.current_month_scans}/${usage.max_scans_per_month}`} icon={ScanLine} />
        <StatsCard label="Usage" value={`${scanPct}%`} icon={TrendingUp} />
      </div>

      <div className="bg-canvas border border-hairline rounded-md p-6 space-y-6">
        <UsageBar label="Scan Usage" current={usage.current_month_scans} max={usage.max_scans_per_month} pct={scanPct} />
        <UsageBar label="User Seats" current={usage.current_users} max={usage.max_users} pct={userPct} />
      </div>
    </div>
  );
}

function UsageBar({ label, current, max, pct }) {
  const color = pct > 80 ? "bg-primary" : pct > 50 ? "bg-amber-500" : "bg-success";
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold text-ink">{label}</span>
        <span className="text-sm text-mute font-bold">{current} / {max}</span>
      </div>
      <div className="h-2 bg-surface-card rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${Math.min(pct, 100)}%` }} />
      </div>
    </div>
  );
}
