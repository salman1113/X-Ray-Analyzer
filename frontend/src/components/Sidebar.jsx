import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, Users, UserSearch, ScanLine,
  Settings, CreditCard, Building2, Shield, LogOut, Menu, X
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useState } from "react";

const navItems = {
  doctor: [
    { to: "/dashboard", icon: LayoutDashboard, label: "Overview" },
    { to: "/dashboard/patients", icon: Users, label: "Patients" },
    { to: "/dashboard/scans", icon: ScanLine, label: "Scans" },
    { to: "/dashboard/settings", icon: Settings, label: "Settings" },
  ],
  admin: [
    { to: "/dashboard", icon: LayoutDashboard, label: "Overview" },
    { to: "/dashboard/patients", icon: Users, label: "Patients" },
    { to: "/dashboard/scans", icon: ScanLine, label: "Scans" },
    { to: "/dashboard/roster", icon: UserSearch, label: "Staff" },
    { to: "/dashboard/billing", icon: CreditCard, label: "Usage" },
    { to: "/dashboard/tenant", icon: Building2, label: "Hospital" },
    { to: "/dashboard/settings", icon: Settings, label: "Account" },
  ],
  superadmin: [
    { to: "/dashboard", icon: LayoutDashboard, label: "Overview" },
    { to: "/dashboard/tenants", icon: Building2, label: "Hospitals" },
    { to: "/dashboard/all-users", icon: Users, label: "Users" },
    { to: "/dashboard/settings", icon: Settings, label: "Account" },
  ],
};

export default function Sidebar() {
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const role = user?.role || "doctor";
  const items = navItems[role] || navItems.doctor;

  // Mobile: show only first 4 items in bottom tab bar
  const mobileItems = items.slice(0, 4);

  return (
    <>
      {/* ── Desktop Sidebar (hidden on mobile) ── */}
      <aside className="hidden md:flex fixed left-0 top-0 bottom-0 w-60 bg-canvas border-r border-hairline flex-col z-40">
        {/* Brand */}
        <div className="h-16 flex items-center px-5 border-b border-hairline">
          <span className="text-base font-bold text-ink tracking-tight">
            AI X-Ray Analyzer
          </span>
        </div>

        {/* Role badge */}
        <div className="px-4 py-3">
          <div className="flex items-center gap-2 px-3 py-2 bg-surface-card rounded-full">
            <Shield className="w-3.5 h-3.5 text-mute" strokeWidth={2} />
            <span className="text-xs font-bold text-mute uppercase tracking-wider">
              {role === "superadmin" ? "Super Admin" : role === "admin" ? "Admin" : "Doctor"}
            </span>
          </div>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-3 space-y-1 overflow-y-auto">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/dashboard"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 rounded-md text-sm font-bold transition-all duration-200 transform ${
                  isActive
                    ? "bg-surface-card text-primary"
                    : "text-mute hover:bg-surface-card/60 hover:text-ink hover:translate-x-1"
                }`
              }
            >
              <item.icon className="w-[18px] h-[18px]" strokeWidth={1.8} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* User footer */}
        <div className="p-4 border-t border-hairline bg-surface-soft/40">
          <div className="bg-canvas border border-hairline rounded-md p-3.5 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-surface-card rounded-full flex items-center justify-center text-ink text-xs font-bold border border-hairline-soft">
                {user?.email?.charAt(0).toUpperCase() || "?"}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-bold text-ink truncate">{user?.email}</p>
                <p className="text-[10px] text-mute font-semibold truncate">{user?.hospital_name || "Platform"}</p>
              </div>
            </div>
            <button
              onClick={logout}
              className="w-full h-8 flex items-center justify-center gap-1.5 px-3 text-xs font-bold text-mute hover:text-error hover:bg-red-50 border border-hairline hover:border-red-100 rounded-md transition-all cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" strokeWidth={2} />
              Sign out
            </button>
          </div>
        </div>
      </aside>

      {/* ── Mobile Top Bar (visible on mobile only) ── */}
      <header className="md:hidden fixed top-0 left-0 right-0 z-50 bg-canvas border-b border-hairline h-14 flex items-center justify-between px-4">
        <span className="text-sm font-bold text-ink">AI X-Ray</span>
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-surface-card rounded-full flex items-center justify-center text-ink text-[10px] font-bold">
            {user?.email?.charAt(0).toUpperCase() || "?"}
          </div>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="p-2 text-ink rounded-md cursor-pointer"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </header>

      {/* ── Mobile Drawer (full nav when hamburger is open) ── */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-40">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMobileOpen(false)} />
          <div className="absolute top-14 right-0 w-64 bottom-0 bg-canvas border-l border-hairline p-4 overflow-y-auto z-10">
            <div className="flex items-center gap-2 px-3 py-2 mb-3 bg-surface-card rounded-full">
              <Shield className="w-3 h-3 text-mute" />
              <span className="text-[10px] font-bold text-mute uppercase tracking-wider">
                {role === "superadmin" ? "Super Admin" : role === "admin" ? "Admin" : "Doctor"}
              </span>
            </div>
            <nav className="space-y-1">
              {items.map((item) => (
                <NavLink
                   key={item.to}
                   to={item.to}
                   end={item.to === "/dashboard"}
                   onClick={() => setMobileOpen(false)}
                   className={({ isActive }) =>
                     `flex items-center gap-3 px-3 py-3 rounded-md text-sm font-semibold transition-colors ${
                       isActive
                         ? "bg-surface-card text-ink"
                         : "text-mute hover:bg-surface-card"
                     }`
                   }
                >
                  <item.icon className="w-[18px] h-[18px]" strokeWidth={1.8} />
                  {item.label}
                </NavLink>
              ))}
            </nav>
            <div className="mt-6 pt-4 border-t border-hairline">
              <p className="text-xs text-ash truncate px-3 mb-2">{user?.email}</p>
              <button
                onClick={() => { logout(); setMobileOpen(false); }}
                className="w-full flex items-center gap-2 px-3 py-2.5 text-sm font-semibold text-mute hover:text-error hover:bg-red-50 rounded-md transition-colors cursor-pointer"
              >
                <LogOut className="w-4 h-4" /> Sign out
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Mobile Bottom Tab Bar ── */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-canvas border-t border-hairline safe-area-bottom flex items-center justify-around px-1" style={{ height: "calc(64px + env(safe-area-inset-bottom, 0px))", paddingBottom: "env(safe-area-inset-bottom, 0px)" }}>
        {mobileItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/dashboard"}
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-md transition-colors ${
                isActive ? "text-primary" : "text-ash"
              }`
            }
          >
            <item.icon className="w-5 h-5" strokeWidth={1.8} />
            <span className="text-[10px] font-bold">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </>
  );
}
