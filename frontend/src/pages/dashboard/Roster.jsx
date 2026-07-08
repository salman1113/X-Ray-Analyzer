import { useState, useEffect } from "react";
import toast from "react-hot-toast";
import { listRoster, removeDoctor } from "../../api/users";
import { useAuth } from "../../context/AuthContext";
import { Users, Trash2, Copy } from "lucide-react";
import Badge from "../../components/ui/Badge";
import LoadingSpinner from "../../components/ui/LoadingSpinner";
import EmptyState from "../../components/ui/EmptyState";
import ConfirmDialog from "../../components/ui/ConfirmDialog";

export default function Roster() {
  const { user } = useAuth();
  const [roster, setRoster] = useState([]);
  const [loading, setLoading] = useState(true);
  const [confirmRemove, setConfirmRemove] = useState(null);

  const load = async () => {
    try {
      const data = await listRoster();
      setRoster(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleRemove = async (email) => {
    try {
      await removeDoctor(email);
      toast.success(`${email} removed from hospital`);
      setConfirmRemove(null);
      load();
    } catch (err) {
      toast.error(err.message || "Failed to remove doctor");
    }
  };

  if (loading) return <div className="flex items-center justify-center py-32"><LoadingSpinner size="lg" text="Loading roster..." /></div>;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl sm:text-[28px] font-bold text-ink tracking-[-1.2px] leading-tight">Staff Roster</h1>
          <p className="text-sm text-mute mt-1">{roster.length} doctor{roster.length !== 1 ? "s" : ""} in your hospital.</p>
        </div>
      </div>

      {/* Invite code banner */}
      {user?.invite_code && (
        <div className="bg-surface-card border border-hairline rounded-md p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <p className="font-bold text-ink tracking-tight">Invite Code</p>
            <p className="text-sm text-primary font-semibold">Share this code with doctors to join your hospital.</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xl font-mono font-bold text-ink bg-canvas px-4 py-2 rounded-md border border-hairline tracking-widest">{user.invite_code}</span>
            <button onClick={() => { navigator.clipboard.writeText(user.invite_code); toast.success("Invite code copied!"); }} className="p-2 bg-secondary-bg hover:bg-secondary-pressed text-ink rounded-md transition-colors cursor-pointer" title="Copy">
              <Copy className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {roster.length === 0 ? (
        <EmptyState icon={Users} title="No doctors yet" description="Share your invite code to onboard doctors." />
      ) : (
        <div className="bg-canvas border border-hairline rounded-md overflow-hidden divide-y divide-hairline">
          {roster.map((d) => (
            <div key={d.email} className="px-6 py-5 flex items-center justify-between hover:bg-surface-card transition-colors">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-surface-card text-ink flex items-center justify-center font-bold text-sm">
                  {d.email?.charAt(0).toUpperCase()}
                </div>
                <div>
                  <p className="font-semibold text-ink text-sm">{d.email}</p>
                  <p className="text-xs text-ash font-medium">{d.role}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant={d.is_verified ? "success" : "warning"}>
                  {d.is_verified ? "Verified" : "Pending"}
                </Badge>
                <Badge variant={d.has_passkey ? "info" : "default"}>
                  {d.has_passkey ? "Passkey" : "Password"}
                </Badge>
                <button onClick={() => setConfirmRemove(d.email)} className="p-2 text-ash hover:text-error hover:bg-red-50 rounded-md transition-colors cursor-pointer" title="Remove">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <ConfirmDialog
        isOpen={!!confirmRemove}
        onClose={() => setConfirmRemove(null)}
        onConfirm={() => handleRemove(confirmRemove)}
        title="Remove Doctor"
        message={`Remove ${confirmRemove} from your hospital? They will lose access to all tenant resources.`}
        confirmText="Remove"
      />
    </div>
  );
}
