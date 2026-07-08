import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { getDashboardData, getPlatformStats } from "../../api/admin";
import { getUsage } from "../../api/billing";
import { Building2, Users, ScanLine, Activity, CreditCard, ShieldCheck } from "lucide-react";
import StatsCard from "../../components/ui/StatsCard";
import LoadingSpinner from "../../components/ui/LoadingSpinner";
import Badge from "../../components/ui/Badge";

export default function Overview() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [stats, setStats] = useState(null);
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const d = await getDashboardData();
        setData(d);
        if (user?.role === "superadmin") setStats(await getPlatformStats());
        if (user?.role === "admin") setUsage(await getUsage());
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    };
    load();
  }, [user?.role]);

  if (loading) return <div className="flex items-center justify-center py-32"><LoadingSpinner text="Loading dashboard..." /></div>;

  // ── Super Admin ──
  if (user?.role === "superadmin") {
    const s = stats || data;
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl sm:text-[28px] font-bold text-ink tracking-[-1.2px] leading-tight">Platform Overview</h1>
          <p className="text-sm text-mute mt-1">All hospitals and users at a glance.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsCard label="Hospitals" value={s?.total_hospitals || 0} icon={Building2} />
          <StatsCard label="Active" value={s?.active_hospitals || 0} icon={Activity} />
          <StatsCard label="Users" value={s?.total_users || 0} icon={Users} />
          <StatsCard label="Verified" value={s?.verified_users || 0} icon={ShieldCheck} />
        </div>
        {data?.hospitals?.length > 0 && (
          <div className="bg-canvas border border-hairline rounded-md overflow-hidden">
            <div className="px-6 py-4 border-b border-hairline">
              <h2 className="text-xs font-bold text-ash uppercase tracking-wider">Hospitals</h2>
            </div>
            <div className="divide-y divide-hairline">
              {data.hospitals.map((h) => (
                <div key={h.id} className="px-6 py-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 bg-surface-card rounded-md flex items-center justify-center text-mute">
                      <Building2 className="w-4 h-4" strokeWidth={1.8} />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-ink">{h.name}</p>
                      <p className="text-xs text-ash font-mono">{h.id?.slice(0, 12)}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Badge variant={h.is_active ? "success" : "danger"}>{h.is_active ? "Active" : "Inactive"}</Badge>
                    <Badge variant="info">{h.plan || "free"}</Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // ── Admin ──
  if (user?.role === "admin") {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl sm:text-[28px] font-bold text-ink tracking-[-1.2px] leading-tight">{user?.hospital_name || "Hospital"}</h1>
          <p className="text-sm text-mute mt-1">Manage your team and operations.</p>
        </div>
        {usage && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatsCard label="Doctors" value={`${usage.current_users}/${usage.max_users}`} icon={Users} />
            <StatsCard label="Scans/Month" value={`${usage.current_month_scans}/${usage.max_scans_per_month}`} icon={ScanLine} />
            <StatsCard label="Plan" value={usage.plan?.toUpperCase()} icon={CreditCard} />
            <StatsCard label="Status" value="Active" icon={Activity} />
          </div>
        )}
        {data?.roster?.length > 0 && (
          <div className="bg-canvas border border-hairline rounded-md overflow-hidden">
            <div className="px-6 py-4 border-b border-hairline">
              <h2 className="text-xs font-bold text-ash uppercase tracking-wider">Doctor Roster</h2>
            </div>
            <div className="divide-y divide-hairline">
              {data.roster.map((d, i) => (
                <div key={i} className="px-6 py-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-surface-card rounded-full flex items-center justify-center text-ink text-xs font-bold">
                      {d.email?.charAt(0).toUpperCase()}
                    </div>
                    <span className="text-sm font-semibold text-ink">{d.email}</span>
                  </div>
                  <div className="flex gap-2">
                    <Badge variant={d.is_verified ? "success" : "warning"}>{d.is_verified ? "Verified" : "Pending"}</Badge>
                    <Badge variant={d.has_passkey ? "info" : "default"}>{d.has_passkey ? "Passkey" : "Password"}</Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // ── Doctor ──
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl sm:text-[28px] font-bold text-ink tracking-[-1.2px] leading-tight">Workspace</h1>
        <p className="text-sm text-mute mt-1">Welcome back, {user?.email}.</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link to="/dashboard/patients" className="bg-canvas border border-hairline rounded-md p-6 hover:bg-surface-card transition-colors">
          <Users className="w-6 h-6 text-ink mb-3" strokeWidth={1.8} />
          <h3 className="text-base font-bold text-ink mb-1 tracking-tight">Patients</h3>
          <p className="text-sm text-mute">View and manage records.</p>
        </Link>
        <Link to="/dashboard/scans" className="bg-canvas border border-hairline rounded-md p-6 hover:bg-surface-card transition-colors">
          <ScanLine className="w-6 h-6 text-ink mb-3" strokeWidth={1.8} />
          <h3 className="text-base font-bold text-ink mb-1 tracking-tight">X-Ray Scans</h3>
          <p className="text-sm text-mute">Upload and analyze images.</p>
        </Link>
        <Link to="/dashboard/settings" className="bg-canvas border border-hairline rounded-md p-6 hover:bg-surface-card transition-colors">
          <ShieldCheck className="w-6 h-6 text-ink mb-3" strokeWidth={1.8} />
          <h3 className="text-base font-bold text-ink mb-1 tracking-tight">Security</h3>
          <p className="text-sm text-mute">Manage passkeys and account.</p>
        </Link>
      </div>
    </div>
  );
}
