
import { request } from "./api";

export interface Cupo {
  id_cupo: number;
  id_vehiculo: number;
  placa: string;
  cantidad_autorizada: number;
  saldo_disponible: number;
  fecha_inicio: string;
  fecha_fin: string;
  estado: string;
}

export interface CupoCreate {
  id_vehiculo: number;
  cantidad_autorizada: number;
  fecha_inicio: string;
  fecha_fin: string;
}

export function listarCupos() {
  return request<Cupo[]>("/cupos/");
}

export function crearCupo(datos: CupoCreate) {
  return request<Cupo>("/cupos/", {
    method: "POST",
    body: JSON.stringify(datos),
  });
}
