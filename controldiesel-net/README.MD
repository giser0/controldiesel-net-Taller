# ControlDiesel-Net

Sistema web para la gestión de despachos de diésel, control de cupos y generación de alertas para revisión.

**Proyecto:** Taller de Proyectos · Carrera de Informática · Universidad Mayor de San Andrés (UMSA)
**Estudiante:** Sergio Wilder Huaylliri Nina · **Mención:** Desarrollo de Software
**Plazo:** cuatro semanas · **La Paz, Bolivia · 2026**

> **Nota de rigor:** es un prototipo académico con **datos ficticios**. Las alertas no prueban fraude ni infracción: son señales para revisión humana. No sustituye ni se integra con plataformas oficiales (YPFB, ANH, etc.).

---

## 📌 Requisitos previos y versiones

| Herramienta | Versión usada | Requerida |
| --- | --- | --- |
| Python | 3.13.2 | 3.11+ |
| Node.js | v24.14.0 | 18+ |
| PostgreSQL | 18.4 | 14+ |
| Git | 2.49.0 | cualquiera reciente |

---

## 🎯 Alcance

Cinco módulos funcionales, con funciones mínimas:

| # | Módulo | Funciones mínimas |
| --- | --- | --- |
| 1 | Administración y acceso | Login, tres roles fijos, usuarios, estaciones y vehículos (baja lógica). |
| 2 | Cupos y despachos | Asignar/consultar cupos, validar vigencia y saldo, registrar despacho. **Módulo prioritario.** |
| 3 | Detección de eventos | Motor de reglas RD-01 y RD-02, invocado dentro de la transacción del despacho. |
| 4 | Alertas y seguimiento | Listar, filtrar, observar, revisar y cerrar alertas. |
| 5 | Auditoría y reportes | Historial de operaciones y consultas por fecha, vehículo y estación. |

**Fuera de alcance:** integraciones externas (YPFB, ANH, B-SISA), IA/ML, aplicación móvil, notificaciones (correo, SMS, WhatsApp), dashboards y analítica avanzada, anulación de despachos confirmados.

---

## 👥 Roles y permisos

Los permisos se aplican **en el backend**; ocultar botones en la interfaz no es un control suficiente.

| Rol | Puede | No puede |
| --- | --- | --- |
| **Administrador** | Gestionar usuarios, estaciones, vehículos y cupos; consultar despachos, alertas, auditoría y reportes. | Borrar físicamente despachos confirmados. |
| **Operador** | Registrar despachos y consultar vehículos, saldo de cupos y despachos de **su** estación. | Despachar en otra estación; administrar usuarios o reglas. |
| **Regulador** | Consultar despachos, alertas y reportes; observar y cerrar alertas. | Administrar usuarios, estaciones, vehículos ni cupos; ver la auditoría técnica. |

La estación del Operador se toma de su asignación en la base de datos, **nunca** de lo que envíe el navegador.

---

## ✅ ¿Qué es un despacho válido y uno rechazado?

**Despacho válido (CONFIRMADO).** Se confirma solo si, dentro de una única transacción:

1. el usuario está autenticado y tiene permiso (Operador con estación asignada);
2. los litros solicitados son mayores que cero;
3. el vehículo tiene un cupo **VIGENTE** (periodo inclusivo en ambos extremos);
4. los litros no superan el saldo disponible del cupo.

Entonces se registra el despacho, se descuenta el saldo **exactamente una vez**, se guarda la auditoría y se evalúan RD-01 y RD-02. Si falla cualquier escritura obligatoria, se revierte todo.

**Despacho rechazado.** No se guarda como despacho ni descuenta saldo. Si el motivo es saldo insuficiente (RD-03), el intento queda en la auditoría con la acción `DESPACHO_RECHAZADO`. Los rechazos no cuentan como consumo.

---

## 🧭 Requisitos funcionales (resumen)

| Código | Requisito |
| --- | --- |
| RF-01 | Iniciar sesión con credenciales válidas; rechazar las incorrectas. |
| RF-02 | El Administrador gestiona usuarios (crear, consultar, modificar, desactivar), asigna rol y estación al Operador. |
| RF-03 | El Administrador gestiona estaciones y vehículos; códigos de estación y placas únicos. |
| RF-04 | El Administrador asigna y consulta cupos por vehículo, litros y periodo. |
| RF-05 | Mostrar litros asignados, consumidos y disponibles de un cupo; el Operador puede consultar el saldo antes de despachar. |
| RF-06 | Rechazar cantidades ≤ 0, cupos no vigentes y solicitudes superiores al saldo. |
| RF-07 | Despacho y descuento de saldo se confirman como una única transacción. |
| RF-08 | Registrar el resultado de la operación y la auditoría mínima; los rechazos (incluido RD-03) se registran en auditoría. |
| RF-09 | Evaluar RD-01 y RD-02 tras un despacho confirmado y crear o actualizar alertas. |
| RF-10 | El Regulador consulta, observa, revisa y cierra alertas; cada cambio conserva usuario, fecha y observación. |
| RF-11 | Historial y reportes por fecha, vehículo y estación; solo los despachos confirmados cuentan como consumo. |
| RF-12 | *(Extensión, prioridad media)* Idempotencia: misma clave y misma carga no generan un segundo descuento; misma clave con carga distinta devuelve 409. |

