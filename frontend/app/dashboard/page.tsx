'use client';

import { useRequireAuth } from '@/lib/hooks/useRequireAuth';
import { useAuthStore } from '@/lib/stores/authStore';

export default function DashboardPage() {
  const { isAuthenticated } = useRequireAuth();
  const signOut = useAuthStore((s) => s.signOut);

  if (!isAuthenticated) return null;

  return (
    <main className="max-w-3xl mx-auto px-6 py-10">
      <h1 className="text-2xl font-semibold">Panel</h1>
      <p className="mt-2 text-muted-foreground">
        Tu tablero de proyectos llega con la Iteración 1 (flujo B2). Esta ruta pasará a /projects.
      </p>

      <div className="mt-6 flex flex-wrap gap-3">
        <button
          className="bg-primary text-primary-foreground rounded px-3 py-2 hover:bg-primary/90"
          type="button"
          onClick={signOut}
        >
          Salir
        </button>
      </div>
    </main>
  );
}
