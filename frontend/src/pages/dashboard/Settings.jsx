import { useState } from "react";
import toast from "react-hot-toast";
import { startPasskeyRegister, verifyPasskeyRegister } from "../../api/auth";
import { startRegistration } from "@simplewebauthn/browser";
import { useAuth } from "../../context/AuthContext";
import { Fingerprint, ShieldCheck, Mail, Lock } from "lucide-react";

export default function DashboardSettings() {
  const { user, reload } = useAuth();
  const [hasPasskey, setHasPasskey] = useState(localStorage.getItem("has_passkey") === "true");
  const [setting, setSetting] = useState(false);

  const handleCreatePasskey = async () => {
    setSetting(true);
    try {
      const options = await startPasskeyRegister(user.email);
      const credential = await startRegistration({ optionsJSON: options });
      const res = await verifyPasskeyRegister(user.email, credential);
      if (res.access_token) { localStorage.setItem("has_passkey", "true"); setHasPasskey(true); toast.success("Passkey registered!"); reload(); }
    } catch { toast.error("Passkey setup cancelled."); } finally { setSetting(false); }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl sm:text-[28px] font-bold text-ink tracking-[-1.2px] leading-tight">Account</h1>
        <p className="text-sm text-mute mt-1">Security and identity settings.</p>
      </div>

      <div className="bg-canvas border border-hairline rounded-md p-6 space-y-6">
        {/* Passkey */}
        <div className="flex items-center gap-4">
          <div className={`p-3 rounded-md ${hasPasskey ? "bg-success-pale" : "bg-surface-card"}`}>
            {hasPasskey ? <ShieldCheck className="w-6 h-6 text-success" /> : <Fingerprint className="w-6 h-6 text-ink" />}
          </div>
          <div className="flex-1">
            <h3 className="text-base font-bold text-ink tracking-tight">Biometric Security</h3>
            <p className="text-sm text-mute mt-0.5">{hasPasskey ? "Passkey active — passwordless login enabled." : "Set up a passkey for faster, safer login."}</p>
          </div>
          {!hasPasskey && (
            <button onClick={handleCreatePasskey} disabled={setting} className="h-10 px-4 text-sm font-bold text-white bg-primary rounded-md hover:bg-primary-pressed transition-colors cursor-pointer disabled:opacity-50">
              {setting ? "Setting up..." : "Setup Passkey"}
            </button>
          )}
        </div>

        <div className="border-t border-hairline" />

        {/* Account info */}
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <Mail className="w-4 h-4 text-ash" />
            <div>
              <p className="text-xs font-bold text-ash uppercase tracking-wider">Email</p>
              <p className="text-sm font-semibold text-ink mt-0.5">{user?.email}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Lock className="w-4 h-4 text-ash" />
            <div>
              <p className="text-xs font-bold text-ash uppercase tracking-wider">Auth Method</p>
              <p className="text-sm font-semibold text-ink mt-0.5">{hasPasskey ? "Passkey (biometric)" : "Password"}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
