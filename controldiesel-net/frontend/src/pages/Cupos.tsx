
import { useEffect, useState } from "react";
import { ApiError } from "../services/api";
import {
  crearCupo,
  listarCupos,
  type Cupo,
} from "../services/cupos";

export default function Cupos() {
  const [cupos, setCupos] = useState<Cupo[]>([]);
  const [idVehiculo, setIdVehiculo] = useState("");
  const [cantidad, setCantidad] = useState("");
  const [fechaInicio, setFechaInicio] = useState("");
  const [fechaFin, setFechaFin] = useState("");
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [cargando, setCargando] = useState(false);

  async function cargarCupos() {
    try {
      const datos = await listarCupos();
      setCupos(datos);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudieron cargar los cupos."
      );
    }
  }

  useEffect(() => {
    cargarCupos();
  }, []);

  async function enviarCupo(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setMensaje("");
    setCargando(true);

    try {
      await crearCupo({
        id_vehiculo: Number(idVehiculo),
        cantidad_autorizada: Number(cantidad),
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
      });

      setMensaje("Cupo registrado correctamente.");
      setIdVehiculo("");
      setCantidad("");
      setFechaInicio("");
      setFechaFin("");
      await cargarCupos();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo registrar el cupo."
      );
    } finally {
      setCargando(false);
    }
  }

  return (
    <section className="welcome-card">
      <h2>Gestión de cupos</h2>

      <form onSubmit={enviarCupo} className="formulario">
        <label htmlFor="vehiculo">ID del vehículo</label>
        <input
          id="vehiculo"
          type="number"
          min="1"
          required
          value={idVehiculo}
          onChange={(e) => setIdVehiculo(e.target.value)}
        />

        <label htmlFor="cantidad">Cantidad autorizada (litros)</label>
        <input
          id="cantidad"
          type="number"
          min="0.01"
          step="0.01"
          required
          value={cantidad}
          onChange={(e) => setCantidad(e.target.value)}
        />

        <label htmlFor="inicio">Fecha de inicio</label>
        <input
          id="inicio"
          type="date"
          required
          value={fechaInicio}
          onChange={(e) => setFechaInicio(e.target.value)}
        />

        <label htmlFor="fin">Fecha de finalización</label>
        <input
          id="fin"
          type="date"
          required
          value={fechaFin}
          onChange={(e) => setFechaFin(e.target.value)}
        />

        <button type="submit" disabled={cargando}>
          {cargando ? "Registrando..." : "Crear cupo"}
        </button>
      </form>

      {mensaje && <p className="mensaje-exito">{mensaje}</p>}
      {error && <p className="mensaje-error" role="alert">{error}</p>}

      <h3>Cupos registrados</h3>

      <button type="button" onClick={cargarCupos}>
        Actualizar lista
      </button>

      {cupos.length === 0 ? (
        <p>No hay cupos registrados.</p>
      ) : (
        <div className="tabla-contenedor">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Placa</th>
                <th>Autorizado</th>
                <th>Saldo</th>
                <th>Inicio</th>
                <th>Fin</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {cupos.map((cupo) => (
                <tr key={cupo.id_cupo}>
                  <td>{cupo.id_cupo}</td>
                  <td>{cupo.placa}</td>
                  <td>{cupo.cantidad_autorizada} L</td>
                  <td>{cupo.saldo_disponible} L</td>
                  <td>{cupo.fecha_inicio}</td>
                  <td>{cupo.fecha_fin}</td>
                  <td>{cupo.estado}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
