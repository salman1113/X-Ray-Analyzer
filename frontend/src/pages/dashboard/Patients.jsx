import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { listPatients, createPatient, deletePatient } from "../../api/patients";
import { Users, Plus, Trash2, Eye, Search } from "lucide-react";
import Modal from "../../components/ui/Modal";
import Badge from "../../components/ui/Badge";
import LoadingSpinner from "../../components/ui/LoadingSpinner";
import EmptyState from "../../components/ui/EmptyState";
import ConfirmDialog from "../../components/ui/ConfirmDialog";

export default function Patients() {
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", age: "", gender: "M", contact: "" });
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(null);

  const load = async () => { try { setPatients(await listPatients()); } catch { /* ignore */ } finally { setLoading(false); } };
  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault(); setCreating(true); setError("");
    try {
      await createPatient({ ...form, age: parseInt(form.age, 10) });
      setShowCreate(false); setForm({ name: "", age: "", gender: "M", contact: "" });
      toast.success("Patient created"); load();
    } catch (err) { setError(err.message); } finally { setCreating(false); }
  };

  const handleDelete = async (id) => {
    try { await deletePatient(id); toast.success("Patient deleted"); setConfirmDelete(null); load(); }
    catch (err) { toast.error(err.message || "Delete failed"); }
  };

  const filtered = patients.filter((p) => p.name?.toLowerCase().includes(search.toLowerCase()) || p.patient_id?.includes(search));

  if (loading) return <div className="flex items-center justify-center py-32"><LoadingSpinner text="Loading patients..." /></div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl sm:text-[28px] font-bold text-ink tracking-[-1.2px] leading-tight">Patients</h1>
          <p className="text-sm text-mute mt-1">{patients.length} total</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="flex items-center justify-center gap-2 px-4 h-10 text-sm font-bold text-white bg-primary rounded-md hover:bg-primary-pressed transition-colors w-full sm:w-auto cursor-pointer">
          <Plus className="w-4 h-4" /> Add Patient
        </button>
      </div>

      {/* Search Bar - rounded-full, 48px height, default bg surface-card */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-ash" />
        <input
          type="text"
          placeholder="Search patients..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full h-12 pl-12 pr-4 bg-surface-card border border-hairline rounded-full text-sm text-ink placeholder:text-ash focus:outline-none focus:bg-canvas focus:ring-2 focus:ring-[var(--focus)] focus:border-ink transition-all"
        />
      </div>

      {filtered.length === 0 ? (
        <EmptyState icon={Users} title="No patients found" description={search ? "Try a different search." : "Add your first patient."} />
      ) : (
        <div className="bg-canvas border border-hairline rounded-md overflow-hidden divide-y divide-hairline">
          {filtered.map((p) => (
            <div key={p.patient_id} className="px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-surface-card rounded-full flex items-center justify-center text-ink text-xs font-bold">
                  {p.name?.charAt(0).toUpperCase()}
                </div>
                <div>
                  <p className="text-sm font-semibold text-ink">{p.name}</p>
                  <p className="text-xs text-ash">{p.age}y / {p.gender}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => navigate(`/dashboard/patients/${p.patient_id}`)} className="p-2 text-ash hover:text-ink hover:bg-surface-card rounded-md transition-colors cursor-pointer"><Eye className="w-4 h-4" /></button>
                <button onClick={() => setConfirmDelete(p.patient_id)} className="p-2 text-ash hover:text-error hover:bg-red-50 rounded-md transition-colors cursor-pointer"><Trash2 className="w-4 h-4" /></button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Add Patient">
        <form onSubmit={handleCreate} className="space-y-4">
          {error && <div className="p-3 rounded-md bg-red-50 text-error text-sm font-semibold border border-red-100">{error}</div>}
          
          <div>
            <input required placeholder="Full name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full h-11 px-4 bg-canvas border border-hairline rounded-md text-sm text-ink placeholder:text-ash focus:outline-none focus:ring-2 focus:ring-[var(--focus)] focus:border-ink transition-all" />
          </div>
          
          <div className="grid grid-cols-2 gap-3">
            <input required type="number" min="0" max="150" placeholder="Age" value={form.age} onChange={(e) => setForm({ ...form, age: e.target.value })} className="w-full h-11 px-4 bg-canvas border border-hairline rounded-md text-sm text-ink placeholder:text-ash focus:outline-none focus:ring-2 focus:ring-[var(--focus)] focus:border-ink transition-all" />
            <select value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })} className="w-full h-11 px-4 bg-canvas border border-hairline rounded-md text-sm text-ink focus:outline-none focus:ring-2 focus:ring-[var(--focus)] focus:border-ink transition-all cursor-pointer">
              <option value="M">Male</option><option value="F">Female</option><option value="Other">Other</option>
            </select>
          </div>
          
          <div>
            <input placeholder="Contact (optional)" value={form.contact} onChange={(e) => setForm({ ...form, contact: e.target.value })} className="w-full h-11 px-4 bg-canvas border border-hairline rounded-md text-sm text-ink placeholder:text-ash focus:outline-none focus:ring-2 focus:ring-[var(--focus)] focus:border-ink transition-all" />
          </div>
          
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={() => setShowCreate(false)} className="flex-1 h-10 text-sm font-bold text-ink bg-secondary-bg rounded-md hover:bg-secondary-pressed transition-colors cursor-pointer">Cancel</button>
            <button type="submit" disabled={creating} className="flex-1 h-10 text-sm font-bold text-white bg-primary rounded-md hover:bg-primary-pressed disabled:opacity-50 transition-colors cursor-pointer">{creating ? "Creating..." : "Create"}</button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog isOpen={!!confirmDelete} onClose={() => setConfirmDelete(null)} onConfirm={() => handleDelete(confirmDelete)} title="Delete Patient" message="This will permanently delete this patient and all associated data." confirmText="Delete" />
    </div>
  );
}
