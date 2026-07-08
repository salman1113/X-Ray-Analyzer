import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { getPatient, updatePatient } from "../../api/patients";
import { listScans } from "../../api/scans";
import { ArrowLeft, ScanLine, Plus, Clock, CheckCircle, AlertCircle, Loader2, Pencil } from "lucide-react";
import Badge from "../../components/ui/Badge";
import LoadingSpinner from "../../components/ui/LoadingSpinner";
import Modal from "../../components/ui/Modal";

const STATUS_MAP = {
  uploaded: { label: "Uploaded", variant: "info", icon: Clock },
  processing: { label: "Processing", variant: "warning", icon: Loader2 },
  analyzed: { label: "Analyzed", variant: "success", icon: CheckCircle },
  failed: { label: "Failed", variant: "danger", icon: AlertCircle },
};

export default function PatientDetail() {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const [patient, setPatient] = useState(null);
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showEdit, setShowEdit] = useState(false);
  const [editForm, setEditForm] = useState({ name: "", age: "", gender: "", contact: "" });
  const [saving, setSaving] = useState(false);

  const load = async () => {
    try {
      const [p, s] = await Promise.all([
        getPatient(patientId),
        listScans(patientId),
      ]);
      setPatient(p);
      setScans(s);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [patientId]); // eslint-disable-line react-hooks/exhaustive-deps

  const openEdit = () => {
    setEditForm({
      name: patient.name || "",
      age: patient.age?.toString() || "",
      gender: patient.gender || "M",
      contact: patient.contact || "",
    });
    setShowEdit(true);
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await updatePatient(patientId, { ...editForm, age: parseInt(editForm.age, 10) });
      toast.success("Patient updated successfully");
      setShowEdit(false);
      load();
    } catch (err) {
      toast.error(err.message || "Failed to update patient");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <LoadingSpinner size="lg" text="Loading patient..." />
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="text-center py-20">
        <p className="text-mute">Patient not found.</p>
        <button onClick={() => navigate("/dashboard/patients")} className="mt-4 text-primary font-bold hover:underline">Back to Patients</button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <button onClick={() => navigate("/dashboard/patients")} className="flex items-center gap-2 text-sm text-mute hover:text-ink transition-colors cursor-pointer font-semibold">
        <ArrowLeft className="w-4 h-4" /> Back to Patients
      </button>

      {/* Patient info */}
      <div className="bg-canvas border border-hairline rounded-md p-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="w-16 h-16 rounded-md bg-surface-card text-primary flex items-center justify-center text-2xl font-bold">
              {patient.name?.charAt(0).toUpperCase()}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-ink tracking-tight">{patient.name}</h1>
              <p className="text-ash text-sm mt-1">
                {patient.age}y &middot; {patient.gender} &middot; {patient.contact || "No contact"}
              </p>
              <p className="text-xs text-ash font-mono mt-1">ID: {patient.patient_id}</p>
            </div>
          </div>
          <button onClick={openEdit} className="flex items-center gap-2 h-10 px-4 border border-hairline bg-transparent rounded-md text-sm font-bold text-mute hover:bg-surface-card hover:text-ink transition-colors cursor-pointer">
            <Pencil className="w-4 h-4" /> Edit
          </button>
        </div>
      </div>

      {/* Scans */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-ink tracking-tight">Scans ({scans.length})</h2>
        <button onClick={() => navigate(`/dashboard/scans?patient=${patientId}`)} className="flex items-center gap-2 px-4 h-10 bg-primary text-white rounded-md text-sm font-bold hover:bg-primary-pressed transition-colors cursor-pointer">
          <Plus className="w-4 h-4" /> New Scan
        </button>
      </div>

      {scans.length === 0 ? (
        <div className="text-center py-12 text-ash">
          <ScanLine className="w-10 h-10 mx-auto mb-3 text-ash" />
          <p className="font-semibold">No scans for this patient yet.</p>
        </div>
      ) : (
        <div className="bg-canvas border border-hairline rounded-md overflow-hidden divide-y divide-hairline">
          {scans.map((s) => {
            const status = STATUS_MAP[s.status] || STATUS_MAP.uploaded;
            return (
              <div key={s.scan_id} className="px-6 py-5 flex items-center justify-between hover:bg-surface-card transition-colors cursor-pointer" onClick={() => navigate(`/dashboard/scans/${s.scan_id}`)}>
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-md bg-surface-card text-ash flex items-center justify-center">
                    <ScanLine className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="font-semibold text-ink text-sm">{s.scan_type?.replace("_", " ")} scan</p>
                    <p className="text-xs text-ash font-mono">ID: {s.scan_id?.slice(0, 8)}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant={status.variant}>{status.label}</Badge>
                  {s.ai_result && (
                    <Badge variant="purple">{s.ai_result.prediction} ({Math.round(s.ai_result.confidence * 100)}%)</Badge>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
      
      {/* Edit Patient Modal */}
      <Modal isOpen={showEdit} onClose={() => setShowEdit(false)} title="Edit Patient">
        <form onSubmit={handleUpdate} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-ink uppercase tracking-wider mb-1.5">Full Name</label>
            <input required value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} className="w-full h-11 px-4 bg-canvas border border-hairline rounded-md text-sm text-ink placeholder:text-ash focus:outline-none focus:ring-2 focus:ring-[var(--focus)] focus:border-ink transition-all" />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-ink uppercase tracking-wider mb-1.5">Age</label>
              <input required type="number" min="0" max="150" value={editForm.age} onChange={(e) => setEditForm({ ...editForm, age: e.target.value })} className="w-full h-11 px-4 bg-canvas border border-hairline rounded-md text-sm text-ink placeholder:text-ash focus:outline-none focus:ring-2 focus:ring-[var(--focus)] focus:border-ink transition-all" />
            </div>
            <div>
              <label className="block text-xs font-bold text-ink uppercase tracking-wider mb-1.5">Gender</label>
              <select value={editForm.gender} onChange={(e) => setEditForm({ ...editForm, gender: e.target.value })} className="w-full h-11 px-4 bg-canvas border border-hairline rounded-md text-sm text-ink focus:outline-none focus:ring-2 focus:ring-[var(--focus)] focus:border-ink transition-all cursor-pointer">
                <option value="M">Male</option>
                <option value="F">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>
          
          <div>
            <label className="block text-xs font-bold text-ink uppercase tracking-wider mb-1.5">Contact</label>
            <input value={editForm.contact} onChange={(e) => setEditForm({ ...editForm, contact: e.target.value })} className="w-full h-11 px-4 bg-canvas border border-hairline rounded-md text-sm text-ink placeholder:text-ash focus:outline-none focus:ring-2 focus:ring-[var(--focus)] focus:border-ink transition-all" placeholder="+91 9876543210" />
          </div>
          
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={() => setShowEdit(false)} className="flex-1 h-10 text-sm font-bold text-ink bg-secondary-bg rounded-md hover:bg-secondary-pressed transition-colors cursor-pointer">Cancel</button>
            <button type="submit" disabled={saving} className="flex-1 h-10 text-sm font-bold text-white bg-primary rounded-md hover:bg-primary-pressed transition-colors disabled:opacity-50 cursor-pointer">
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
