# Mejora premium - Seguimiento de cobranzas

Fecha: 2026-05-30

Objetivo para el lunes: transformar la seccion de cobranzas en una herramienta de seguimiento gerencial, no solo en un listado de importes. La pantalla debe ayudar a detectar si la cooperativa esta cobrando bien, donde esta floja, que socios requieren seguimiento y como evoluciona la recuperacion periodo a periodo.

## Diagnostico actual

Hoy ya existe:

- cobranza mensual desde `movcaja`;
- detalle diario de cobranzas;
- detalle de un dia por socio, con comprobantes;
- top deudores;
- deuda por antiguedad y zona;
- pagos recientes;
- filtros por periodo, zona y estado.

Lo que falta para seguimiento real:

- ver objetivo vs avance;
- distinguir recuperacion de deuda vieja vs pagos corrientes;
- priorizar socios accionables;
- mostrar tendencias visuales mas claras;
- entender zonas flojas;
- tener una pantalla que gerencia pueda mirar todos los dias y decidir a quien llamar o revisar.

## Enfoque recomendado

Hacer una nueva vista principal dentro de `Cobranzas`, con estetica mas premium pero operativa:

1. tablero de salud de cobranzas;
2. graficos de tendencia y cumplimiento;
3. embudo/listado de seguimiento por socio;
4. drill-down por zona, dia y antiguedad;
5. alertas accionables.

No conviene arrancar por decoracion. Primero hay que definir indicadores que realmente muevan gestion.

## Propuesta visual

### Encabezado premium

Arriba de `Cobranzas`:

- KPI grande: `Cobrado periodo`.
- KPI comparativo: `vs periodo anterior`.
- KPI: `Cobrado ultimos 7 dias`.
- KPI: `Socios que pagaron`.
- KPI critico: `Deuda vencida pendiente`.
- Badge de estado: `Ritmo bajo`, `Ritmo normal`, `Buen ritmo`.

Formato sugerido:

- fondo claro;
- tarjetas compactas;
- un acento verde/teal para cobros;
- ambar para atraso;
- rojo solo para riesgo real;
- nada de graficos decorativos sin lectura concreta.

### Grafico principal

Un grafico combinado:

- barras: cobrado por dia;
- linea: acumulado del mes;
- linea punteada: objetivo esperado o promedio historico.

Sirve para responder:

- vamos bien o atrasados respecto al ritmo del mes;
- que dias hubo caida de caja;
- si el cobro esta concentrado en pocos dias.

### Heatmap semanal

Matriz simple:

- filas: semanas;
- columnas: lunes a viernes/sabado;
- color: intensidad de cobranza.

Sirve para detectar dias flojos recurrentes y patrones de caja.

### Ranking accionable de socios

Tabla premium, no solo top deudores:

Columnas:

- socio;
- zona;
- deuda total;
- deuda vencida;
- ultimo pago;
- dias sin pagar;
- cantidad de facturas/deudas;
- riesgo;
- accion sugerida.

Acciones sugeridas iniciales:

- `Llamar`: deuda alta y sin pago reciente.
- `Revisar`: movimiento raro o estado dudoso.
- `Seguimiento normal`: pago reciente pero deuda pendiente.
- `Sin accion`: al dia o baja prioridad.

## Indicadores nuevos propuestos

### 1. Tasa de recuperacion

Formula inicial:

```text
cobranzas_periodo / deuda_vencida_inicio_periodo
```

Si no tenemos snapshot de deuda al inicio, usar version MVP:

```text
cobranzas_periodo / deuda_vencida_actual
```

Nota: documentar que la version MVP es aproximada.

### 2. Ritmo de cobranza

Formula:

```text
cobrado_acumulado_mes / dias_habiles_transcurridos
```

Comparar contra:

- promedio diario del mes anterior;
- promedio diario de ultimos 3 meses;
- objetivo manual si gerencia lo define.

### 3. Socios recuperados

Socios con deuda que tuvieron pago en los ultimos 30 dias.

Ya existe parcialmente como `clientes_con_pagos_recientes`, pero hay que cruzarlo con deuda para saber si recupero o solo hizo un pago chico.

### 4. Socios criticos sin contacto

Socios con:

- deuda vencida;
- sin pago reciente;
- monto alto;
- varias facturas pendientes.

Inicialmente no tendremos registro de contacto, pero podemos llamar el indicador:

```text
Socios criticos sin pago reciente
```

### 5. Cobranzas por zona con eficiencia

No alcanza ver monto por zona. Hay que cruzar:

- deuda vencida por zona;
- cobrado por zona;
- cantidad de socios con pago;
- porcentaje estimado de recuperacion.

Esto permite ver si una zona tiene deuda alta y poca cobranza.

### 6. Concentracion de cobranza

Medir si pocos socios explican gran parte de la cobranza:

```text
top 10 socios cobrados / cobranza total
```

Si es muy alto, la cobranza depende de pocos pagos grandes.

### 7. Promesa operativa del dashboard

Una frase interna para guiar UX:

```text
En menos de 30 segundos gerencia debe saber si la cobranza viene bien, donde esta floja y que socios revisar primero.
```

## Pantallas a construir

### Vista 1 - Cobranzas premium

Ruta sugerida:

```text
#collections
```

Reemplaza/mejora la pantalla mensual actual.

Secciones:

1. KPIs de salud.
2. Grafico cobrado diario + acumulado.
3. Cobranzas por zona.
4. Ranking accionable.
5. Alertas de seguimiento.

### Vista 2 - Mes de cobranzas

Ruta actual:

```text
#collections-day
```

Mejoras:

- mantener listado diario;
- agregar mini grafico del mes arriba;
- destacar dias por encima/debajo del promedio;
- al tocar un dia abre detalle por socio.

