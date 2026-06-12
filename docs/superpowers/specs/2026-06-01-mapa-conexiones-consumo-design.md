# Mapa de conexiones por consumo

## Objetivo

Agregar una primera visualizacion geografica al dashboard usando `conexiones.ubicacion` y la relacion `consumo.idconexion` -> `conexiones.idconexion`. La primera entrega vive dentro de la vista `Consumos`, pero el contrato de datos debe quedar preparado para evolucionar a una seccion `Mapa` con capas de consumo, deuda, cobranzas y estado del padron.

## Alcance inicial

- Mostrar conexiones con coordenadas validas en un mapa interactivo.
- Usar el ultimo consumo conocido por conexion, respetando los filtros actuales de zona y estado.
- Colorear cada punto por estado operativo:
  - `zero`: ultimo consumo igual a cero.
  - `stale`: sin lectura reciente segun la regla actual de 90 dias.
  - `jump`: salto anormal detectado por la logica existente.
  - `normal`: lectura vigente sin alerta.
- Mostrar en popup: conexion, cliente, direccion, zona, periodo, consumo y fecha de toma.
- Informar resumen de cobertura: conexiones mapeadas, sin ubicacion y con coordenadas invalidas.

## Arquitectura

El backend extiende el payload existente de `/api/dashboard/summary/` con una nueva clave `maps`. La estructura inicial sera:

```json
{
  "maps": {
    "connections": {
      "summary": {
        "mapped": 0,
        "missing_location": 0,
        "invalid_location": 0
      },
      "points": []
    }
  }
}
```

Cada punto incluira `idconexion`, `idcliente`, `cliente`, `direccion`, `zona`, `lat`, `lng`, `ultimo_periodo`, `ultimo_consumo`, `ultima_fecha_toma` y `status`. Esta forma permite sumar mas capas sin romper el frontend: `maps.debt`, `maps.collections` o `maps.layers` pueden agregarse luego.

## Datos

`conexiones.ubicacion` se interpreta como texto `lat, lon`, por ejemplo `-26.854263, -54.885124`. El parseo acepta espacios y descarta valores fuera de rango geografico. Las conexiones sin ubicacion o con ubicacion invalida no se renderizan como puntos, pero se cuentan en el resumen.

Para cada conexion se toma su ultimo registro de consumo ordenado por periodo y fecha de toma. La clasificacion prioriza alertas operativas: `jump`, luego `stale`, luego `zero`, luego `normal`.

## Frontend

La vista `Consumos` incorporara un panel de mapa encima del listado mensual. Se usara Leaflet con tiles publicos de OpenStreetMap. El componente recibira `dashboard.maps.connections` y sera independiente para poder reutilizarse en una futura vista `Mapa`.

El mapa centrara automaticamente el encuadre sobre los puntos disponibles. Si no hay puntos, mostrara un estado vacio con el conteo de conexiones sin ubicacion.

## Errores y estados vacios

Si el backend no puede parsear una ubicacion, no falla el dashboard completo: omite ese punto y aumenta `invalid_location`. Si no hay coordenadas validas, la pantalla conserva el resto de los indicadores de consumo.

## Verificacion

- Tests unitarios backend para parseo de coordenadas y clasificacion de puntos.
- Build frontend con `npm run build`.
- Smoke manual o navegador local para confirmar que el mapa se renderiza, centra los puntos y muestra popups.
