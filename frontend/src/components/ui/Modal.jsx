export default function Modal({ isOpen, onClose, title, children }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center">
      {/* Scrim with 50% opacity overlay */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-[1px]" onClick={onClose} />

      {/* Card: bottom sheet on mobile, centered card on desktop */}
      <div className="relative w-full max-w-md bg-[var(--canvas)] rounded-t-lg md:rounded-lg p-8 mx-0 md:mx-4 shadow-xl z-10 transition-all transform duration-300">
        {title && (
          <h2 className="text-[22px] font-semibold text-[var(--ink)] leading-[1.25] tracking-tight mb-6">{title}</h2>
        )}
        {children}
      </div>
    </div>
  );
}