### Vista 3 - Dia por socio

Ruta actual:

```text
#collections-member
```

Mejoras:

- ordenar por importe descendente;
- agregar total del dia;
- agregar buscador por socio;
- mostrar cantidad de comprobantes;
- marcar pagos chicos vs deuda grande cuando tengamos deuda del socio.

### Vista 4 - Seguimiento de socios

Nueva vista opcional:

```text
#collections-followup
```

Tabla pensada para gestion diaria:

- socios priorizados;
- deuda;
- ultimo pago;
- riesgo;
- zona;
- accion sugerida.

Esta vista es la que mas valor operativo puede dar.

## Datos necesarios

Ya disponibles:

- `movcaja`: fecha, importe, idCliente, comprobante, estado.
- `clientes`: socio, zona, activo.
- `cabfact`: facturacion y vencimiento.
- `ctacte`: deuda.
- `conexiones`: zona/conexion.

Datos deseables para version 2:

- registro de llamadas o gestion de cobranza;
- responsable asignado;
- estado de seguimiento;
- promesa de pago;
- fecha de proximo contacto.

Esto ultimo podria ser una tabla propia del dashboard, sin tocar la base operativa.

## Backend - cambios sugeridos

En `backend/dashboard_api/metrics.py`:

- agregar `collections_health`;
- agregar `collections_daily_performance`;
- agregar `collections_by_zone_efficiency`;
- agregar `collections_followup`;
- agregar `collections_concentration`.

Estructura esperada:

```json
{
  "collections": {
    "health": {
      "period_collected": 0,
      "previous_period_collected": 0,
      "variation_pct": 0,
      "last_7_days": 0,
      "paying_clients": 0,
      "estimated_recovery_rate": 0,
      "status": "low|normal|good"
    },
    "daily_performance": [],
    "zone_efficiency": [],
    "followup": [],
    "concentration": {}
  }
}
```

Mantener compatibilidad con las claves actuales para no romper pantallas existentes.

## Frontend - cambios sugeridos

En `frontend/src/App.vue` conviene empezar a separar componentes, porque ya esta creciendo demasiado.

Componentes sugeridos:

- `CollectionsOverview.vue`
- `CollectionsTrendChart.vue`
- `CollectionsZonePanel.vue`
- `CollectionsFollowupTable.vue`
- `CollectionsDayDetail.vue`
- `CollectionsMemberDetail.vue`

Si no se quiere refactor completo el lunes, minimo extraer solo cobranzas.

## Graficos recomendados

Prioridad 1:

- barras diarias + linea acumulada;
- ranking horizontal de zonas;
- tabla accionable con chips de riesgo.

Prioridad 2:

- heatmap semanal;
- dona de concentracion;
- sparkline por socio/zona.

Libreria:

- usar una libreria liviana si ya entra bien en Vite, por ejemplo `recharts` no aplica por Vue; opciones Vue:
  - `vue-chartjs` + Chart.js;
  - `echarts` / `vue-echarts`.

Recomendacion: `echarts`, porque permite graficos mas premium y dashboards densos sin pelear tanto.

## UX premium sin perder utilidad

Reglas:

- no agrandar todo como landing page;
- mantener densidad de gestion;
- usar color para explicar riesgo, no para decorar;
- cada grafico debe responder una pregunta concreta;
- cada alerta debe tener una accion sugerida;
- mobile debe seguir siendo usable, pero el foco premium probablemente se luzca mas en desktop.

## Plan de implementacion para el lunes

### Paso 1 - Backend de indicadores de cobranza

- Crear tests en `backend/tests/test_dashboard_metrics.py`.
- Calcular:
  - cobrado periodo;
  - variacion vs periodo anterior;
  - cobrado ultimos 7 dias;
  - socios con pago;
  - deuda vencida por zona;
  - cobranza por zona;
  - ranking de socios criticos.
- Exponer bajo `payload.collections`.

### Paso 2 - Nueva UI de Cobranzas premium

- Reemplazar vista `#collections`.
- Mantener click a mes.
- Agregar KPIs superiores.
- Agregar grafico principal.
- Agregar panel de zonas.
- Agregar ranking accionable.

### Paso 3 - Mejorar dia y socio

- En `#collections-day`, agregar total del mes y promedio diario.
- En `#collections-member`, agregar total del dia y buscador.
- Mostrar comprobantes de forma mas prolija.

### Paso 4 - Verificacion

Ejecutar:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe backend\manage.py check
cd frontend
npm run build
```

Luego:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_dashboard.ps1 -ApiBase https://agua.vogelconsultoria.com.ar/api
```

Y probar en navegador:

- dashboard;
- cobranzas;
- mes;
- dia;
- detalle por socio;
- mobile;
- desktop.

## Riesgos y definiciones pendientes

1. Definir que significa "objetivo de cobranza".
   - opcion A: promedio historico;
   - opcion B: deuda vencida esperada;
   - opcion C: meta manual cargada en config.

2. Confirmar como interpretar deuda con `ctacte`.
   - ya se usa para deuda total;
   - para seguimiento fino conviene validar con gerencia.

3. Decidir si se agrega gestion manual.
   - sin gestion manual: solo analitica;
   - con gestion manual: registrar llamada, promesa de pago, responsable.

## Recomendacion

Para el lunes conviene implementar primero una version premium analitica, sin gestion manual:

1. Cobranzas premium con KPIs y graficos.
2. Ranking accionable de socios criticos.
3. Drill-down mejorado por dia/socio.

Despues, si gerencia lo usa, se agrega una tabla propia de seguimiento manual con llamadas, promesas y responsables. Eso ya seria un mini CRM de cobranzas, y conviene hacerlo cuando el criterio de trabajo este validado.

