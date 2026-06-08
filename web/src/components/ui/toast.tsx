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
    <div className="fixed top-4 right-4 z-50 space-y-2">
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
    success: "border-green-500/50 bg-green-950/80 text-green-400",
    error: "border-red-500/50 bg-red-950/80 text-red-400",
    warning: "border-yellow-500/50 bg-yellow-950/80 text-yellow-400",
    info: "border-cyan-500/50 bg-cyan-950/80 text-cyan-400",
  };

  const icons = {
    success: <CheckCircle size={16} />,
    error: <AlertTriangle size={16} />,
    warning: <AlertTriangle size={16} />,
    info: <Info size={16} />,
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
      <button onClick={() => onDismiss(toast.id)} className="opacity-60 hover:opacity-100">
        <X size={14} />
      </button>
    </div>
  );
}