## 📏 Reglas de negocio

| Código | Regla |
| --- | --- |
| RN-01 | Solo usuarios autenticados acceden a rutas protegidas. |
| RN-02 | Cada rol tiene permisos definidos y aplicados en el backend. |
| RN-03 | El Operador solo registra despachos de su estación asignada. |
| RN-04 | Los litros solicitados deben ser mayores que cero. |
| RN-05 | Un despacho se confirma solo si el cupo está vigente y el saldo es suficiente. |
| RN-06 | Despacho y descuento de saldo se confirman o revierten juntos. |
| RN-07 | Los periodos de vigencia son inclusivos; no hay cupos PENDIENTES o VIGENTES superpuestos para un mismo vehículo. |
| RN-08 | Las alertas son señales para revisión humana, no determinan una infracción. |
| RN-09 | Toda revisión o cierre de alerta registra usuario, fecha, estado y observación. |
| RN-10 | No existe anulación ni reversión de despachos confirmados en esta versión. |

## 🚨 Reglas de detección y validación

| Código | Condición | Acción |
| --- | --- | --- |
| **RD-01** Estaciones distintas | Al confirmar un despacho en *t*, el mismo vehículo tiene otro despacho confirmado en una estación distinta dentro de `[t−12 h, t]` (extremos incluidos). | Crea o actualiza una alerta abierta con los despachos que la sustentan. **No bloquea.** |
| **RD-02** Frecuencia | Al confirmar un despacho en *t*, el vehículo acumula 4 o más despachos confirmados dentro de `[t−24 h, t]` (extremos incluidos). | Crea o actualiza una alerta abierta. **No bloquea.** |
| **RD-03** Saldo insuficiente | Los litros solicitados superan el saldo disponible durante la validación transaccional. | **Rechaza** sin despacho ni descuento; intenta registrar el rechazo en auditoría. **No genera alerta.** |

Una alerta abierta (PENDIENTE o EN_REVISION) por combinación de vehículo y tipo: si la regla vuelve a cumplirse, se actualiza esa alerta y no se crea una duplicada.

**Estados:** cupos `PENDIENTE · VIGENTE · VENCIDO` · despachos `CONFIRMADO` · alertas `PENDIENTE → EN_REVISION → CERRADA` (al cerrar: `JUSTIFICADA` o `REQUIERE_SEGUIMIENTO`).

---

## 🏗️ Arquitectura y tecnologías

| Capa | Tecnología | Responsabilidad |
| --- | --- | --- |
| Presentación | React + TypeScript (Vite) | Formularios, tablas, navegación, consulta de alertas. |
| API y lógica | Python + FastAPI | Autenticación, permisos, validaciones, reglas, transacciones. |
| Persistencia | PostgreSQL | Entidades, restricciones, índices, transacciones, auditoría. |
| Pruebas y control | pytest + cliente HTTP, Git | Pruebas reproducibles y control de versiones. |

### Estructura del repositorio

```
controldiesel-net/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/          # rutas
│   │   ├── schemas/      # modelos Pydantic
│   │   ├── services/     # lógica de negocio y reglas
│   │   ├── models/       # modelos de base de datos
│   │   └── core/         # configuración y seguridad
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/ (pages, components, services, types, routes)
├── db/
│   ├── 01_schema.sql     # tablas, claves y restricciones
│   └── 02_seed.sql       # datos ficticios de demostración
├── docs/                 # propuesta, DER, casos de uso, diccionario de datos, matriz de pruebas
└── README.md
```

### Decisiones de diseño

- **Autorización siempre en el servidor.** La interfaz solo muestra u oculta; el backend decide.
- **Concurrencia:** el despacho bloquea la fila del cupo (`SELECT ... FOR UPDATE`) y vuelve a comprobar vigencia y saldo dentro de la transacción, para evitar sobregiros por solicitudes simultáneas.
- **Alertas en la misma transacción del despacho:** todo despacho confirmado conserva la evidencia de su revisión; el costo es que un fallo al escribir la alerta revierte el despacho.
- **Integridad en la base de datos:** `CHECK`, `UNIQUE`, claves foráneas y una restricción `EXCLUDE` (con `btree_gist`) impiden cupos superpuestos aunque falle el código.
- **Fechas:** todo se almacena en **UTC** (`TIMESTAMPTZ`) y se convierte a hora de La Paz solo para mostrar. Las ventanas de 12 h y 24 h son móviles e inclusivas en sus extremos.

---

## 🚀 Instalación y ejecución

