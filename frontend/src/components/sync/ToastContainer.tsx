import { useSyncStore } from '../../stores/syncStore';

export default function ToastContainer() {
  const { toasts, removeToast } = useSyncStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`flex items-center gap-2 px-4 py-3 rounded-xl shadow-xl text-sm font-medium pointer-events-auto border ${
            toast.type === 'success'
              ? 'bg-green-950 text-green-100 border-green-800'
              : 'bg-red-950 text-red-100 border-red-800'
          }`}
        >
          <span>{toast.type === 'success' ? '✓' : '✗'}</span>
          <span>{toast.message}</span>
          <button
            onClick={() => removeToast(toast.id)}
            className="ml-1 opacity-50 hover:opacity-100 transition-opacity leading-none"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}
