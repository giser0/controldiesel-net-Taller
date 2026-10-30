
import { request, setToken } from "./api";
import type { Usuario } from "../types";

export async function login(
  email: string,
  password: string
): Promise<void> {
  const data = await request<{ access_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

  setToken(data.access_token);
}

export const me = () => request<Usuario>("/auth/me");
