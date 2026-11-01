
import { useState } from "react";
import { ApiError } from "../services/api";
import {
  registrarDespacho,
  type Despacho,
} from "../services/despachos";

export default function Despachos() {
  const [idCupo, setIdCupo] = useState("");
  const [cantidad, setCantidad] = useState("");
  const [resultado, setResultado] = useState<Despacho | null>(null);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  async function enviarDespacho(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setResultado(null);
    setCargando(true);

    try {
      const datos = await registrarDespacho({
        id_cupo: Number(idCupo),
        cantidad: Number(cantidad),
      });

      setResultado(datos);
      setIdCupo("");
      setCantidad("");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "No se pudo conectar con el servidor."
      );
    } finally {
      setCargando(false);
    }
  }

  return (
    <section className="welcome-card">
      <h2>Registro de despachos</h2>
      <p>Registra la cantidad de diésel despachada para un cupo autorizado.</p>

      <form onSubmit={enviarDespacho} className="formulario">
        <label htmlFor="idCupo">ID del cupo</label>
        <input
          id="idCupo"
          type="number"
          min="1"
          required
          value={idCupo}
          onChange={(e) => setIdCupo(e.target.value)}
          placeholder="Ej. 1"
        />

        <label htmlFor="cantidad">Litros a despachar</label>
        <input
          id="cantidad"
          type="number"
          min="0.01"
          step="0.01"
          required
          value={cantidad}
          onChange={(e) => setCantidad(e.target.value)}
          placeholder="Ej. 50"
        />

        <button type="submit" disabled={cargando}>
          {cargando ? "Registrando..." : "Registrar despacho"}
        </button>
      </form>

      {error && (
        <p className="mensaje-error" role="alert">
          {error}
        </p>
      )}

      {resultado && (
        <div className="mensaje-exito" role="status">
          <h3>Despacho registrado correctamente</h3>
          <p>Número: {resultado.id_despacho}</p>
          <p>Cupo: {resultado.id_cupo}</p>
          <p>Litros: {resultado.cantidad}</p>
          <p>Estado: {resultado.estado}</p>
        </div>
      )}
    </section>
  );
}
