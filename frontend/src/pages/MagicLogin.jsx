import { useEffect, useRef, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { KeyRound, CheckCircle, AlertCircle } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function MagicLogin() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  const attempted = useRef(false);

  // Derive status from the token synchronously (no setState needed)
  const { status, isSuccess, token } = useMemo(() => {
    const t = searchParams.get("token");
    if (!t) return { status: "Invalid or missing Magic Link.", isSuccess: false, token: null };

    try {
      const p = JSON.parse(atob(t.split(".")[1]));
      if (p.type !== "magic_link") return { status: "Token is not a valid magic link.", isSuccess: false, token: null };
      return { status: "Successfully authenticated!", isSuccess: true, token: t };
    } catch {
      return { status: "Failed to decode secure token.", isSuccess: false, token: null };
    }
  }, [searchParams]);

  useEffect(() => {
    if (attempted.current || !isSuccess || !token) return;
    attempted.current = true;
    login(token, null, false);
    setTimeout(() => navigate("/dashboard"), 1500);
  }, [isSuccess, token, login, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-surface-soft">
      <div className="w-full max-w-md bg-canvas border border-hairline rounded-lg p-8 text-center shadow-sm">
        <div className={`w-14 h-14 rounded-md mx-auto mb-5 flex items-center justify-center ${
          isSuccess === true ? "bg-success-pale" : isSuccess === false ? "bg-red-50" : "bg-surface-card"
        }`}>
          {isSuccess === true ? (
            <CheckCircle className="text-success w-7 h-7" />
          ) : isSuccess === false ? (
            <AlertCircle className="text-error w-7 h-7" />
          ) : (
            <KeyRound className="text-ink w-7 h-7 animate-pulse" />
          )}
        </div>

        <h2 className="text-xl font-bold tracking-tight text-ink mb-2">Magic Login</h2>
        <p className={`text-sm font-semibold ${isSuccess === false ? "text-error" : "text-mute"}`}>
          {status}
        </p>

        {isSuccess === false && (
          <button
            onClick={() => navigate("/login")}
            className="mt-6 h-10 px-5 text-sm font-bold text-ink bg-secondary-bg rounded-md hover:bg-secondary-pressed transition-colors cursor-pointer"
          >
            Return to Login
          </button>
        )}
      </div>
    </div>
  );
}
