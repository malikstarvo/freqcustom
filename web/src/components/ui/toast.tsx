import { useEffect, useState } from "react";
import { X, CheckCircle, AlertTriangle, Info } from "lucide-react";

export type ToastType = "success" | "error" | "warning" | "info";

export interface ToastMessage {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
}

export function ToastContainer({ toasts, onDismiss }: {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}) {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2" role="status" aria-live="polite">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onDismiss }: {
  toast: ToastMessage;
  onDismiss: (id: string) => void;
}) {
  const [opacity, setOpacity] = useState(0);
  useEffect(() => {
    const timer = setTimeout(() => setOpacity(1), 50);
    const dismiss = setTimeout(() => onDismiss(toast.id), 4000);
    return () => { clearTimeout(timer); clearTimeout(dismiss); };
  }, [toast.id, onDismiss]);

  const colors = {
    success: "border-profit/25 bg-profit/10 text-profit",
    error: "border-loss/25 bg-loss/10 text-loss",
    warning: "border-warning/25 bg-warning/10 text-warning",
    info: "border-primary/25 bg-primary/10 text-primary",
  };

  const icons = {
    success: <CheckCircle size={16} aria-hidden="true" />,
    error: <AlertTriangle size={16} aria-hidden="true" />,
    warning: <AlertTriangle size={16} aria-hidden="true" />,
    info: <Info size={16} aria-hidden="true" />,
  };

  return (
    <div
      className={`flex items-start gap-3 px-4 py-3 rounded-lg border shadow-lg backdrop-blur-sm max-w-sm transition-opacity duration-300 ${colors[toast.type]}`}
      style={{ opacity }}
    >
      {icons[toast.type]}
      <div className="flex-1 min-w-0">
        <div className="font-semibold text-sm">{toast.title}</div>
        {toast.message && <div className="text-xs opacity-80 mt-0.5">{toast.message}</div>}
      </div>
      <button onClick={() => onDismiss(toast.id)} className="opacity-60 hover:opacity-100" aria-label="Dismiss">
        <X size={14} aria-hidden="true" />
      </button>
    </div>
  );
}
