import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';
import Home from './pages/Home';
import Comprobantes from './pages/Comprobantes';
import ComprobanteForm from './pages/ComprobanteForm';
import Contactos from './pages/Contactos';
import ContactoForm from './pages/ContactoForm';
import Ingresos from './pages/Ingresos';
import IngresoForm from './pages/IngresoForm';
import Reportes from './pages/Reportes';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/comprobantes" element={<Comprobantes />} />
          <Route path="/comprobantes/nuevo" element={<ComprobanteForm />} />
          <Route path="/comprobantes/:id/editar" element={<ComprobanteForm />} />
          <Route path="/contactos" element={<Contactos />} />
          <Route path="/contactos/nuevo" element={<ContactoForm />} />
          <Route path="/contactos/:id/editar" element={<ContactoForm />} />
          <Route path="/ingresos" element={<Ingresos />} />
          <Route path="/ingresos/nuevo" element={<IngresoForm />} />
          <Route path="/ingresos/:id/editar" element={<IngresoForm />} />
          <Route path="/reportes" element={<Reportes />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
