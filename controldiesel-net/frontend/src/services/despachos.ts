
import { request } from "./api";

export interface DespachoCreate {
  id_cupo: number;
  cantidad: number;
}

export interface Despacho {
  id_despacho: number;
  id_cupo: number;
  id_estacion: number;
  id_usuario: number;
  cantidad: number;
  fecha_hora: string;
  estado: string;
}

export function registrarDespacho(datos: DespachoCreate) {
  return request<Despacho>("/despachos/", {
    method: "POST",
    body: JSON.stringify(datos),
  });
}
