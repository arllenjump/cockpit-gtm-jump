import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./Layout";
import Login from "./Login";

export type Usuario = { email: string; name: string };

export default function App() {
  const [usuario, setUsuario] = useState<Usuario | null | undefined>(undefined);

  useEffect(() => {
    fetch("/api/me")
      .then((r) => (r.ok ? r.json() : null))
      .then(setUsuario)
      .catch(() => setUsuario(null));
  }, []);

  if (usuario === undefined) return null;

  return (
    <Routes>
      <Route path="/login" element={usuario ? <Navigate to="/" /> : <Login />} />
      <Route path="/*" element={usuario ? <Layout usuario={usuario} /> : <Navigate to="/login" />} />
    </Routes>
  );
}
