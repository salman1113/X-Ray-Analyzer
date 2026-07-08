import { useState, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import toast from "react-hot-toast";
import { listScans, createScan, uploadScanImage, analyzeScan, deleteScan, getBodyParts, scanImageUrl } from "../../api/scans";
import { listPatients } from "../../api/patients";
import { ScanLine, Plus, Zap, Trash2, Eye, Loader2, Image as ImageIcon } from "lucide-react";
import Modal from "../../components/ui/Modal";
import Badge from "../../components/ui/Badge";
import LoadingSpinner from "../../components/ui/LoadingSpinner";
import EmptyState from "../../components/ui/EmptyState";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import AuthImage from "../../components/ui/AuthImage";

const STATUS_MAP = { uploaded: "info", processing: "warning", analyzed: "success", failed: "danger" };

export default function Scans() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preselectedPatient = searchParams.get("patient");
  const [scans, setScans] = useState([]);
  const [patients, setPatients] = useState([]);
  const [bodyParts, setBodyParts] = useState({});
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(!!preselectedPatient);
  const [selectedPatient, setSelectedPatient] = useState(preselectedPatient || "");
  const [bodyPart, setBodyPart] = useState("chest");
  const [selectedFile, setSelectedFile] = useState(null);
  const [creating, setCreating] = useState(false);
  const [analyzing, setAnalyzing] = useState(null);
  const [error, setError] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(null);
  const fileRef = useRef(null);

  const load = async () => {
    try {
      const [s, p, bp] = await Promise.all([listScans(), listPatients(), getBodyParts()]);
      setScans(s);
      setPatients(p);
      setBodyParts(bp);
    } catch { /* ignore */ } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!selectedPatient) { setError("Select a patient"); return; }
    setCreating(true); setError("");
    try {
      const scan = await createScan({ patient_id: selectedPatient, body_part: bodyPart, scan_type: "xray" });
      if (selectedFile) await uploadScanImage(scan.scan_id, selectedFile);
      setShowCreate(false); setSelectedFile(null); setSelectedPatient("");
      toast.success("Scan created"); load();
    } catch (err) { setError(err.message); } finally { setCreating(false); }
  };

  const handleAnalyze = async (scan) => {
    setAnalyzing(scan.scan_id);
    try {
      await analyzeScan(scan.scan_id, scan.body_part || "chest");
      toast.success("Analysis complete");
      load();
    } catch (err) { toast.error(err.message); } finally { setAnalyzing(null); }
  };

  const handleDelete = async (scanId) => {
    try { await deleteScan(scanId); toast.success("Scan deleted"); setConfirmDelete(null); load(); }
    catch (err) { toast.error(err.message); }
  };

  if (loading) return <div className="flex items-center justify-center py-32"><LoadingSpinner text="Loading scans..." /></div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl sm:text-[28px] font-bold text-ink tracking-[-1.2px] leading-tight">X-Ray Scans</h1>
          <p className="text-sm text-mute mt-1">{scans.length} total</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="flex items-center justify-center gap-2 px-4 h-10 text-sm font-bold text-white bg-primary rounded-md hover:bg-primary-pressed transition-colors w-full sm:w-auto cursor-pointer">
          <Plus className="w-4 h-4" /> New Scan
        </button>
      </div>

      {scans.length === 0 ? (
        <EmptyState icon={ScanLine} title="No scans yet" description="Create a scan to upload and analyze X-ray images." />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {scans.map((s) => {
            const patient = patients.find((p) => p.patient_id === s.patient_id);
            const bpLabel = bodyParts[s.body_part]?.label || s.body_part || "Scan";
            return (
              <div key={s.scan_id} className="bg-canvas border border-hairline rounded-md overflow-hidden flex flex-col hover:border-ash transition-all group shadow-sm hover:shadow-md">
                {/* Image / Thumbnail Container */}
                <div className="h-44 w-full bg-[#0c0c0e] relative flex items-center justify-center overflow-hidden border-b border-hairline-soft select-none">
                  {s.image_path ? (
                    <AuthImage
                      src={scanImageUrl(s.scan_id)}
                      alt={`${bpLabel} X-ray`}
                      className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-[1.04]"
                    />
                  ) : (
                    <div className="flex flex-col items-center justify-center text-ash gap-2">
                      <ScanLine className="w-8 h-8 opacity-60" strokeWidth={1.5} />
                      <span className="text-xs font-semibold">No X-ray image</span>
                    </div>
                  )}
                  {/* Floating badges */}
                  <div className="absolute top-3 left-3 flex flex-wrap gap-1.5 pointer-events-none">
                    <Badge variant={STATUS_MAP[s.status]}>{s.status}</Badge>
                    {s.ai_result && (
                      <Badge variant={s.ai_result.prediction?.toLowerCase().includes("normal") ? "success" : "purple"}>
                        {s.ai_result.prediction}
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Card Content */}
                <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
                  <div className="space-y-2">
                    <h3 className="text-sm font-bold text-ink truncate" title={patient?.name || "Unknown Patient"}>
                      {patient?.name || "Unknown Patient"}
                    </h3>
                    <p className="text-xs font-bold text-mute uppercase tracking-wider">{bpLabel}</p>
                    
                    {/* Diagnostic Summary / Status */}
                    {s.ai_result ? (
                      <div className="pt-2 flex items-center justify-between border-t border-hairline-soft">
                        <span className="text-xs text-ash font-semibold">Confidence</span>
                        <span className="text-sm font-bold text-ink">{Math.round(s.ai_result.confidence * 100)}%</span>
                      </div>
                    ) : s.image_path ? (
                      <p className="text-xs text-mute italic font-semibold pt-1">Ready for analysis</p>
                    ) : (
                      <p className="text-xs text-ash italic pt-1">Awaiting image upload</p>
                    )}
                  </div>
                  
                  {/* Card Actions */}
                  <div className="flex items-center gap-2 pt-3 border-t border-hairline-soft">
                    {s.status === "uploaded" && s.image_path && (
                      <button
                        onClick={() => handleAnalyze(s)}
                        disabled={analyzing === s.scan_id}
                        className="flex-1 h-9 px-3 text-xs font-bold text-white bg-primary rounded-md hover:bg-primary-pressed disabled:opacity-50 flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                      >
                        {analyzing === s.scan_id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
                        Analyze
                      </button>
                    )}
                    
                    <button
                      onClick={() => navigate(`/dashboard/scans/${s.scan_id}`)}
                      className={`${
                        s.status === "uploaded" && s.image_path ? "px-3" : "flex-1"
                      } h-9 bg-secondary-bg hover:bg-secondary-pressed text-ink rounded-md text-xs font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer`}
                    >
                      <Eye className="w-3.5 h-3.5" />
                      {!(s.status === "uploaded" && s.image_path) && "View Details"}
                    </button>
                    
                    <button
                      onClick={() => setConfirmDelete(s.scan_id)}
                      className="w-9 h-9 shrink-0 bg-transparent hover:bg-red-50 text-ash hover:text-error border border-hairline hover:border-red-100 rounded-md flex items-center justify-center transition-all cursor-pointer"
                      title="Delete Scan"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create scan modal */}
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="New X-Ray Scan">
        <form onSubmit={handleCreate} className="space-y-4">
          {error && <div className="p-3 rounded-md bg-red-50 text-error text-sm font-semibold border border-red-100">{error}</div>}

          {/* Patient selector */}
          <div>
            <label className="block text-xs font-bold text-ink uppercase tracking-wider mb-1.5">Select Patient</label>
            <select required value={selectedPatient} onChange={(e) => setSelectedPatient(e.target.value)} className="w-full h-11 px-4 bg-canvas border border-hairline rounded-md text-sm text-ink focus:outline-none focus:ring-2 focus:ring-[var(--focus)] focus:border-ink transition-all cursor-pointer">
              <option value="">Select patient...</option>
              {patients.map((p) => <option key={p.patient_id} value={p.patient_id}>{p.name} ({p.age}y)</option>)}
            </select>
          </div>

          {/* Body part selector (dynamic from API) */}
          <div>
            <label className="block text-xs font-bold text-ink uppercase tracking-wider mb-1.5">Body Part</label>
            <select value={bodyPart} onChange={(e) => setBodyPart(e.target.value)} className="w-full h-11 px-4 bg-canvas border border-hairline rounded-md text-sm text-ink focus:outline-none focus:ring-2 focus:ring-[var(--focus)] focus:border-ink transition-all cursor-pointer">
              {Object.entries(bodyParts).map(([key, cfg]) => (
                <option key={key} value={key}>{cfg.label}</option>
              ))}
              {Object.keys(bodyParts).length === 0 && <option value="chest">Chest / Thorax</option>}
            </select>
          </div>

          {/* Optional description of selected body part */}
          {bodyParts[bodyPart]?.description && (
            <p className="text-xs text-ash px-1 font-semibold">{bodyParts[bodyPart].description}</p>
          )}

          {/* File upload */}
          <div>
            <label className="block text-xs font-bold text-ink uppercase tracking-wider mb-1.5">Upload X-ray Image</label>
            <div onClick={() => fileRef.current?.click()} className="border-2 border-dashed border-hairline rounded-md p-8 text-center cursor-pointer hover:border-ash transition-colors bg-surface-card">
              <input ref={fileRef} type="file" accept="image/*" onChange={(e) => setSelectedFile(e.target.files[0])} className="hidden" />
              {selectedFile ? <span className="text-sm font-semibold text-ink">{selectedFile.name}</span> : <span className="text-sm text-ash font-medium">Click to upload X-ray image (optional — can upload later)</span>}
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={() => setShowCreate(false)} className="flex-1 h-10 text-sm font-bold text-ink bg-secondary-bg rounded-md hover:bg-secondary-pressed transition-colors cursor-pointer">Cancel</button>
            <button type="submit" disabled={creating} className="flex-1 h-10 text-sm font-bold text-white bg-primary rounded-md hover:bg-primary-pressed disabled:opacity-50 transition-colors cursor-pointer">{creating ? "Creating..." : "Create"}</button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog isOpen={!!confirmDelete} onClose={() => setConfirmDelete(null)} onConfirm={() => handleDelete(confirmDelete)} title="Delete Scan" message="This will permanently delete this scan." confirmText="Delete" />
    </div>
  );
}
