import { BrowserRouter, Routes, Route } from 'react-router-dom';
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
