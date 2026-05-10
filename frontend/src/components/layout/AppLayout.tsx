import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import BottomNav from './BottomNav';
import SyncIndicator from '../sync/SyncIndicator';

export default function AppLayout() {
  return (
    <div className="flex h-screen bg-slate-950 text-slate-100">
      <Sidebar />
      <main className="flex-1 overflow-y-auto pb-16 md:pb-0">
        <Outlet />
      </main>
      <BottomNav />
      {/* Sync indicator flotante solo en móvil, sobre el BottomNav */}
      <div className="fixed bottom-20 right-4 z-40 md:hidden">
        <SyncIndicator compact />
      </div>
    </div>
  );
}
