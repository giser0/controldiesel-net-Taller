-- Clave para identificar solicitudes repetidas de despacho.
ALTER TABLE despachos
ADD COLUMN idempotency_key VARCHAR(100);

-- Una misma clave no puede registrar dos despachos
-- para el mismo usuario.
CREATE UNIQUE INDEX uq_despachos_usuario_idempotencia
ON despachos (id_usuario, idempotency_key)
WHERE idempotency_key IS NOT NULL;