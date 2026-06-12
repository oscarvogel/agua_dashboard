# Validacion gerencial de indicadores

Esta checklist sirve para comparar el dashboard contra reportes actuales de la cooperativa antes de darlo por cerrado.

## Datos de la corrida

- Fecha de validacion:
- Responsable cooperativa:
- Responsable tecnico:
- Log de sincronizacion usado:
- Periodo validado:
- Zona validada:
- Estado validado:

## Indicadores a comparar

| Indicador | Fuente dashboard | Reporte actual | Diferencia | Aprobado |
| --- | ---: | ---: | ---: | --- |
| Facturacion del periodo | | | | |
| Cobranzas del periodo | | | | |
| Deuda total | | | | |
| Deuda vencida | | | | |
| Pendiente de facturacion | | | | |
| Consumo ultimo periodo | | | | |
| Conexiones activas | | | | |
| Clientes activos | | | | |
| Conexiones sin lectura reciente | | | | |

## Detalles a revisar

| Detalle | Criterio | Aprobado |
| --- | --- | --- |
| Cobranzas | Deben salir de `movcaja`, no de `cabfact.fechapag`. | |
| Fechas invalidas | `0000-00-00` y futuras no razonables deben ignorarse o normalizarse. | |
| Deuda | Confirmar interpretacion de `ctacte.Monto` con signos debe/haber. | |
| Vencida | Confirmar regla de `cabfact.fechaven < fecha actual` y deuda neta positiva. | |
| Pendientes | Confirmar que `pendfact.facturado = 0` representa pendiente real. | |
| Lecturas recientes | Confirmar umbral operativo de 90 dias. | |

## Resultado

- Aprobado para uso gerencial:
- Ajustes requeridos:
- Observaciones:
