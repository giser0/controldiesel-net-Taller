-- =====================================================================
-- ControlDiesel-Net · 02_seed.sql
-- Datos FICTICIOS de demostración. Ejecutar DESPUÉS de 01_schema.sql:
--   psql -U controldiesel -d controldiesel -f db/02_seed.sql
--
-- Usuarios de demostración (contraseña entre paréntesis):
--   admin@controldiesel.test       Administrador  (Admin#2026)
--   regulador@controldiesel.test   Regulador      (Regula#2026)
--   operador1@controldiesel.test   Operador, EST-001 (Operador1#2026)
--   operador2@controldiesel.test   Operador, EST-002 (Operador2#2026)
-- Las contraseñas se guardan como hash bcrypt; estos hashes son solo de demo.
-- Los cupos se calculan con la fecha actual para que sigan vigentes.
-- =====================================================================

INSERT INTO roles (nombre, descripcion) VALUES
  ('Administrador', 'Gestiona usuarios, estaciones, vehículos y cupos; consulta despachos, alertas, auditoría y reportes.'),
  ('Operador',      'Registra despachos en su estación asignada y consulta saldos.'),
  ('Regulador',     'Consulta despachos, alertas y reportes; observa y cierra alertas.');

INSERT INTO estaciones (codigo, nombre, ubicacion) VALUES
  ('EST-001', 'Estación Centro',   'La Paz, zona Centro (ficticia)'),
  ('EST-002', 'Estación Sur',      'La Paz, zona Sur (ficticia)'),
  ('EST-003', 'Estación El Alto',  'El Alto, Ciudad Satélite (ficticia)');

INSERT INTO vehiculos (placa, descripcion) VALUES
  ('1001-AAA', 'Camión de carga (ficticio)'),
  ('1002-BBB', 'Camión de carga (ficticio)'),
  ('1003-CCC', 'Minibús (ficticio) con cupo pequeño para pruebas de saldo'),
  ('1004-DDD', 'Volqueta (ficticia)'),
  ('1005-EEE', 'Camioneta (ficticia) con cupo vencido y cupo vigente'),
  ('1006-FFF', 'Bus (ficticio) con cupo aún no vigente');

INSERT INTO usuarios (id_rol, id_estacion, nombre, email, password_hash)
SELECT r.id_rol, e.id_estacion, u.nombre, u.email, u.hash
FROM (VALUES
  ('Administrador', NULL,      'Admin Demo',      'admin@controldiesel.test',     '$2b$12$NQFDXKqKTgOvOVNW9Mioau/VX4goMaM6k.SXLymY4BinzfRzzRJme'),
  ('Regulador',     NULL,      'Regulador Demo',  'regulador@controldiesel.test', '$2b$12$zLfXR36tudOsnN1FgZmhq.BvrkfozLU1UwCgyaen.i.sL73eAlYFe'),
  ('Operador',      'EST-001', 'Operador Uno',    'operador1@controldiesel.test', '$2b$12$mrGGVNnAw6Lc4q2CqRVvZe4KWC4yL8PHr/LflCsq6aazl14R7qUNK'),
  ('Operador',      'EST-002', 'Operador Dos',    'operador2@controldiesel.test', '$2b$12$ZsQ14IDT3l126icRj.LlT.joVSlwNgYp0ykZ3eQO.Is5LnAKSwqvO')
) AS u (rol, codigo_estacion, nombre, email, hash)
JOIN roles r ON r.nombre = u.rol
LEFT JOIN estaciones e ON e.codigo = u.codigo_estacion;

-- Cupos vigentes: mes en curso (extremos inclusivos).
-- 1001, 1002, 1004, 1005: 200 L · 1003: 50 L (para probar saldo insuficiente, RD-03).
INSERT INTO cupos (id_vehiculo, cantidad_autorizada, saldo_disponible, fecha_inicio, fecha_fin, estado)
SELECT v.id_vehiculo,
       c.litros, c.litros,
       date_trunc('month', current_date)::date,
       (date_trunc('month', current_date) + interval '1 month - 1 day')::date,
       'VIGENTE'
FROM (VALUES ('1001-AAA', 200.00), ('1002-BBB', 200.00), ('1003-CCC', 50.00),
             ('1004-DDD', 200.00), ('1005-EEE', 200.00)) AS c (placa, litros)
JOIN vehiculos v ON v.placa = c.placa;

-- Cupo VENCIDO (mes anterior) del vehículo 1005: prueba de cupo no vigente (P07)
-- y de periodos consecutivos válidos (P14).
INSERT INTO cupos (id_vehiculo, cantidad_autorizada, saldo_disponible, fecha_inicio, fecha_fin, estado)
SELECT id_vehiculo, 100.00, 0.00,
       (date_trunc('month', current_date) - interval '1 month')::date,
       (date_trunc('month', current_date) - interval '1 day')::date,
       'VENCIDO'
FROM vehiculos WHERE placa = '1005-EEE';

-- Cupo PENDIENTE (mes siguiente) del vehículo 1006, que no tiene cupo vigente (P07).
INSERT INTO cupos (id_vehiculo, cantidad_autorizada, saldo_disponible, fecha_inicio, fecha_fin, estado)
SELECT id_vehiculo, 150.00, 150.00,
       (date_trunc('month', current_date) + interval '1 month')::date,
       (date_trunc('month', current_date) + interval '2 month - 1 day')::date,
       'PENDIENTE'
FROM vehiculos WHERE placa = '1006-FFF';
