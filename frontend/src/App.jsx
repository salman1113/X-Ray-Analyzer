import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";

// Public pages
import Landing from "./pages/Landing";
import Auth from "./pages/Auth";
import MagicLogin from "./pages/MagicLogin";

// Dashboard
import DashboardLayout from "./pages/dashboard/DashboardLayout";
import Overview from "./pages/dashboard/Overview";
import Patients from "./pages/dashboard/Patients";
import PatientDetail from "./pages/dashboard/PatientDetail";
import Scans from "./pages/dashboard/Scans";
import ScanDetail from "./pages/dashboard/ScanDetail";
import Roster from "./pages/dashboard/Roster";
import TenantSettings from "./pages/dashboard/TenantSettings";
import Billing from "./pages/dashboard/Billing";
import DashboardSettings from "./pages/dashboard/Settings";
import AdminTenants from "./pages/dashboard/AdminTenants";
import AllUsers from "./pages/dashboard/AllUsers";

function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: {
            borderRadius: '16px',
            background: '#262622',
            color: '#ffffff',
            fontSize: '14px',
            fontWeight: '600',
            padding: '12px 16px',
          },
          success: { iconTheme: { primary: '#103c25', secondary: '#c7f0da' } },
          error: { iconTheme: { primary: '#e60023', secondary: '#ffffff' }, duration: 4000 },
        }}
      />
      <AuthProvider>
        <Routes>
          {/* ── Public ─────────────────────────────────────── */}
          <Route path="/" element={<Landing />} />
          <Route path="/landing" element={<Landing />} />
          <Route path="/login" element={<Auth />} />
          <Route path="/register" element={<Auth />} />
          <Route path="/magic-login" element={<MagicLogin />} />

          {/* ── Authenticated Dashboard ────────────────────── */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Overview />} />

            {/* Patients & Scans — doctor, admin */}
            <Route path="patients" element={<ProtectedRoute roles={["doctor", "admin"]}><Patients /></ProtectedRoute>} />
            <Route path="patients/:patientId" element={<ProtectedRoute roles={["doctor", "admin"]}><PatientDetail /></ProtectedRoute>} />
            <Route path="scans" element={<ProtectedRoute roles={["doctor", "admin"]}><Scans /></ProtectedRoute>} />
            <Route path="scans/:scanId" element={<ProtectedRoute roles={["doctor", "admin"]}><ScanDetail /></ProtectedRoute>} />

            {/* Admin-only */}
            <Route path="roster" element={<ProtectedRoute roles={["admin"]}><Roster /></ProtectedRoute>} />
            <Route path="tenant" element={<ProtectedRoute roles={["admin"]}><TenantSettings /></ProtectedRoute>} />
            <Route path="billing" element={<ProtectedRoute roles={["admin"]}><Billing /></ProtectedRoute>} />

            {/* Superadmin-only */}
            <Route path="tenants" element={<ProtectedRoute roles={["superadmin"]}><AdminTenants /></ProtectedRoute>} />
            <Route path="all-users" element={<ProtectedRoute roles={["superadmin"]}><AllUsers /></ProtectedRoute>} />

            {/* Account settings — all roles */}
            <Route path="settings" element={<DashboardSettings />} />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
