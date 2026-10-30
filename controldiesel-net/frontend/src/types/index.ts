
export interface Usuario {
  id_usuario: number;
  nombre: string;
  email: string;
  id_estacion: number | null;
  rol: "Administrador" | "Operador" | "Regulador";
}
