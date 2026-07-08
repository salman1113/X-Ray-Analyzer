export default function ConfirmDialog({ isOpen, onClose, onConfirm, title, message, confirmText = "Confirm" }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Scrim */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-[1px]" onClick={onClose} />
      
      {/* Card */}
      <div className="relative w-full max-w-sm bg-[var(--canvas)] rounded-lg p-8 mx-4 shadow-xl z-10">
        <h3 className="text-[22px] font-semibold text-[var(--ink)] leading-[1.25] tracking-tight mb-2">{title}</h3>
        <p className="text-sm text-[var(--mute)] mb-6 leading-relaxed">{message}</p>
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 h-10 inline-flex items-center justify-center text-sm font-bold text-[var(--ink)] bg-[var(--secondary-bg)] rounded-md hover:bg-[var(--secondary-pressed)] transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 h-10 inline-flex items-center justify-center text-sm font-bold text-[var(--on-primary)] bg-[var(--primary)] rounded-md hover:bg-[var(--primary-pressed)] transition-colors cursor-pointer"
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
