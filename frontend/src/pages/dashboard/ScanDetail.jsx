import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { getScan, uploadScanImage, analyzeScan, getBodyParts, gradcamUrl, scanImageUrl } from "../../api/scans";
import { getPatient } from "../../api/patients";
import {
  ArrowLeft, Upload, Zap, Loader2, CheckCircle,
  AlertCircle, Brain, Activity, ChevronDown,
  FileText, Heart, Eye, ShieldAlert,
  Clock, User, Hash, Crosshair
} from "lucide-react";
import Badge from "../../components/ui/Badge";
import LoadingSpinner from "../../components/ui/LoadingSpinner";
import AuthImage from "../../components/ui/AuthImage";

const renderClinicalExplanation = (text) => {
  if (!text) return null;
  const lines = text.split("\n");
  return (
    <div className="space-y-1">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={idx} className="h-1.5" />;

        // Header Check
        if (trimmed.startsWith("#")) {
          const headerText = trimmed.replace(/^#+\s*/, "");
          return (
            <h3 key={idx} className="text-xs font-bold uppercase tracking-wider text-ash mt-5 mb-2.5 first:mt-0">
              {headerText}
            </h3>
          );
        }

        // Bullet Point Check
        if (trimmed.startsWith("-") || trimmed.startsWith("*") || trimmed.startsWith("•")) {
          const bulletText = trimmed.replace(/^[-*•]\s*/, "");
          const parts = bulletText.split(/(\*\*.*?\*\*)/g);
          return (
            <div key={idx} className="flex items-start gap-2 text-[13px] leading-relaxed pl-1 py-0.5">
              <span className="w-1.5 h-1.5 bg-primary rounded-full mt-1.5 shrink-0" />
              <span className="flex-1 font-semibold text-ink-soft">
                {parts.map((part, pIdx) => {
                  if (part.startsWith("**") && part.endsWith("**")) {
                    return <strong key={pIdx} className="font-bold text-ink">{part.slice(2, -2)}</strong>;
                  }
                  return part;
                })}
              </span>
            </div>
          );
        }

        // Regular Text Line
        const parts = trimmed.split(/(\*\*.*?\*\*)/g);
        return (
          <p key={idx} className="text-[13px] text-body leading-relaxed font-semibold">
            {parts.map((part, pIdx) => {
              if (part.startsWith("**") && part.endsWith("**")) {
                return <strong key={pIdx} className="font-bold text-ink">{part.slice(2, -2)}</strong>;
              }
              return part;
            })}
          </p>
        );
      })}
    </div>
  );
};

