import { Outlet } from "react-router-dom";
import Sidebar from "../../components/Sidebar";

export default function DashboardLayout() {
  return (
    <div className="min-h-screen bg-[var(--surface-soft)]">
      <Sidebar />
      {/* Desktop: offset for sidebar. Mobile: offset for top bar + bottom tab bar */}
      <main className="md:ml-60 min-h-screen pt-14 pb-20 md:pt-0 md:pb-0">
        <div className="max-w-5xl mx-auto px-4 sm:px-5 md:px-8 py-5 sm:py-6 md:py-10 animate-fade-in">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
