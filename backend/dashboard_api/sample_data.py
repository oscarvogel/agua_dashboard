from __future__ import annotations


SAMPLE_ROWS = {
    "clientes": [
        {"idcliente": 1, "nombre": "Consorcio Centro", "activo": 1, "zona": 1},
        {"idcliente": 2, "nombre": "Familia Benitez", "activo": 1, "zona": 2},
        {"idcliente": 3, "nombre": "Comercio El Molino", "activo": 1, "zona": 1},
        {"idcliente": 4, "nombre": "Loteo Norte", "activo": 0, "zona": 3},
    ],
    "conexiones": [
        {"idconexion": 10, "idcliente": 1, "activo": 1, "zona": 1, "ultmed": "2026-04-30"},
        {"idconexion": 11, "idcliente": 2, "activo": 1, "zona": 2, "ultmed": "2026-02-15"},
        {"idconexion": 12, "idcliente": 3, "activo": 1, "zona": 1, "ultmed": "2026-04-30"},
        {"idconexion": 13, "idcliente": 4, "activo": 0, "zona": 3, "ultmed": "2025-12-31"},
    ],
    "cabfact": [
        {"IdCabFact": 100, "idcliente": 1, "fechaem": "2026-05-05", "fechaven": "2026-05-20", "neto": 18800, "iva": 3948, "dgr": 0, "estado": 0},
        {"IdCabFact": 101, "idcliente": 2, "fechaem": "2026-05-05", "fechaven": "2026-05-20", "neto": 9200, "iva": 1932, "dgr": 0, "estado": 0},
        {"IdCabFact": 102, "idcliente": 3, "fechaem": "2026-04-05", "fechaven": "2026-04-20", "neto": 24100, "iva": 5061, "dgr": 0, "estado": 0},
        {"IdCabFact": 103, "idcliente": 1, "fechaem": "2026-03-05", "fechaven": "2026-03-20", "neto": 17400, "iva": 3654, "dgr": 0, "estado": 0},
    ],
    "movcaja": [
        {"idMovCaja": 900, "Fecha": "2026-05-10", "importe": 12000, "estado": 0},
        {"idMovCaja": 901, "Fecha": "2026-05-15", "importe": 8500, "estado": 0},
        {"idMovCaja": 902, "Fecha": "2026-04-18", "importe": 21000, "estado": 0},
    ],
    "ctacte": [
        {"idCtaCte": 1, "idFactura": 100, "Monto": 22748, "Fecha": "2026-05-05"},
        {"idCtaCte": 2, "idFactura": 101, "Monto": 11132, "Fecha": "2026-05-05"},
        {"idCtaCte": 3, "idFactura": 102, "Monto": 29161, "Fecha": "2026-04-05"},
        {"idCtaCte": 4, "idRecibo": 900, "Monto": -12000, "Fecha": "2026-05-10"},
        {"idCtaCte": 5, "idRecibo": 901, "Monto": -8500, "Fecha": "2026-05-15"},
    ],
    "consumo": [
        {"idconsumo": 1, "idconexion": 10, "periodo": 202604, "consumo": 19, "fechatoma": "2026-04-30"},
        {"idconsumo": 2, "idconexion": 11, "periodo": 202604, "consumo": 0, "fechatoma": "2026-04-30"},
        {"idconsumo": 3, "idconexion": 12, "periodo": 202604, "consumo": 44, "fechatoma": "2026-04-30"},
    ],
    "pendfact": [
        {"idpendfact": 1, "idcliente": 2, "idconexion": 11, "periodo": 202605, "neto": 3800, "iva": 798, "dgr": 0, "facturado": 0},
        {"idpendfact": 2, "idcliente": 3, "idconexion": 12, "periodo": 202605, "neto": 6200, "iva": 1302, "dgr": 0, "facturado": 0},
    ],
}
