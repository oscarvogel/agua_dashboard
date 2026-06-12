# Inspeccion base cooperativa

- Generado: 2026-05-29 15:39:57
- Base: `agua`
- Servidor: `8.0.36`
- Tablas/vistas: `42`

## Inventario

| Tabla | Tipo | Filas aprox. | MB | Columnas | Indices |
|---|---:|---:|---:|---:|---:|
| `accesos` | BASE TABLE | 4 | 0.02 | 4 | 1 |
| `afip` | BASE TABLE | 4 | 0.02 | 7 | 1 |
| `alicuota` | BASE TABLE | 7 | 0.02 | 2 | 1 |
| `articulos` | BASE TABLE | 8878 | 4.17 | 36 | 5 |
| `artprov` | BASE TABLE | 10397 | 3.53 | 17 | 6 |
| `cabfact` | BASE TABLE | 62331 | 10.55 | 16 | 3 |
| `clientes` | BASE TABLE | 476 | 0.23 | 23 | 4 |
| `comprobantes` | BASE TABLE | 3 | 0.02 | 2 | 1 |
| `conceptos` | BASE TABLE | 19 | 0.02 | 8 | 1 |
| `conexiones` | BASE TABLE | 606 | 0.14 | 10 | 3 |
| `consumo` | BASE TABLE | 61380 | 5.03 | 7 | 2 |
| `ctacte` | BASE TABLE | 25146 | 4.39 | 8 | 3 |
| `ctrocosto` | BASE TABLE | 0 | 0.02 | 2 | 1 |
| `detfact` | BASE TABLE | 198572 | 18.03 | 7 | 2 |
| `formula` | BASE TABLE | 44 | 0.02 | 9 | 1 |
| `gruform` | BASE TABLE | 0 | 0.02 | 2 | 1 |
| `movcaja` | BASE TABLE | 20157 | 3.83 | 21 | 2 |
| `paramfac` | BASE TABLE | 0 | 0.02 | 12 | 0 |
| `paramsist` | BASE TABLE | 8 | 0.02 | 3 | 1 |
| `pcabecera` | BASE TABLE | 0 | 0.05 | 29 | 3 |
| `pdetalle` | BASE TABLE | 0 | 0.06 | 8 | 4 |
| `pendfact` | BASE TABLE | 7680 | 1.95 | 10 | 4 |
| `periodicidad` | BASE TABLE | 7 | 0.02 | 2 | 1 |
| `provincias` | BASE TABLE | 24 | 0.02 | 2 | 1 |
| `rangom3` | BASE TABLE | 9 | 0.03 | 4 | 2 |
| `sistema` | BASE TABLE | 0 | 0.02 | 5 | 1 |
| `tablas` | BASE TABLE | 14 | 0.03 | 8 | 2 |
| `tip_comp` | BASE TABLE | 2 | 0.02 | 8 | 1 |
| `tipcompafip` | BASE TABLE | 0 | 0.02 | 2 | 1 |
| `tipoconsumo` | BASE TABLE | 2 | 0.02 | 2 | 1 |
| `tipofor` | BASE TABLE | 5 | 0.02 | 3 | 1 |
| `tipoiva` | BASE TABLE | 3 | 0.02 | 5 | 1 |
| `tiposervicio` | BASE TABLE | 4 | 0.02 | 2 | 1 |
| `tipotablas` | BASE TABLE | 3 | 0.02 | 5 | 1 |
| `titularinmueble` | BASE TABLE | 0 | 0.06 | 6 | 4 |
| `titularservicio` | BASE TABLE | 0 | 0.05 | 5 | 3 |
| `userlev` | BASE TABLE | 5 | 0.02 | 3 | 0 |
| `usuarios` | BASE TABLE | 0 | 0.02 | 12 | 1 |
| `factimp` | VIEW | 0 | 0.00 | 15 | 0 |
| `facturas` | VIEW | 0 | 0.00 | 16 | 0 |
| `tipdoc` | VIEW | 0 | 0.00 | 5 | 0 |
| `zonas` | VIEW | 0 | 0.00 | 5 | 0 |

## Tablas principales por volumen

