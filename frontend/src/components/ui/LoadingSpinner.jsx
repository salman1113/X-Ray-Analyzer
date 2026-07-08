export default function LoadingSpinner({ text }) {
  return (
    <div className="flex flex-col items-center gap-3">
      <div className="w-8 h-8 border-2 border-[var(--hairline)] border-t-[var(--primary)] rounded-full animate-spin" />
      {text && <p className="text-sm text-[var(--mute)]">{text}</p>}
    </div>
  );
}
