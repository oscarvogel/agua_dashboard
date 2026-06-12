# Dashboard ejecutivo cooperativa - plan inicial

## Objetivo

Construir primero un dashboard ejecutivo/gerencial para la cooperativa, separado de la web app de campo/catastro.

El dashboard debe mostrar indicadores utiles para gerencia y direccion a partir de la base operativa actual de la cooperativa, sin modificar esa base y sin depender de que el dashboard consulte directamente la computadora interna.

## Alcance de este plan

Este plan cubre solo:

- inspeccion de la base operativa actual;
- seleccion de datos relevantes para gestion;
- modulo de sincronizacion que vive dentro de la cooperativa;
- copia de datos hacia el VPS;
- dashboard ejecutivo de solo lectura sobre la copia del VPS.

Queda fuera de este plan:

- app de campo para ubicacion de medidores;
- carga de infraestructura, cañerias, tanques y observaciones;
- PWA de catastro;
- edicion de datos operativos desde el dashboard.

La app de campo/catastro sigue como proyecto separado.

## Arquitectura propuesta

### 1. Base operativa de la cooperativa

Es la fuente primaria de datos.

Datos detectados en la inspeccion:

- Base: `agua`
- Tablas/vistas: 42
- Tablas principales:
  - `clientes`
  - `conexiones`
  - `consumo`
  - `cabfact`
  - `detfact`
  - `ctacte`
  - `movcaja`
  - `pendfact`
  - `conceptos`
  - `tablas`

Regla: esta base no debe ser modificada por el dashboard.

### 2. Modulo de sincronizacion en la cooperativa

Proceso local instalado en una computadora/servidor dentro de la cooperativa.

Responsabilidades:

- conectarse a la base operativa local con usuario de solo lectura;
- extraer solo las tablas/campos necesarios para gestion;
- normalizar fechas invalidas como `0000-00-00`;
- enviar los datos al VPS;
- registrar logs de cada corrida;
- alertar si falla la sincronizacion.

Este modulo es el unico componente que necesita permiso de escritura sobre la base destino del VPS.

### 3. VPS

El VPS recibe una copia de datos seleccionados.

La copia del VPS debe ser tratada como fuente de solo lectura para el dashboard.

Usuarios sugeridos:

- `sync_writer`: usado solo por el sincronizador, con permisos para crear/actualizar tablas de staging/reporting.
- `dashboard_reader`: usado por Django/dashboard, con permisos solo `SELECT`.

### 4. Backend dashboard

Backend Django + Django REST Framework.

Responsabilidades:

- autenticacion de usuarios;
- endpoints de indicadores;
- consultas agregadas sobre la copia del VPS;
- control de permisos;
- panel administrativo basico para usuarios y configuracion.

### 5. Frontend dashboard

Frontend Vue.

Responsabilidades:

- dashboard ejecutivo;
- filtros por periodo, zona, estado y tipo de indicador;
- graficos;
- tablas resumidas;
- mapas solo cuando aporten valor gerencial;
- exportaciones.

## Flujo de datos

1. La base operativa de la cooperativa sigue funcionando como hasta ahora.
2. El sincronizador local lee datos con usuario de solo lectura.
3. El sincronizador actualiza una copia en el VPS.
4. Django/DRF consulta la copia del VPS con usuario de solo lectura.
5. Vue muestra indicadores ejecutivos.
6. El dashboard nunca escribe en la base operativa.

## Datos a sincronizar en primera etapa

Primera seleccion sugerida:

- `clientes`
- `conexiones`
- `consumo`
- `cabfact`
- `detfact`
- `ctacte`
- `movcaja`
- `pendfact`
- `conceptos`
- `tablas`
- vistas utiles si son estables: `facturas`, `zonas`

No conviene sincronizar todo al principio si no aporta al dashboard.

## Indicadores ejecutivos propuestos

### Resumen general

- conexiones activas;
- clientes activos;
- facturacion del mes;
- cobranzas del mes;
- deuda total estimada;
- deuda vencida;
- consumos del ultimo periodo;
- conexiones sin lectura reciente;
- pendientes de facturacion.

### Facturacion

Tablas base:

- `cabfact`
- `detfact`
- `conceptos`

Indicadores:

- facturacion mensual;
- facturacion por concepto;
- emitido vs pagado;
- facturas vencidas;
- importe promedio por conexion;
- evolucion intermensual.

### Cobranzas y caja

Tablas base:

- `movcaja`
- `ctacte`
- `cabfact`

Indicadores:

- cobranzas por dia/mes;
- pagos aplicados;
- comprobantes anulados o en estado dudoso;
- conciliacion basica entre caja, facturas y cuenta corriente;
- clientes con pagos recientes.

### Deuda y cuenta corriente

Tablas base:

- `ctacte`
- `cabfact`
- `clientes`
- `conexiones`

Indicadores:

- deuda total;
- deuda vencida;
- deuda por antiguedad;
- top deudores;
- deuda por zona;
- conexiones con deuda recurrente.

### Consumos

Tablas base:

- `consumo`
- `conexiones`
- `clientes`

Indicadores:

