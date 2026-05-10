# Prompt — Fase 2 Bloque 2.1: Setup Frontend PWA

## Contexto

Backend completo (Fase 1 cerrada). Ahora arrancamos el frontend PWA.

Leer `CLAUDE.md` y `docs/especificacion_tecnica.md` sección 4 (estructura de carpetas) y sección 5 (stack frontend) antes de empezar.

## Stack frontend (confirmado)

- React 18
- Vite
- Tailwind CSS 3
- React Router v6
- Dexie.js (wrapper de IndexedDB para offline)
- Workbox (Service Worker — solo setup básico en este bloque)
- Zustand (estado global)

## Alcance de este bloque

**Solo setup y scaffolding.** No implementar pantallas ni lógica de negocio.

### Hacer:

1. Desde la raíz del proyecto, crear carpeta `frontend/` con Vite + React + TypeScript:
   ```
   npm create vite@latest frontend -- --template react-ts
   ```

2. Instalar dependencias:
   ```
   npm install react-router-dom dexie dexie-react-hooks zustand recharts
   npm install -D tailwindcss @tailwindcss/vite
   ```

3. Configurar Tailwind con el plugin de Vite (`@tailwindcss/vite`) en `vite.config.ts`

4. Configurar `vite.config.ts`:
   - Plugin de Tailwind
   - Proxy de `/api` a `http://localhost:8000` (para desarrollo)

5. PWA manifest — crear `public/manifest.json`:
   ```json
   {
     "name": "TributarioPY",
     "short_name": "TributarioPY",
     "start_url": "/",
     "display": "standalone",
     "background_color": "#ffffff",
     "theme_color": "#0f172a",
     "icons": []
   }
   ```
   Agregar `<link rel="manifest">` en `index.html`.

6. Service Worker — crear `public/sw.js` mínimo (solo registro, sin caching aún):
   ```js
   self.addEventListener('install', () => self.skipWaiting());
   self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));
   ```
   Registrar en `src/main.tsx`.

7. Crear estructura de carpetas vacía:
   ```
   frontend/src/
   ├── components/       # Componentes reutilizables
   ├── pages/            # Pantallas (una por ruta)
   ├── hooks/            # Custom hooks
   ├── services/
   │   ├── api.ts        # HTTP client (fetch wrapper contra backend)
   │   ├── db.ts         # Dexie.js — schema IndexedDB
   │   └── sync.ts       # Placeholder (Fase 3)
   ├── stores/           # Zustand stores
   ├── utils/            # Helpers
   ├── types/            # TypeScript types/interfaces
   ├── App.tsx           # Router setup
   └── main.tsx          # Entry point
   ```

8. `src/services/db.ts` — Definir schema de Dexie.js (espejo de PostgreSQL):
   ```ts
   import Dexie, { type Table } from 'dexie';

   export interface ContactoLocal {
     id: string;          // UUID
     ruc: string;
     razon_social: string;
     nombre_fantasia?: string;
     tipo: 'cliente' | 'proveedor' | 'ambos';
     es_frecuente: boolean;
     sync_status: 'pending' | 'synced' | 'conflict';
     created_at: string;
     updated_at: string;
     deleted_at?: string;
   }

   // Definir interfaces para: ComprobanteLocal, ImputacionFiscalLocal,
   // ArchivoAdjuntoLocal, IngresoLocal, CategoriaIRPLocal, SyncQueueItem
   // Basarse en docs/erd.md para los campos.

   export class TributarioDatabase extends Dexie {
     contactos!: Table<ContactoLocal>;
     comprobantes!: Table<ComprobanteLocal>;
     imputaciones!: Table<ImputacionFiscalLocal>;
     adjuntos!: Table<ArchivoAdjuntoLocal>;
     ingresos!: Table<IngresoLocal>;
     categorias_irp!: Table<CategoriaIRPLocal>;
     sync_queue!: Table<SyncQueueItem>;

     constructor() {
       super('tributario_py');
       this.version(1).stores({
         contactos: 'id, ruc, tipo, sync_status',
         comprobantes: 'id, contacto_id, periodo_fiscal, tipo_operacion, fecha_emision, sync_status',
         imputaciones: 'id, comprobante_id, categoria_irp_id',
         adjuntos: 'id, comprobante_id, sync_status',
         ingresos: 'id, contacto_id, tipo_ingreso, periodo_devengado, sync_status',
         categorias_irp: 'id, codigo',
         sync_queue: '++autoId, tabla, registro_id, operacion, timestamp',
       });
     }
   }

   export const db = new TributarioDatabase();
   ```
   
   Nota: las categorías IRP y reglas de imputación son read-only en el frontend. Se descargan del backend en el primer pull y se cachean en IndexedDB. No se editan offline.

9. `src/services/api.ts` — Fetch wrapper básico:
   ```ts
   const BASE_URL = '/api/v1';

   async function request<T>(path: string, options?: RequestInit): Promise<T> {
     const res = await fetch(`${BASE_URL}${path}`, {
       headers: { 'Content-Type': 'application/json', ...options?.headers },
       ...options,
     });
     if (!res.ok) throw new Error(`API error: ${res.status}`);
     return res.json();
   }

   export const api = {
     get: <T>(path: string) => request<T>(path),
     post: <T>(path: string, body: unknown) => request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
     put: <T>(path: string, body: unknown) => request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
     delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
   };
   ```

10. `src/App.tsx` — Router con rutas placeholder:
    ```tsx
    import { BrowserRouter, Routes, Route } from 'react-router-dom';

    // Páginas placeholder (crearlas como componentes mínimos)
    import Home from './pages/Home';

    export default function App() {
      return (
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Home />} />
            {/* Rutas por agregar en bloque 2.3:
              /comprobantes
              /comprobantes/nuevo
              /contactos
              /ingresos
              /reportes
            */}
          </Routes>
        </BrowserRouter>
      );
    }
    ```

11. `src/pages/Home.tsx` — Página placeholder que confirma que todo funciona:
    - Mostrar "TributarioPY" como título
    - Mostrar estado de conexión con el backend (fetch a `/api/v1/categorias-irp` como health check)
    - Mostrar estado de IndexedDB (Dexie inicializado correctamente)

## Diseño

- **Mobile-first**. Tailwind breakpoints: diseñar para `sm` primero, adaptar para `md`/`lg`.
- Viewport meta tag en `index.html`: `<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">`
- Color scheme: tema oscuro `slate-900` como base, acentos con `blue-500`. Definir después — por ahora solo que funcione.

## NO hacer en este bloque

- No implementar pantallas de CRUD
- No implementar sincronización
- No instalar Workbox (viene en Fase 3, el SW manual alcanza por ahora)
- No agregar Recharts todavía (viene en bloque 2.5)
- No configurar PWA icons (viene después)

## Validaciones al terminar

1. `cd frontend && npm run dev` levanta sin errores
2. Abrir `http://localhost:5173` muestra la página Home
3. El proxy a `/api` funciona (Home muestra datos de categorías IRP del backend)
4. IndexedDB "tributario_py" aparece en DevTools → Application → IndexedDB
5. `public/manifest.json` aparece en DevTools → Application → Manifest
6. Service Worker registrado en DevTools → Application → Service Workers
7. No hay errores en consola del browser
