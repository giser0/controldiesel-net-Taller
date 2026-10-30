
import { useEffect, useState } from "react";
import Login from "./pages/Login";
import { clearToken, getToken } from "./services/api";
import { me } from "./services/auth";
import type { Usuario } from "./types";

export default function App() {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      setCargando(false);
      return;
    }

    me()
      .then((datos) => setUsuario(datos))
      .catch(() => {
        clearToken();
        setUsuario(null);
      })
      .finally(() => setCargando(false));
  }, []);

  if (cargando) {
    return <p className="loading">Cargando ControlDiesel-Net...</p>;
  }

  if (!usuario) {
    return <Login />;
  }

  const cerrarSesion = () => {
    clearToken();
    setUsuario(null);
  };

  return (
    <main className="dashboard">
      <header className="dashboard-header">
        <div>
          <h1>ControlDiesel-Net</h1>
          <p>Panel de gestión y auditoría logística</p>
        </div>

        <button onClick={cerrarSesion}>Cerrar sesión</button>
      </header>

      <section className="welcome-card">
        <h2>¡Bienvenido, {usuario.nombre}!</h2>
        <p>Correo: {usuario.email}</p>
        <p>Rol: {usuario.rol}</p>
        <p>
          {usuario.id_estacion !== null
            ? `Estación asignada: ${usuario.id_estacion}`
            : "Sin estación asignada"}
        </p>
      </section>

      <section className="welcome-card">
        <h2>Menú principal</h2>

        {usuario.rol === "Administrador" && (
          <ul>
            <li>Gestión de usuarios</li>
            <li>Gestión de estaciones</li>
            <li>Gestión de vehículos</li>
            <li>Auditoría del sistema</li>
          </ul>
        )}

        {usuario.rol === "Regulador" && (
          <ul>
            <li>Consulta de vehículos</li>
            <li>Revisión de alertas</li>
            <li>Consulta de despachos</li>
            <li>Auditoría logística</li>
          </ul>
        )}

        {usuario.rol === "Operador" && (
          <ul>
            <li>Consulta de vehículos</li>
            <li>Registro de despachos</li>
            <li>Consulta de cupos</li>
          </ul>
        )}
      </section>
    </main>
  );
}
