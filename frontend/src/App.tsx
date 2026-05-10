import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';
import Home from './pages/Home';
import Comprobantes from './pages/Comprobantes';
import Ingresos from './pages/Ingresos';
import Contactos from './pages/Contactos';
import Reportes from './pages/Reportes';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/comprobantes" element={<Comprobantes />} />
          <Route path="/ingresos" element={<Ingresos />} />
          <Route path="/contactos" element={<Contactos />} />
          <Route path="/reportes" element={<Reportes />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
