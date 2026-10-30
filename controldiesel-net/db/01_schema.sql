-- =====================================================================
-- ControlDiesel-Net · 01_schema.sql
-- Esquema de base de datos (PostgreSQL 14+). Fuente: docs/diccionario.md
--
-- Ejecutar con:  psql -U controldiesel -d controldiesel -f db/01_schema.sql
-- Repetir desde cero (solo desarrollo, BORRA TODO):
--   DROP SCHEMA public CASCADE; CREATE SCHEMA public;
--
-- Convenciones: snake_case, instantes en TIMESTAMPTZ (UTC), litros en
-- NUMERIC(12,2), baja lógica con "activo", estados con CHECK ... IN (...).
-- =====================================================================

-- Necesaria para la restricción que impide cupos superpuestos (EXCLUDE).
-- Si tu usuario no es superusuario, créala una vez con el usuario postgres.
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ---------------------------------------------------------------------
-- 1. Catálogos y administración
-- ---------------------------------------------------------------------
CREATE TABLE roles (
    id_rol       INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre       VARCHAR(30)  NOT NULL UNIQUE,
    descripcion  VARCHAR(150)
);

CREATE TABLE estaciones (
    id_estacion  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo       VARCHAR(20)  NOT NULL UNIQUE,
    nombre       VARCHAR(100) NOT NULL,
    ubicacion    VARCHAR(200),
    activo       BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE TABLE usuarios (
    id_usuario     INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_rol         INT          NOT NULL REFERENCES roles (id_rol),
    -- Obligatoria solo para Operadores: esa regla la aplica el servicio.
    id_estacion    INT          REFERENCES estaciones (id_estacion),
    nombre         VARCHAR(100) NOT NULL,
    email          VARCHAR(150) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    activo         BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE TABLE vehiculos (
    id_vehiculo  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    placa        VARCHAR(15)  NOT NULL UNIQUE,
    descripcion  VARCHAR(100),
    activo       BOOLEAN      NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- 2. Cupos y despachos (núcleo)
-- ---------------------------------------------------------------------
CREATE TABLE cupos (
    id_cupo              INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_vehiculo          INT           NOT NULL REFERENCES vehiculos (id_vehiculo),
    cantidad_autorizada  NUMERIC(12,2) NOT NULL,
    saldo_disponible     NUMERIC(12,2) NOT NULL,
    fecha_inicio         DATE          NOT NULL,
    fecha_fin            DATE          NOT NULL,
    estado               VARCHAR(20)   NOT NULL DEFAULT 'PENDIENTE',

    CONSTRAINT cupos_cantidad_positiva CHECK (cantidad_autorizada > 0),
    -- El saldo nunca es negativo ni supera lo autorizado: evita sobregiros
    -- aunque falle el código.
    CONSTRAINT cupos_saldo_valido CHECK (saldo_disponible >= 0
                                         AND saldo_disponible <= cantidad_autorizada),
    CONSTRAINT cupos_fechas_validas CHECK (fecha_inicio <= fecha_fin),
    CONSTRAINT cupos_estado_valido CHECK (estado IN ('PENDIENTE', 'VIGENTE', 'VENCIDO')),
    -- Un vehículo no puede tener dos cupos PENDIENTE/VIGENTE con periodos
    -- que se solapan (los extremos cuentan: '[]').
    CONSTRAINT cupos_sin_solape EXCLUDE USING gist (
        id_vehiculo WITH =,
        daterange(fecha_inicio, fecha_fin, '[]') WITH &&
    ) WHERE (estado IN ('PENDIENTE', 'VIGENTE'))
);

CREATE TABLE despachos (
    id_despacho  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_cupo      INT           NOT NULL REFERENCES cupos (id_cupo),
    id_estacion  INT           NOT NULL REFERENCES estaciones (id_estacion),
    id_usuario   INT           NOT NULL REFERENCES usuarios (id_usuario),
    cantidad     NUMERIC(12,2) NOT NULL,
    fecha_hora   TIMESTAMPTZ   NOT NULL DEFAULT now(),
    estado       VARCHAR(20)   NOT NULL DEFAULT 'CONFIRMADO',

    CONSTRAINT despachos_cantidad_positiva CHECK (cantidad > 0),
    CONSTRAINT despachos_estado_valido CHECK (estado IN ('CONFIRMADO'))
);

-- Ventanas de RD-01/RD-02 (por cupo y tiempo) y reportes por estación.
CREATE INDEX idx_despachos_cupo_fecha     ON despachos (id_cupo, fecha_hora);
CREATE INDEX idx_despachos_estacion_fecha ON despachos (id_estacion, fecha_hora);
CREATE INDEX idx_despachos_usuario        ON despachos (id_usuario);

-- ---------------------------------------------------------------------
-- 3. Alertas y seguimiento
-- ---------------------------------------------------------------------
CREATE TABLE alertas (
    id_alerta       INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_vehiculo     INT          NOT NULL REFERENCES vehiculos (id_vehiculo),
    tipo            VARCHAR(10)  NOT NULL,
    estado          VARCHAR(20)  NOT NULL DEFAULT 'PENDIENTE',
    descripcion     TEXT,
    fecha_creacion  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    fecha_ultima    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    contador        INT          NOT NULL DEFAULT 1,

    CONSTRAINT alertas_tipo_valido   CHECK (tipo IN ('RD-01', 'RD-02')),
    CONSTRAINT alertas_estado_valido CHECK (estado IN ('PENDIENTE', 'EN_REVISION', 'CERRADA')),
    CONSTRAINT alertas_contador_min  CHECK (contador >= 1)
);

-- Una sola alerta ABIERTA por vehículo y tipo (política de alertas repetidas).
-- Cerrada una alerta, un evento posterior puede crear otra.
CREATE UNIQUE INDEX uq_alerta_abierta
    ON alertas (id_vehiculo, tipo)
    WHERE estado IN ('PENDIENTE', 'EN_REVISION');

CREATE TABLE alerta_despacho (
    id_alerta    INT NOT NULL REFERENCES alertas (id_alerta),
    id_despacho  INT NOT NULL REFERENCES despachos (id_despacho),
    PRIMARY KEY (id_alerta, id_despacho)
);

CREATE TABLE revisiones_alerta (
    id_revision      INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_alerta        INT          NOT NULL REFERENCES alertas (id_alerta),
    id_usuario       INT          NOT NULL REFERENCES usuarios (id_usuario),
    estado_anterior  VARCHAR(20)  NOT NULL,
    estado_nuevo     VARCHAR(20)  NOT NULL,
    observaciones    TEXT,
    resultado        VARCHAR(100),
    fecha_hora       TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT revisiones_estados_validos CHECK (
        estado_anterior IN ('PENDIENTE', 'EN_REVISION', 'CERRADA')
        AND estado_nuevo IN ('PENDIENTE', 'EN_REVISION', 'CERRADA')),
    CONSTRAINT revisiones_resultado_valido CHECK (
        resultado IS NULL OR resultado IN ('JUSTIFICADA', 'REQUIERE_SEGUIMIENTO')),
    -- Al cerrar una alerta debe quedar el resultado de la revisión (RN-09).
    CONSTRAINT revisiones_cierre_con_resultado CHECK (
        estado_nuevo <> 'CERRADA' OR resultado IS NOT NULL)
);

CREATE INDEX idx_revisiones_alerta ON revisiones_alerta (id_alerta, fecha_hora);

-- ---------------------------------------------------------------------
-- 4. Auditoría (incluye intentos de despacho rechazados, RD-03)
-- ---------------------------------------------------------------------
CREATE TABLE auditoria (
    id_auditoria  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    -- Opcional: un login con correo inexistente no tiene usuario.
    id_usuario    INT          REFERENCES usuarios (id_usuario),
    accion        VARCHAR(100) NOT NULL,
    entidad       VARCHAR(50)  NOT NULL,
    -- Sin clave foránea a propósito: apunta a distintas tablas según "entidad".
    id_registro   INT,
    resultado     VARCHAR(40)  NOT NULL,
    fecha_hora    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    -- Solo información NO sensible (nunca contraseñas ni tokens).
    detalle       TEXT,

    CONSTRAINT auditoria_resultado_valido CHECK (resultado IN ('EXITO', 'RECHAZADO', 'ERROR'))
);

CREATE INDEX idx_auditoria_fecha  ON auditoria (fecha_hora);
CREATE INDEX idx_auditoria_accion ON auditoria (accion, fecha_hora);

-- ---------------------------------------------------------------------
-- 5. EXTENSIÓN OPCIONAL (RF-12, idempotencia): descomentar solo si se
--    implementa. No forma parte del esquema base.
-- ---------------------------------------------------------------------
-- CREATE TABLE solicitudes_despacho (
--     clave_solicitud  UUID PRIMARY KEY,
--     huella_carga     VARCHAR(64) NOT NULL,
--     resultado        VARCHAR(40) NOT NULL,
--     id_despacho      INT REFERENCES despachos (id_despacho),
--     fecha_hora       TIMESTAMPTZ NOT NULL DEFAULT now()
-- );
