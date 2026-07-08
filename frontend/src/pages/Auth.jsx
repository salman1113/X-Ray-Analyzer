import { useState, useEffect } from "react";
import {
  loginUser, startPasskeyLogin, verifyPasskeyLogin, forgotPassword,
  registerUser, verifyOtp, startPasskeyRegister, verifyPasskeyRegister
} from "../api/auth";
import { startAuthentication, startRegistration } from "@simplewebauthn/browser";
import { Fingerprint, Mail, Lock, Database, Zap, ShieldCheck, ChevronLeft, Globe, Copy } from "lucide-react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuth } from "../context/AuthContext";
import { buildTenantUrl, isTrustedTenantUrl, getCurrentSubdomain } from "../lib/subdomain";
import { getTenantBySubdomain } from "../api/tenants";

/** Safely redirect to a tenant URL only if it's under our domain. */
function safeTenantRedirect(url, path = "/dashboard") {
  if (url && isTrustedTenantUrl(url)) {
    window.location.href = url.replace(/\/$/, "") + path;
    return true;
  }
  return false;
}

export default function Auth() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated } = useAuth();

  const [isLoginMode, setIsLoginMode] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isForgotMode, setIsForgotMode] = useState(false);
  const [otp, setOtp] = useState("");
  const [regStep, setRegStep] = useState("register");
  const [role, setRole] = useState("doctor");
  const [hospitalName, setHospitalName] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [tenantUrl, setTenantUrl] = useState("");
  const [subdomain, setSubdomain] = useState("");
  const [tenantName, setTenantName] = useState("");

  useEffect(() => {
    const currentSub = getCurrentSubdomain();
    if (currentSub) {
      setSubdomain(currentSub);
      setRole("doctor");
      getTenantBySubdomain(currentSub)
        .then(t => {
          if (t && t.name) {
            setTenantName(t.name);
          }
        })
        .catch(err => {
          console.error("Failed to load tenant info:", err);
        });
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) navigate("/dashboard", { replace: true });
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    setIsLoginMode(location.pathname !== "/register");
    setError(""); setMessage("");
  }, [location.pathname]);

  const toggleAuth = () => {
    setError(""); setMessage("");
    navigate(isLoginMode ? "/register" : "/login");
  };

  // ── Login ──
  const handleLogin = async (e) => {
    e.preventDefault(); setError(""); setIsLoading(true);
    try {
      const res = await loginUser({ email, password });
      if (res.access_token) {
        await login(res.access_token, res.refresh_token, res.has_passkey);
        toast.success("Welcome back!");
        if (!safeTenantRedirect(res.tenant_url)) navigate("/dashboard");
      } else setError(res.detail || "Invalid credentials");
    } catch (err) { setError(err.message || "Login failed"); }
    finally { setIsLoading(false); }
  };

  const handlePasskeyLogin = async () => {
    setError("");
    if (!email) { setError("Enter your email first."); return; }
    setIsLoading(true);
    try {
      const options = await startPasskeyLogin(email);
      const credential = await startAuthentication({ optionsJSON: options });
      const res = await verifyPasskeyLogin(email, credential);
      if (res.access_token) {
        await login(res.access_token, res.refresh_token, true);
        toast.success("Biometric login successful");
        if (!safeTenantRedirect(res.tenant_url)) navigate("/dashboard");
      } else setError(res.detail || "Passkey login failed.");
    } catch { setError("Passkey login cancelled or failed."); }
    finally { setIsLoading(false); }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault(); setError(""); setMessage("");
    if (!email) { setError("Enter your email."); return; }
    try {
      await forgotPassword(email, window.location.origin);
      toast.success("Recovery link sent!"); setMessage("Check your email for the reset link.");
    } catch { setError("Failed to send recovery email."); }
  };

  // ── Register ──
  const handleRegister = async (e) => {
    e.preventDefault(); setError(""); setIsLoading(true);
    if (password.length < 8) {
      setError("Password must be at least 8 characters."); setIsLoading(false); return;
    }
    try {
      const payload = { email, password, role };
      if (role === "hospital") payload.hospital_name = hospitalName;
      if (role === "doctor") payload.invite_code = inviteCode;
      const res = await registerUser(payload);
      if (res.message?.includes("OTP")) {
        toast.success("Code sent!");
        if (res.subdomain) setSubdomain(res.subdomain);
        if (res.tenant_url) setTenantUrl(res.tenant_url);
        setRegStep("otp");
      }
      else setError(res.detail || "Registration error");
    } catch (err) { setError(err.message || "Registration failed"); }
    finally { setIsLoading(false); }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault(); setError(""); setIsLoading(true);
    try {
      const res = await verifyOtp(email, otp);
      if (res.access_token) {
        await login(res.access_token, res.refresh_token, res.has_passkey);
        if (res.tenant_url) setTenantUrl(res.tenant_url);
        if (res.subdomain) setSubdomain(res.subdomain);
        toast.success("Verified!"); setRegStep("passkey_prompt");
      } else setError(res.detail || "Invalid OTP");
    } catch { setError("OTP verification failed."); }
    finally { setIsLoading(false); }
  };

  const handleRegisterPasskey = async () => {
    setError(""); setIsLoading(true);
    try {
      const options = await startPasskeyRegister(email);
      const credential = await startRegistration({ optionsJSON: options });
      const res = await verifyPasskeyRegister(email, credential);
      if (res.access_token) {
        await login(res.access_token, res.refresh_token, true);
        toast.success("Passkey registered!");
        if (!safeTenantRedirect(tenantUrl)) navigate("/dashboard");
      } else setError(res.detail || "Passkey setup failed");
    } catch {
      toast("Skipped passkey setup.", { icon: "👋" });
      setTimeout(() => {
        if (!safeTenantRedirect(tenantUrl)) navigate("/dashboard");
      }, 1500);
    }
    finally { setIsLoading(false); }
  };

  const handleSkipPasskey = () => {
    if (!safeTenantRedirect(tenantUrl)) navigate("/dashboard");
  };

  return (
    <div className="min-h-screen bg-surface-soft flex flex-col items-center justify-center px-4 py-12">
      <Link to="/" className="mb-8 text-xl font-bold tracking-tight text-ink">
        {tenantName ? `${tenantName} Portal` : "AI X-Ray Analyzer"}
      </Link>

      <div className="w-full max-w-[400px] bg-canvas border border-hairline rounded-lg p-8 shadow-sm">
        <h2 className="text-2xl font-bold tracking-tight text-ink text-center mb-2">
          {isLoginMode ? (isForgotMode ? "Reset password" : "Welcome back") : "Create account"}
        </h2>
        <p className="text-sm text-mute text-center mb-6 leading-normal">
          {isLoginMode
            ? (isForgotMode ? "We'll send a recovery link" : tenantName ? `Sign in to the ${tenantName} workspace` : "Sign in to your hospital portal")
            : "Register your hospital or join one"
          }
        </p>

        {error && <div role="alert" className="mb-4 p-3 rounded-md bg-red-50 text-error text-sm text-center font-semibold border border-red-100">{error}</div>}
        {message && <div role="status" className="mb-4 p-3 rounded-md bg-success-pale text-success text-sm text-center font-semibold">{message}</div>}

        {/* ── LOGIN ── */}
        {isLoginMode && !isForgotMode && (
          <>
            <form onSubmit={handleLogin} className="space-y-3">
              <Input icon={<Mail className="w-4 h-4" />} type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} autoComplete="email" aria-label="Email address" />
              <Input icon={<Lock className="w-4 h-4" />} type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" aria-label="Password" />
              <div className="text-right">
                <button type="button" onClick={() => setIsForgotMode(true)} className="text-xs font-semibold text-mute hover:text-ink">Forgot password?</button>
              </div>
              <PrimaryButton loading={isLoading}>Sign in</PrimaryButton>
            </form>
            <Divider label="or" />
            <SecondaryButton onClick={handlePasskeyLogin} icon={<Fingerprint className="w-4 h-4" />} disabled={isLoading}>
              Sign in with Passkey
            </SecondaryButton>
          </>
        )}

        {/* ── FORGOT ── */}
        {isLoginMode && isForgotMode && (
          <form onSubmit={handleForgotPassword} className="space-y-3">
            <Input icon={<Mail className="w-4 h-4" />} type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} autoComplete="email" aria-label="Email address" />
            <PrimaryButton>Send recovery link</PrimaryButton>
            <button type="button" onClick={() => setIsForgotMode(false)} className="w-full text-sm text-mute hover:text-ink mt-2 font-medium">Back to sign in</button>
          </form>
        )}

        {/* ── REGISTER ── */}
        {!isLoginMode && regStep === "register" && (
          <form onSubmit={handleRegister} className="space-y-3">
            {!subdomain && (
              <div className="flex gap-2 mb-2" role="group" aria-label="Account type">
                <RoleTab active={role === "doctor"} onClick={() => setRole("doctor")}>Doctor</RoleTab>
                <RoleTab active={role === "hospital"} onClick={() => setRole("hospital")}>Hospital Admin</RoleTab>
              </div>
            )}
            {subdomain && (
              <div className="p-3 bg-surface-card rounded-md border border-hairline-soft mb-2 text-center">
                <p className="text-xs font-bold text-ink-soft">Joining Hospital: {tenantName || subdomain.toUpperCase()}</p>
              </div>
            )}
            {role === "hospital" && !subdomain && <Input icon={<Database className="w-4 h-4" />} placeholder="Hospital name" value={hospitalName} onChange={e => setHospitalName(e.target.value)} aria-label="Hospital name" maxLength={120} />}
            {role === "doctor" && <Input icon={<Zap className="w-4 h-4" />} placeholder="Invite code" value={inviteCode} onChange={e => setInviteCode(e.target.value)} aria-label="Invite code" />}
            <Input icon={<Mail className="w-4 h-4" />} type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} autoComplete="email" aria-label="Email address" />
            <Input icon={<Lock className="w-4 h-4" />} type="password" placeholder="Password (min 8 characters)" value={password} onChange={e => setPassword(e.target.value)} autoComplete="new-password" aria-label="Password" minLength={8} />
            <PrimaryButton loading={isLoading}>Create account</PrimaryButton>
          </form>
        )}

        {!isLoginMode && regStep === "otp" && (
          <form onSubmit={handleVerifyOtp} className="space-y-4">
            <p className="text-sm text-mute text-center leading-normal">Enter the 6-digit code sent to your email.</p>
            <input
              className="w-full text-center text-2xl tracking-[0.4em] font-mono bg-surface-card border border-hairline rounded-md px-4 py-3 focus:outline-none focus:ring-2 focus:ring-[var(--focus)] focus:border-ink transition-all"
              placeholder="000000" maxLength={6} value={otp}
              onChange={e => setOtp(e.target.value.replace(/\D/g, ""))}
              inputMode="numeric" pattern="[0-9]*" autoComplete="one-time-code"
              aria-label="Verification code"
            />
            <PrimaryButton loading={isLoading}>Verify</PrimaryButton>
            <button type="button" onClick={() => setRegStep("register")} className="w-full text-sm text-mute hover:text-ink flex items-center justify-center gap-1 font-semibold">
              <ChevronLeft className="w-3.5 h-3.5" /> Back
            </button>
          </form>
        )}

        {!isLoginMode && regStep === "passkey_prompt" && (
          <div className="text-center space-y-4">
            {subdomain && (
              <div className="p-4 bg-success-pale rounded-md text-left border border-success/10">
                <div className="flex items-center gap-2 mb-1">
                  <Globe className="w-4 h-4 text-success" />
                  <span className="text-xs font-bold text-success uppercase tracking-wider">Your Portal</span>
                </div>
                <div className="flex items-center gap-2">
                  <code className="text-sm font-mono font-bold text-ink">{tenantUrl || buildTenantUrl(subdomain)}</code>
                  <button type="button" onClick={() => { navigator.clipboard.writeText(tenantUrl || buildTenantUrl(subdomain)); toast.success("Copied!"); }} className="p-1 hover:bg-white/50 rounded" aria-label="Copy portal URL">
                    <Copy className="w-3.5 h-3.5 text-mute" />
                  </button>
                </div>
              </div>
            )}
            <div className="p-5 bg-surface-card rounded-md">
              <ShieldCheck className="w-8 h-8 text-ink mx-auto mb-2" />
              <h3 className="text-base font-semibold text-ink mb-1">Set up Passkey</h3>
              <p className="text-sm text-mute">Enable biometric login for faster, passwordless access.</p>
            </div>
            <PrimaryButton onClick={handleRegisterPasskey} icon={<Fingerprint className="w-4 h-4" />} loading={isLoading}>Setup Passkey</PrimaryButton>
            <SecondaryButton onClick={handleSkipPasskey} disabled={isLoading}>Skip for now</SecondaryButton>
          </div>
        )}

        <div className="mt-6 text-center">
          <span className="text-sm text-mute">
            {isLoginMode ? "New here? " : "Already a member? "}
            <button onClick={toggleAuth} className="font-semibold text-ink hover:underline">
              {isLoginMode ? "Create account" : "Sign in"}
            </button>
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Reusable sub-components ──