export default function ScanDetail() {
  const { scanId } = useParams();
  const navigate = useNavigate();
  const fileRef = useRef(null);
  const [scan, setScan] = useState(null);
  const [patient, setPatient] = useState(null);
  const [bodyParts, setBodyParts] = useState({});
  const [selectedBodyPart, setSelectedBodyPart] = useState("chest");
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [zoomImage, setZoomImage] = useState(false);
  const [activeTab, setActiveTab] = useState("results");

  const load = async () => {
    try {
      const [s, bp] = await Promise.all([getScan(scanId), getBodyParts()]);
      setScan(s);
      setBodyParts(bp);
      setSelectedBodyPart(s.body_part || "chest");
      if (s.patient_id) {
        const p = await getPatient(s.patient_id);
        setPatient(p);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [scanId]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    try {
      await uploadScanImage(scanId, file);
      toast.success("Image uploaded successfully");
      load();
    } catch (err) {
      toast.error(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      await analyzeScan(scanId, selectedBodyPart);
      toast.success("AI analysis complete");
      load();
    } catch (err) {
      toast.error(err.message || "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-[60vh]"><LoadingSpinner size="lg" text="Loading scan..." /></div>;

  if (!scan) {
    return (
      <div className="text-center py-20 text-mute">
        <AlertCircle className="w-10 h-10 text-ash mx-auto mb-3" />
        <p className="font-semibold">Scan not found.</p>
        <button onClick={() => navigate(-1)} className="mt-3 text-primary hover:underline text-sm font-bold">Go back</button>
      </div>
    );
  }

  const statusColors = { uploaded: "info", processing: "warning", analyzed: "success", failed: "danger" };
  const ai = scan.ai_result;
  const bpLabel = bodyParts[scan.body_part]?.label || ai?.body_part_label || scan.body_part || "Scan";

  const isNormal = ai?.prediction?.toLowerCase().includes("normal");
  let diagBg = "bg-emerald-50"; let diagBorder = "border-emerald-200"; let diagColor = "#10b981";
  let diagText = "text-emerald-700"; let diagIcon = <Heart className="w-5 h-5 text-emerald-600" />;
  if (ai && !isNormal) {
    if (ai.confidence >= 0.85) {
      diagBg = "bg-red-50"; diagBorder = "border-red-200"; diagColor = "#e60023";
      diagText = "text-red-700"; diagIcon = <ShieldAlert className="w-5 h-5 text-red-600" />;
    } else {
      diagBg = "bg-amber-50"; diagBorder = "border-amber-200"; diagColor = "#d97706";
      diagText = "text-amber-700"; diagIcon = <AlertCircle className="w-5 h-5 text-amber-600" />;
    }
  }

  const showControls = scan.image_path && (scan.status === "uploaded" || scan.status === "analyzed" || scan.status === "failed");

  return (
    <div className="h-full flex flex-col min-h-0">
      {/* Top Bar — redesigned premium layout */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-4 shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={() => navigate(-1)}
            className="w-8 h-8 rounded-full bg-canvas border border-hairline flex items-center justify-center text-mute hover:text-ink hover:bg-surface-card transition-all cursor-pointer shadow-sm shrink-0"
            title="Back"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="min-w-0">
            <h1 className="text-xl sm:text-[22px] font-bold text-ink tracking-tight truncate leading-tight">{bpLabel} Analysis</h1>
            <p className="text-xs text-ash font-semibold mt-0.5">X-Ray diagnostics overview</p>
          </div>
          <Badge variant={statusColors[scan.status] || "default"}>{scan.status?.toUpperCase()}</Badge>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-canvas border border-hairline rounded-full text-xs text-ink-soft font-bold shadow-sm">
            <User className="w-3.5 h-3.5 text-primary" />
            <span>{patient?.name || "Patient"}</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-canvas border border-hairline rounded-full text-xs text-mute font-bold shadow-sm">
            <Clock className="w-3.5 h-3.5 text-ash" />
            <span>{new Date(scan.created_at || Date.now()).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-card border border-hairline-soft rounded-full text-xs text-mute font-mono font-bold">
            <Hash className="w-3.5 h-3.5 text-ash" />
            <span>ID: {scan.scan_id?.slice(0, 8)}</span>
          </div>
        </div>
      </div>

      {/* Grid Layout — separated industrial standard cards */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">

        {/* Left Column: Image Viewer + Controls */}
        <div className="lg:col-span-5 space-y-4">
          
          {/* Medical Viewer Card */}
          <div className="bg-[#0c0c0e] border border-hairline rounded-md overflow-hidden relative h-[280px] flex items-center justify-center shadow-sm group">
            {scan.image_path ? (
              <>
                <AuthImage
                  src={scanImageUrl(scan.scan_id)}
                  alt={`${bpLabel} X-ray`}
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-[1.02]"
                />
                
                {/* DICOM Style HUD Overlays */}
                <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-transparent to-black/60 pointer-events-none p-3.5 flex flex-col justify-between text-[10px] font-mono text-white/70 select-none">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-bold text-white tracking-wider truncate max-w-[140px]">{patient?.name || "ANONYMOUS"}</p>
                      <p className="text-[9px] opacity-75">ID: {scan.scan_id?.slice(0, 8)}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-primary tracking-wider">{bpLabel?.toUpperCase()}</p>
                      <p className="text-[9px] opacity-75">{new Date(scan.created_at || Date.now()).toLocaleDateString()}</p>
                    </div>
                  </div>
                  
                  {/* Center Crosshair Overlay */}
                  <div className="absolute inset-0 flex items-center justify-center opacity-15 pointer-events-none">
                    <div className="w-8 h-[1px] bg-white"></div>
                    <div className="h-8 w-[1px] bg-white absolute"></div>
                    <div className="w-16 h-16 border border-dashed border-white rounded-full absolute"></div>
                  </div>

                  <div className="flex justify-between items-end">
                    <div>
                      <p className="opacity-75">W: 420 L: 180</p>
                      <p className="opacity-75">ZOOM: COMPACT (COVER)</p>
                    </div>
                    <div className="text-right">
                      <p className="opacity-75 font-bold text-emerald-400">AI PROCESSED</p>
                    </div>
                  </div>
                </div>

                {/* View Fullscreen button */}
                <button
                  onClick={() => setZoomImage(true)}
                  className="absolute top-3 right-3 p-2 bg-black/75 hover:bg-black/90 text-white rounded-full transition-all cursor-pointer shadow-md hover:scale-105 flex items-center justify-center"
                  title="Open Diagnostic Viewer"
                >
                  <Eye className="w-3.5 h-3.5" />
                </button>
              </>
            ) : (
              <div onClick={() => fileRef.current?.click()} className="flex flex-col items-center gap-2.5 cursor-pointer p-8 text-center">
                <input ref={fileRef} type="file" accept="image/*,.dicom" onChange={handleUpload} className="hidden" />
                <div className="p-3.5 bg-white/5 rounded-full border border-white/10">
                  {uploading ? <Loader2 className="w-6 h-6 text-white animate-spin" /> : <Upload className="w-6 h-6 text-white/60" />}
                </div>
                <p className="text-sm font-semibold text-white/90">{uploading ? "Uploading..." : "Upload X-Ray"}</p>
                <p className="text-xs text-white/40 font-semibold">PNG, JPG, or DICOM</p>
              </div>
            )}
          </div>

          {/* Controls Card */}
          {showControls && (
            <div className="bg-canvas border border-hairline rounded-md p-4 space-y-4 shadow-sm">
              <div className="flex items-center gap-2">
                <div className="relative flex-1">
                  <select
                    value={selectedBodyPart}
                    onChange={(e) => setSelectedBodyPart(e.target.value)}
                    className="w-full h-10 pl-3 pr-8 bg-surface-card border border-hairline rounded-md text-xs appearance-none focus:outline-none focus:ring-2 focus:ring-[var(--focus)]/20 font-bold text-ink-soft cursor-pointer"
                  >
                    {Object.entries(bodyParts).map(([key, cfg]) => (
                      <option key={key} value={key}>{cfg.label}</option>
                    ))}
                    {Object.keys(bodyParts).length === 0 && <option value="chest">Chest / Thorax</option>}
                  </select>
                  <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-ash pointer-events-none" />
                </div>
                <button
                  onClick={handleAnalyze}
                  disabled={analyzing}
                  className="h-10 px-4 bg-primary hover:bg-primary-pressed text-white rounded-md text-xs font-bold transition-all disabled:opacity-50 flex items-center gap-1.5 cursor-pointer shrink-0"
                >
                  {analyzing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
                  {analyzing ? "Running..." : scan.status === "analyzed" ? "Re-Analyze" : "Analyze"}
                </button>
              </div>

              {bodyParts[selectedBodyPart]?.conditions && (
                <div className="flex flex-wrap gap-1.5 pt-3 border-t border-hairline-soft">
                  {bodyParts[selectedBodyPart].conditions.map((c) => (
                    <span key={c} className="text-[11px] px-2.5 py-1 bg-surface-card text-ink-soft rounded-full border border-hairline-soft font-bold">
                      {c.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Results */}
        <div className="lg:col-span-7 bg-canvas border border-hairline rounded-md overflow-hidden shadow-sm flex flex-col min-h-[480px]">
          {ai ? (
            <>
              {/* Tabs */}
              <div className="flex border-b border-hairline shrink-0">
                {[
                  { id: "results", label: "Diagnosis", icon: Heart },
                  { id: "report", label: "Report", icon: FileText },
                  ...(ai.gradcam_path ? [{ id: "heatmap", label: "Heatmap", icon: Crosshair }] : [])
                ].map(({ id, label, icon: Icon }) => ( // eslint-disable-line no-unused-vars
                  <button
                    key={id}
                    onClick={() => setActiveTab(id)}
                    className={`flex items-center gap-1.5 px-4 py-3 text-xs font-bold border-b-2 transition-colors cursor-pointer ${
                      activeTab === id
                        ? "border-primary text-primary"
                        : "border-transparent text-mute hover:text-ink"
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />{label}
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6 animate-fade-in">
                {activeTab === "results" && (
                  <>
                    {/* Diagnosis Card: Premium left-accent card */}
                    <div className={`${diagBg} ${diagBorder} border border-l-4 rounded-md p-5 relative overflow-hidden bg-gradient-to-r from-canvas to-transparent`} style={{ borderLeftColor: diagColor }}>
                      <div className="absolute -right-2 -top-2 opacity-[0.06]"><Brain className="w-20 h-20" strokeWidth={1} /></div>
                      <div className="flex items-center gap-4">
                        <div className="p-2.5 bg-canvas rounded-md shrink-0 border border-hairline-soft shadow-sm">{diagIcon}</div>
                        <div className="flex-1 min-w-0">
                          <p className={`text-[10px] font-bold uppercase tracking-wider ${diagText}`}>Primary Diagnosis</p>
                          <p className="text-xl font-bold tracking-tight text-ink truncate mt-0.5">{ai.prediction?.replace(/_/g, " ")}</p>
                        </div>
                        <div className="text-right shrink-0">
                          <p className="text-2xl font-bold tracking-tight" style={{ color: diagColor }}>{Math.round(ai.confidence * 100)}%</p>
                          <p className="text-[10px] text-ash font-bold">confidence</p>
                        </div>
                      </div>
                      <div className="mt-4 h-1.5 bg-canvas rounded-full overflow-hidden border border-hairline-soft">
                        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${ai.confidence * 100}%`, backgroundColor: diagColor }} />
                      </div>
                    </div>

                    {/* Patient Summary */}
                    {ai.patient_summary && (
                      typeof ai.patient_summary === "string" ? (
                        <div className="bg-surface-soft rounded-md p-5 border border-hairline-soft border-l-4 border-l-ash">
                          <p className="text-[10px] font-bold uppercase tracking-wider text-ash mb-2 flex items-center gap-1">Summary</p>
                          <p className="text-sm text-body leading-relaxed font-semibold">{ai.patient_summary}</p>
                        </div>
                      ) : (
                        <div className={`rounded-md border border-hairline border-l-4 overflow-hidden bg-canvas ${
                          ai.patient_summary.urgency === "urgent" ? "border-l-primary"
                            : ai.patient_summary.urgency === "soon" ? "border-l-amber-500"
                            : ai.patient_summary.urgency === "watch" ? "border-l-blue-500"
                            : "border-l-success"
                        }`}>
                          <div className="p-5 space-y-4">
                            <div className="flex items-center gap-2 pb-2 border-b border-hairline-soft">
                              <span className="text-lg">{ai.patient_summary.emoji}</span>
                              <h3 className="text-sm font-bold text-ink tracking-tight">{ai.patient_summary.headline}</h3>
                            </div>
                            <div className="space-y-3.5 text-[13px] text-body">
                              <div className="bg-surface-soft rounded-md p-3.5 border border-hairline-soft">
                                <p className="text-[9px] font-bold uppercase tracking-wider text-ash mb-1">What the AI detected</p>
                                <p className="font-bold text-ink-soft">{ai.patient_summary.what_found}</p>
                              </div>
                              {ai.patient_summary.what_it_means && (
                                <div className="px-1.5 py-1">
                                  <p className="text-[9px] font-bold uppercase tracking-wider text-ash mb-1">What this means</p>
                                  <p className="leading-relaxed font-semibold text-body">{ai.patient_summary.what_it_means}</p>
                                </div>
                              )}
                              {ai.patient_summary.what_to_do && (
                                <div className={`rounded-md p-3.5 border border-l-2 ${
                                  ai.patient_summary.urgency === "urgent" ? "bg-red-50/50 border-red-200 border-l-primary"
                                    : ai.patient_summary.urgency === "soon" ? "bg-amber-50/50 border-amber-200 border-l-amber-500"
                                    : ai.patient_summary.urgency === "watch" ? "bg-blue-50/50 border-blue-200 border-l-blue-500"
                                    : "bg-emerald-50/50 border-emerald-200 border-l-success"
                                }`}>
                                  <p className="text-[9px] font-bold uppercase tracking-wider opacity-75 mb-1">Recommended Action</p>
                                  <p className="font-bold text-ink-soft leading-normal">{ai.patient_summary.what_to_do}</p>
                                </div>
                              )}
                              {ai.patient_summary.confidence_text && (
                                <p className="text-[11px] italic text-ash pt-2 border-t border-hairline font-semibold">{ai.patient_summary.confidence_text}</p>
                              )}
                            </div>
                          </div>
                        </div>
                      )
                    )}

                    {/* Probabilities */}
                    {ai.probabilities && Object.keys(ai.probabilities).length > 0 && (
                      <div className="space-y-3">
                        <p className="text-[10px] font-bold uppercase tracking-wider text-ash flex items-center gap-1.5">
                          <Activity className="w-3.5 h-3.5 text-primary" />Condition Probabilities
                        </p>
                        <div className="space-y-3.5 bg-surface-soft p-5 rounded-md border border-hairline-soft">
                          {Object.entries(ai.probabilities).sort(([, a], [, b]) => b - a).map(([condition, prob]) => {
                            const isTop = condition === ai.prediction;
                            return (
                              <div key={condition} className="flex items-center gap-3">
                                <span className={`text-xs w-28 truncate font-bold ${isTop ? "text-primary" : "text-mute"}`}>
                                  {condition.replace(/_/g, " ")}
                                </span>
                                <div className="flex-1 h-1.5 bg-canvas rounded-full overflow-hidden border border-hairline-soft">
                                  <div className="h-full rounded-full transition-all duration-700" style={{ width: `${prob * 100}%`, backgroundColor: isTop ? diagColor : "#dadad3" }} />
                                </div>
                                <span className="text-[11px] font-mono text-ash w-8 text-right font-bold">{Math.round(prob * 100)}%</span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </>
                )}

                {activeTab === "report" && (
                  <div className="space-y-4">
                    {ai.rag_explanation ? (
                      <>
                        <div className="flex items-center justify-between border-b border-hairline pb-2">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-ash flex items-center gap-1.5">
                            <FileText className="w-3.5 h-3.5 text-mute" />Clinical Interpretation
                          </span>
                          <span className="text-[9px] font-mono text-ash bg-surface-card px-2 py-0.5 rounded font-bold">AI GENERATED</span>
                        </div>
                        <div className="text-[14px] leading-[1.6] text-body font-medium">
                          {renderClinicalExplanation(ai.rag_explanation)}
                        </div>
                      </>
                    ) : (
                      <div className="flex flex-col items-center justify-center py-12 text-center">
                        <FileText className="w-8 h-8 text-ash mb-2" />
                        <p className="text-sm font-semibold text-mute">No clinical report available</p>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === "heatmap" && ai.gradcam_path && (
                  <div className="space-y-4">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-ash flex items-center gap-1.5">
                      <Crosshair className="w-3.5 h-3.5 text-purple-600" />Grad-CAM Attention Map
                    </p>
                    <div className="bg-[#0a0a0f] rounded-md overflow-hidden flex items-center justify-center border border-hairline-soft">
                      <AuthImage src={gradcamUrl(scan.scan_id)} alt="Grad-CAM heatmap" className="w-full object-contain max-h-[50vh] rounded-none" />
                    </div>
                    <p className="text-[11px] text-ash text-center font-semibold">Red/orange highlights indicate regions driving the AI diagnosis</p>
                  </div>
                )}
              </div>
            </>
          ) : scan.status === "processing" ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-3">
              <Loader2 className="w-7 h-7 text-primary animate-spin" />
              <p className="text-sm font-bold text-ink">Analyzing...</p>
              <p className="text-[11px] text-ash font-semibold">Computing diagnostic probabilities</p>
            </div>
          ) : scan.status === "failed" ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-3">
              <AlertCircle className="w-7 h-7 text-error" />
              <p className="text-sm font-bold text-error">Analysis failed</p>
              <button onClick={handleAnalyze} className="h-8 px-4 text-xs bg-primary text-white font-bold rounded-md hover:bg-primary-pressed transition-colors cursor-pointer">Retry</button>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center gap-2 text-center px-6">
              <CheckCircle className="w-7 h-7 text-ash" />
              <p className="text-sm font-bold text-ink">No results yet</p>
              <p className="text-[11px] text-ash max-w-[200px] font-semibold">Upload an image and run analysis to see results</p>
            </div>
          )}
        </div>
      </div>

      {/* Medical Lightbox Modal */}
      {zoomImage && (
        <div className="fixed inset-0 z-50 flex flex-col bg-black/95 animate-fade-in p-4 sm:p-6 justify-center items-center">
          <div className="absolute top-4 right-4 flex gap-3">
            <button
              onClick={() => setZoomImage(false)}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-md text-xs font-bold transition-colors cursor-pointer"
            >
              Close Viewer
            </button>
          </div>
          <div className="w-full max-w-4xl h-[85vh] flex items-center justify-center">
            <AuthImage
              src={scanImageUrl(scan.scan_id)}
              alt={`${bpLabel} X-ray`}
              className="max-w-full max-h-full object-contain rounded-md"
            />
          </div>
          <p className="text-white/60 text-xs font-mono mt-3">ID: {scan.scan_id} &middot; {bpLabel} Diagnostic View</p>
        </div>
      )}
    </div>
  );
}