- consumo por periodo;
- consumo promedio por conexion;
- conexiones con consumo cero;
- saltos anormales de consumo;
- conexiones sin consumo registrado;
- consumo por zona.

### Padron y conexiones

Tablas base:

- `clientes`
- `conexiones`
- `tablas`

Indicadores:

- conexiones activas/inactivas;
- clientes activos/inactivos;
- distribucion por zona;
- conexiones sin ubicacion;
- conexiones con datos incompletos;
- altas por periodo si `fechaingreso` es confiable.

### Pendientes operativos

Tablas base:

- `pendfact`

Indicadores:

- pendientes de facturacion;
- pendientes por concepto;
- pendientes por periodo;
- monto pendiente;
- conexiones/clientes con pendientes repetidos.

## Reglas de calidad de datos

Durante sincronizacion y consultas se deben normalizar o filtrar:

- fechas `0000-00-00`;
- fechas futuras no razonables como `2089-01-02` o `2103-06-06`;
- importes nulos;
- conexiones sin cliente;
- clientes inactivos si el indicador pide solo activos;
- coordenadas vacias o invalidas;
- registros duplicados si aparecen en vistas o joins.

Las reglas deben documentarse porque afectan la lectura gerencial.

## Frecuencia de sincronizacion

Primera version recomendada:

- sincronizacion cada 30 o 60 minutos durante horario laboral;
- una corrida manual bajo demanda;
- log de inicio, fin, tablas procesadas, filas enviadas y errores.

No hace falta tiempo real para un dashboard ejecutivo inicial.

## Seguridad

- La base operativa de la cooperativa debe tener usuario de solo lectura para el sincronizador.
- El VPS debe tener usuario de escritura solo para el sincronizador.
- El dashboard debe usar usuario `SELECT` solamente.
- No guardar claves en codigo fuente.
- Usar archivos `.env` fuera del repositorio o excluidos por `.gitignore`.
- Publicar dashboard con HTTPS.
- Dashboard con usuario y contrasena.
- Registrar ultimo login y acciones administrativas.

## Archivos de configuracion previstos

En la cooperativa:

```env
# .env.coop
COOP_MYSQL_HOST=
COOP_MYSQL_PORT=3306
COOP_MYSQL_DATABASE=agua
COOP_MYSQL_USER=
COOP_MYSQL_PASSWORD=
COOP_MYSQL_SSL_MODE=preferred
```

Para el destino VPS:

```env
# .env.vps
VPS_MYSQL_HOST=
VPS_MYSQL_PORT=3306
VPS_MYSQL_DATABASE=agua_dashboard
VPS_MYSQL_USER=
VPS_MYSQL_PASSWORD=
VPS_MYSQL_SSL_MODE=preferred
```

## Etapas de trabajo

### Etapa 1 - Validar modelo de datos

- Revisar columnas de tablas principales.
- Confirmar significado de `estado`, `periodo`, `facturado`, `activo`, `zona`.
- Identificar formulas para deuda, pagado y pendiente.
- Confirmar si `ctacte.Monto` representa debe/haber con signo o requiere interpretacion por comprobante.
- Confirmar si `cabfact.fechapag` es confiable o si el pago real sale de `movcaja`/`ctacte`.

### Etapa 2 - Definir dataset ejecutivo

- Elegir tablas a sincronizar.
- Elegir columnas necesarias.
- Definir reglas de limpieza.
- Definir nombres de tablas espejo en VPS.
- Definir indices para consultas del dashboard.

### Etapa 3 - Construir sincronizador local

- Script Python de lectura desde la base cooperativa.
- Escritura hacia VPS.
- Modo dry-run.
- Modo sync real.
- Logs.
- Control de errores.
- Ejecucion programada.

### Etapa 4 - Backend dashboard

- Django + DRF.
- Conexion al VPS con usuario solo lectura.
- Endpoints agregados.
- Autenticacion.
- Tests de consultas.

### Etapa 5 - Frontend Vue

- Pantalla de login.
- Dashboard ejecutivo.
- Filtros de periodo/zona.
- Graficos principales.
- Tablas de detalle.
- Exportacion.

### Etapa 6 - Verificacion con gerencia

- Comparar indicadores contra reportes actuales.
- Validar definiciones de deuda, facturacion y cobranzas.
- Ajustar filtros.
- Dejar documentadas las reglas.

## Primer entregable recomendado

Un dashboard ejecutivo minimo con:

- facturacion mensual;
- cobranzas mensuales;
- deuda total y vencida;
- top deudores;
- consumos del ultimo periodo;
- conexiones sin lectura;
- conexiones activas/inactivas;
- pendientes de facturacion.

Este entregable valida el valor gerencial sin mezclarlo con la app de campo.

## Pendientes antes de implementar

- Confirmar estructura exacta del VPS destino.
- Crear `.env.vps`.
- Definir nombre de base destino: sugerido `agua_dashboard`.
- Confirmar si el sincronizador correra en `notebook-oscar` o en una PC/servidor de la cooperativa.
- Confirmar si el dashboard se publicara en `agua.vogelconsultoria.com.ar` o en otro subdominio.
- Definir usuarios iniciales del dashboard.