> Los comandos están escritos para **Windows (PowerShell)**. En Linux/macOS cambia solo la activación del entorno virtual (`source .venv/bin/activate`).

### 1. Clonar el repositorio

```powershell
git clone <URL-DEL-REPOSITORIO> controldiesel-net
cd controldiesel-net
```

### 2. Crear la base de datos

```powershell
psql -U postgres
```

```sql
CREATE USER controldiesel WITH PASSWORD 'cambia_esta_clave';
CREATE DATABASE controldiesel OWNER controldiesel;
\q
```

Cargar esquema y datos ficticios:

```powershell
psql -U controldiesel -d controldiesel -f db/01_schema.sql
psql -U controldiesel -d controldiesel -f db/02_seed.sql
```

> La extensión `btree_gist` requiere un superusuario la primera vez: `psql -U postgres -d controldiesel -c "CREATE EXTENSION IF NOT EXISTS btree_gist;"`.

### 3. Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # luego edita .env con tus valores
uvicorn app.main:app --reload
```

- API: <http://127.0.0.1:8000> · Documentación interactiva: <http://127.0.0.1:8000/docs>
- Verificación: `GET /health` debe responder correctamente y confirmar la conexión a PostgreSQL.

### 4. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Interfaz: <http://localhost:5173>

### Variables de entorno

Se configuran en `backend/.env` (nunca se sube a Git; el repositorio solo incluye `.env.example` sin secretos reales).

| Variable | Descripción |
| --- | --- |
| `DATABASE_URL` | Cadena de conexión, p. ej. `postgresql+psycopg://controldiesel:CLAVE@localhost:5432/controldiesel` |
| `SECRET_KEY` | Clave para firmar los tokens JWT (cadena larga y aleatoria). |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Vigencia del token (por ejemplo, `60`). |
| `CORS_ORIGINS` | Orígenes permitidos (por ejemplo, `http://localhost:5173`). |

### Usuarios de demostración

Los usuarios y contraseñas ficticios se definen en `db/02_seed.sql` (un Administrador, un Regulador y dos Operadores, cada uno con su estación). *Completar esta tabla cuando exista el script.*

---

## 🧪 Pruebas

```powershell
cd backend
pytest -v
```

Cada caso de prueba (P01–P20) registra: identificador, precondiciones y datos, pasos, resultado esperado, **resultado observado**, estado (Aprobada / Fallida / Bloqueada), fecha y evidencia breve. Los resultados observados se completan **después** de ejecutar; no se anticipan aprobaciones. La matriz completa vive en `docs/`.

Núcleo: P01–P15 y P18–P20 (18 casos). Extensión de idempotencia (RF-12): P16 y P17.

---

## 📅 Cronograma (cuatro semanas)

| Semana | Foco | Criterio de salida |
| --- | --- | --- |
| **1. Análisis y base** | Requisitos, repositorio, modelo ER, base y datos semilla, API base, login, esqueleto de React. | Proyecto ejecutable desde estas instrucciones; endpoints base y login. |
| **2. Flujo crítico** | Roles y estación del Operador, cupos, despacho transaccional, RD-03, auditoría, pruebas de saldo, rollback y concurrencia. | **HITO OBLIGATORIO:** un despacho válido descuenta una sola vez; uno inválido no modifica saldo; permisos en backend; la prueba concurrente no genera sobregiro. |
| **3. Alertas e interfaz** | RD-01 y RD-02, pantallas de alertas, historial y reportes sencillos; idempotencia si el flujo base es estable. | Flujo de punta a punta: login → despacho → saldo → alerta → historial. |
| **4. Pruebas y entrega** | Completar la matriz de pruebas, corregir defectos, manual, limitaciones y demostración. | Versión reproducible, matriz con resultados observados, manual breve y demo. |

**Orden de recorte si hay retraso:** (1) idempotencia RF-12 y casos P16–P17; (2) interfaz de administración de usuarios, estaciones y vehículos; (3) filtros secundarios y reportes extra; (4) dashboard y refinamientos visuales.
**No se sacrifica:** autenticación y permisos, cupos, despacho transaccional, validación de saldo y vigencia, RD-01/02/03, auditoría mínima y las pruebas críticas (P02, P03, P05, P06, P08, P09, P18).

### Estado actual

- [ ] Semana 1: base y API
- [ ] Semana 2: flujo crítico
- [ ] Semana 3: alertas e interfaz
- [ ] Semana 4: pruebas y entrega

---

## ⚠️ Limitaciones

- Los resultados dependen de datos simulados y reglas predefinidas.
- RD-01 y RD-02 solo identifican patrones para revisión; RD-03 rechaza por saldo insuficiente.
- No garantiza disponibilidad de nivel productivo ni inmutabilidad absoluta de la auditoría.
- Sin anulación de despachos ni integraciones externas.

## 📄 Documentación

La propuesta completa, el diagrama entidad-relación, el diagrama de casos de uso, el diccionario de datos y la matriz de pruebas están en la carpeta [`docs/`](docs/).