import { useState, useEffect } from "react";
import toast from "react-hot-toast";
import { listTenants, deactivateTenant, updateTenant } from "../../api/tenants";
import { Building2, Trash2, Pencil } from "lucide-react";
import Badge from "../../components/ui/Badge";
import LoadingSpinner from "../../components/ui/LoadingSpinner";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import Modal from "../../components/ui/Modal";

export default function AdminTenants() {
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [confirmDeactivate, setConfirmDeactivate] = useState(null);
  const [editTenant, setEditTenant] = useState(null);
  const [editForm, setEditForm] = useState({ name: "", plan: "free", max_users: 5, max_scans_per_month: 100 });
  const [saving, setSaving] = useState(false);

  const load = async () => {
    try {
      const data = await listTenants();
      setTenants(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const openEdit = (t) => {
    setEditForm({
      name: t.name || "",
      plan: t.plan || "free",
      max_users: t.max_users || 5,
      max_scans_per_month: t.max_scans_per_month || 100,
    });
    setEditTenant(t);
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await updateTenant(editTenant.hospital_id, {
        ...editForm,
        max_users: parseInt(editForm.max_users, 10),
        max_scans_per_month: parseInt(editForm.max_scans_per_month, 10),
      });
      toast.success(`${editForm.name} updated successfully`);
      setEditTenant(null);
      load();
    } catch (err) {
      toast.error(err.message || "Failed to update tenant");
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async (hospitalId) => {
    try {
      await deactivateTenant(hospitalId);
      toast.success("Tenant deactivated");
      setConfirmDeactivate(null);
      load();
    } catch (err) {
      toast.error(err.message || "Failed to deactivate tenant");
    }
  };

  if (loading) return <div className="flex items-center justify-center py-32"><LoadingSpinner size="lg" text="Loading tenants..." /></div>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl sm:text-[28px] font-bold text-ink tracking-[-1.2px] leading-tight">All Hospitals</h1>
        <p className="text-sm text-mute mt-1">{tenants.length} registered hospital{tenants.length !== 1 ? "s" : ""}.</p>
      </div>

      <div className="bg-canvas border border-hairline rounded-md overflow-hidden divide-y divide-hairline">
        {tenants.map((t) => (
          <div key={t.hospital_id} className="px-6 py-5 flex items-center justify-between hover:bg-surface-card transition-colors">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-md bg-surface-card text-primary flex items-center justify-center">
                <Building2 className="w-5 h-5" strokeWidth={1.5} />
              </div>
              <div>
                <p className="font-bold text-ink tracking-tight">{t.name}</p>
                <p className="text-xs text-ash font-mono mt-0.5">Code: {t.invite_code} &middot; {t.max_users} users &middot; {t.max_scans_per_month} scans/mo</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant={t.is_active ? "success" : "danger"}>{t.is_active ? "Active" : "Inactive"}</Badge>
              <Badge variant="info">{t.plan || "free"}</Badge>
              <button onClick={() => openEdit(t)} className="p-2 text-ash hover:text-primary hover:bg-surface-card rounded-md transition-colors cursor-pointer" title="Edit">
                <Pencil className="w-4 h-4" />
              </button>
              {t.is_active && (
                <button onClick={() => setConfirmDeactivate(t.hospital_id)} className="p-2 text-ash hover:text-error hover:bg-red-50 rounded-md transition-colors cursor-pointer" title="Deactivate">
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Edit Tenant Modal */}
      <Modal isOpen={!!editTenant} onClose={() => setEditTenant(null)} title={`Edit ${editTenant?.name || "Tenant"}`}>
        <form onSubmit={handleUpdate} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-ink uppercase tracking-wider mb-1.5">Hospital Name</label>
            <input required value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} className="w-full h-11 px-4 bg-canvas border border-hairline rounded-md text-sm text-ink focus:outline-none focus:ring-2 focus:ring-[var(--focus)] focus:border-ink transition-all" />
          </div>
          <div>
            <label className="block text-xs font-bold text-ink uppercase tracking-wider mb-1.5">Plan</label>
            <select value={editForm.plan} onChange={(e) => setEditForm({ ...editForm, plan: e.target.value })} className="w-full h-11 px-4 bg-canvas border border-hairline rounded-md text-sm text-ink focus:outline-none focus:ring-2 focus:ring-[var(--focus)] focus:border-ink transition-all cursor-pointer">
              <option value="free">Free</option>
              <option value="basic">Basic</option>
              <option value="pro">Pro</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-ink uppercase tracking-wider mb-1.5">Max Users</label>
              <input required type="number" min="1" value={editForm.max_users} onChange={(e) => setEditForm({ ...editForm, max_users: e.target.value })} className="w-full h-11 px-4 bg-canvas border border-hairline rounded-md text-sm text-ink focus:outline-none focus:ring-2 focus:ring-[var(--focus)] focus:border-ink transition-all" />
            </div>
            <div>
              <label className="block text-xs font-bold text-ink uppercase tracking-wider mb-1.5">Max Scans/Month</label>
              <input required type="number" min="1" value={editForm.max_scans_per_month} onChange={(e) => setEditForm({ ...editForm, max_scans_per_month: e.target.value })} className="w-full h-11 px-4 bg-canvas border border-hairline rounded-md text-sm text-ink focus:outline-none focus:ring-2 focus:ring-[var(--focus)] focus:border-ink transition-all" />
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={() => setEditTenant(null)} className="flex-1 h-10 text-sm font-bold text-ink bg-secondary-bg rounded-md hover:bg-secondary-pressed transition-colors cursor-pointer">Cancel</button>
            <button type="submit" disabled={saving} className="flex-1 h-10 text-sm font-bold text-white bg-primary rounded-md hover:bg-primary-pressed transition-colors disabled:opacity-50 cursor-pointer">
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={!!confirmDeactivate}
        onClose={() => setConfirmDeactivate(null)}
        onConfirm={() => handleDeactivate(confirmDeactivate)}
        title="Deactivate Tenant"
        message="This will disable the hospital and all associated users will lose access. This action cannot be undone."
        confirmText="Deactivate"
      />
    </div>
  );
}