function Input({ icon, ...props }) {
  return (
    <div className="relative">
      <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-ash w-4 h-4" aria-hidden="true">
        {icon}
      </span>
      <input
        {...props}
        required
        className="w-full h-11 bg-canvas border border-hairline text-ink text-sm rounded-md pl-10 pr-4 placeholder:text-ash focus:outline-none focus:ring-2 focus:ring-[var(--focus)] focus:border-ink transition-all"
      />
    </div>
  );
}

function PrimaryButton({ children, loading, icon, onClick, type = "submit", disabled }) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={loading || disabled}
      className="w-full h-10 flex items-center justify-center gap-2 px-4 text-sm font-bold text-white bg-primary rounded-md hover:bg-primary-pressed disabled:opacity-60 transition-colors cursor-pointer"
    >
      {icon}{loading ? "Loading..." : children}
    </button>
  );
}

function SecondaryButton({ children, icon, onClick, disabled }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="w-full h-10 flex items-center justify-center gap-2 px-4 text-sm font-bold text-ink bg-secondary-bg rounded-md hover:bg-secondary-pressed disabled:opacity-60 transition-colors cursor-pointer"
    >
      {icon}{children}
    </button>
  );
}

function RoleTab({ active, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex-1 py-2 text-sm font-bold rounded-full transition-colors cursor-pointer ${
        active ? "bg-ink text-white" : "bg-surface-card text-mute hover:bg-secondary-bg"
      }`}
    >
      {children}
    </button>
  );
}

function Divider({ label }) {
  return (
    <div className="relative flex items-center justify-center my-5">
      <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-hairline" /></div>
      <span className="relative bg-canvas px-3 text-xs text-ash uppercase font-bold tracking-wider">{label}</span>
    </div>
  );
}