- `detfact`: aprox. 198572 filas. Columnas: `idDetFact`, `idCabfact`, `idconcepto`, `neto`, `iva`, `dgr`, `detalle`
- `cabfact`: aprox. 62331 filas. Columnas: `IdCabFact`, `Tipo`, `Clase`, `numero`, `idcliente`, `idconexion`, `fechaem`, `fechaven`, `fechapag`, `neto`, `iva`, `dgr`, `periodo`, `estado`, `CESP`, `VencCESP`
- `consumo`: aprox. 61380 filas. Columnas: `idconsumo`, `idconexion`, `fechatoma`, `estadomed`, `periodo`, `consumo`, `facturado`
- `ctacte`: aprox. 25146 filas. Columnas: `idCtaCte`, `Fecha`, `idFactura`, `idRecibo`, `Monto`, `_usuario`, `_fecha`, `_hora`
- `movcaja`: aprox. 20157 filas. Columnas: `idMovCaja`, `Fecha`, `idTipoComp`, `numcomp`, `importe`, `banco`, `sucursal`, `numche`, `vence`, `cuit`, `estado`, `idCabFact`, `idProveedor`, `idCliente`, `_usuario`, `_fecha`
- `artprov`: aprox. 10397 filas. Columnas: `idArtxProv`, `idArticulo`, `idProveedor`, `UnCompra`, `CalculoCompra`, `UnVenta`, `CalculoVenta`, `Costo`, `Descuentos`, `Recargos`, `Total`, `Peso`, `CodigoProv`, `CompraMinima`, `TipoFlete`, `idTipoFlete`
- `articulos`: aprox. 8878 filas. Columnas: `idArticulo`, `Nombre`, `NombreTicket`, `Unidad`, `idGrupo`, `Costo`, `Peso`, `ProvPpal`, `Incre1`, `Precio1`, `Incre2`, `Precio2`, `Incre3`, `Precio3`, `Visible`, `Descuenta`
- `pendfact`: aprox. 7680 filas. Columnas: `idpendfact`, `idconexion`, `idcliente`, `idconcepto`, `periodo`, `neto`, `iva`, `dgr`, `detalle`, `facturado`
- `conexiones`: aprox. 606 filas. Columnas: `idconexion`, `idcliente`, `direccion`, `ubicacion`, `zona`, `ultmed`, `activo`, `socio`, `fechaingreso`, `integracion`
- `clientes`: aprox. 476 filas. Columnas: `idcliente`, `nombre`, `direccion`, `telefono`, `tipdoc`, `numdoc`, `sitiva`, `zona`, `activo`, `cuit`, `descuento`, `TitularInmueble`, `TitularServicio`, `Partida`, `Departamento`, `Municipio`
- `formula`: aprox. 44 filas. Columnas: `for_id`, `for_nomb`, `sis_id`, `tfo_id`, `for_orde`, `for_pare`, `for_arch`, `for_imag`, `gfo_id`
- `provincias`: aprox. 24 filas. Columnas: `codigo`, `denominacion`

## Relaciones declaradas

- `articulos.idGrupo` -> `grupos.idGrupo`
- `articulos.ProvPpal` -> `proveedores.idProveedor`
- `articulos.TipoIva` -> `tipoiva.CODIGO`
- `articulos.Unidad` -> `unimedi.Unidad`
- `artprov.idArticulo` -> `articulos.idArticulo`
- `artprov.idProveedor` -> `proveedores.idProveedor`
- `artprov.idTipoFlete` -> `tipoflete.idTipoFlete`
- `artprov.UnCompra` -> `unimedi.Unidad`
- `artprov.UnVenta` -> `unimedi.Unidad`
- `cabfact.idcliente` -> `clientes.idcliente`
- `cabfact.idconexion` -> `conexiones.idconexion`
- `clientes.sitiva` -> `tablas.ID_Tabla`
- `clientes.tipdoc` -> `tablas.ID_Tabla`
- `clientes.zona` -> `tablas.ID_Tabla`
- `conexiones.zona` -> `tablas.ID_Tabla`
- `consumo.idconexion` -> `conexiones.idconexion`
- `ctacte.idFactura` -> `cabfact.IdCabFact`
- `detfact.idconcepto` -> `conceptos.idconcepto`
- `movcaja.idTipoComp` -> `tip_comp.Codigo`
- `pcabecera.idTipo` -> `tip_comp.Codigo`
- `pendfact.idcliente` -> `clientes.idcliente`
- `pendfact.idconcepto` -> `conceptos.idconcepto`
- `pendfact.idconexion` -> `conexiones.idconexion`
- `rangom3.idConcepto` -> `conceptos.idconcepto`
- `tablas.ID_TipTab` -> `tipotablas.ID_TipTab`
- `titularinmueble.idConexion` -> `conexiones.idconexion`
- `titularinmueble.sitfteiva` -> `tablas.ID_Tabla`
- `titularinmueble.TipoDocumento` -> `tablas.ID_Tabla`
- `titularservicio.idConexion` -> `conexiones.idconexion`
- `titularservicio.TipoDoc` -> `tablas.ID_Tabla`

## Rangos de fechas

- `accesos.acc_fech`: 0 registros, desde `None` hasta `None`
- `articulos.UltAct`: 9130 registros, desde `2018-11-13` hasta `2024-10-22`
- `cabfact.fechaem`: 62805 registros, desde `2010-04-30` hasta `2026-04-30`
- `cabfact.fechaven`: 62805 registros, desde `2010-05-05` hasta `2026-12-15`
- `cabfact.fechapag`: 62805 registros, desde `0000-00-00` hasta `2089-01-02`
- `cabfact.VencCESP`: 62805 registros, desde `0000-00-00` hasta `2026-04-30`
- `conexiones.fechaingreso`: 606 registros, desde `0000-00-00` hasta `2103-06-06`
- `consumo.fechatoma`: 61224 registros, desde `2008-10-31` hasta `2026-04-30`
- `ctacte.Fecha`: 24898 registros, desde `2020-11-06` hasta `2026-05-04`
- `ctacte._fecha`: 24898 registros, desde `2020-11-06` hasta `2026-05-04`
- `factimp.fechaem`: error al inspeccionar.
- `factimp.fechapag`: error al inspeccionar.
- `facturas.fechaem`: 200077 registros, desde `2010-04-30` hasta `2026-04-30`
- `facturas.fechaven`: 200077 registros, desde `2010-05-05` hasta `2026-12-15`
- `facturas.fechapag`: 200077 registros, desde `0000-00-00` hasta `2089-01-02`
- `movcaja.Fecha`: 20223 registros, desde `2020-11-06` hasta `2026-05-04`
- `movcaja.vence`: 20223 registros, desde `2020-11-06` hasta `2026-05-04`
- `movcaja._fecha`: 20223 registros, desde `2020-11-06` hasta `2026-05-04`
- `pcabecera.fecha`: 0 registros, desde `None` hasta `None`
- `pcabecera._fecha`: 0 registros, desde `None` hasta `None`
- `tablas.F_Alta`: 14 registros, desde `0000-00-00` hasta `0000-00-00`
- `tablas.F_Baja`: 14 registros, desde `0000-00-00` hasta `0000-00-00`
- `tipotablas.F_Alta`: 3 registros, desde `2009-09-29` hasta `2009-12-16`
- `tipotablas.F_Baja`: 3 registros, desde `0000-00-00` hasta `0000-00-00`
- `usuarios.FECHAING`: 1 registros, desde `2004-12-20` hasta `2004-12-20`
- `usuarios.FECHABAJA`: 1 registros, desde `0000-00-00` hasta `0000-00-00`

## Ideas iniciales para dashboard ejecutivo

- Facturacion: evolucion mensual, importes por tipo de comprobante, servicios/familias facturadas.
- Cuenta corriente: saldos, deuda vencida, antiguedad de deuda, clientes con mayor saldo.
- Consumos: evolucion por periodo, conexiones sin lectura, consumos cero, saltos anormales.
- Conexiones: altas/bajas, estado del padron, distribucion por zona/tipo de servicio.
- Clientes/socios: padron activo, segmentacion por zona, titularidad y datos incompletos.
- Caja/cobranzas: ingresos por fecha, medios/conceptos, conciliacion operativa.
- Pendientes de facturacion: volumen pendiente, antiguedad y riesgo operativo.
- Articulos/proveedores: inventario o items facturables si aplican a la operatoria.
- Mapa ejecutivo: capas geograficas disponibles en conexiones.

## Archivos generados

- `tables.csv`: inventario de tablas y tamanos.
- `columns.csv`: columnas y tipos.
- `indexes.csv`: indices detectados.
- `foreign_keys.csv`: relaciones declaradas, si existen.
- `date_ranges.csv`: rangos de campos fecha.
