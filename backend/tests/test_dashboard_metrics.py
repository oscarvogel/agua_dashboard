from datetime import date

from dashboard_api.metrics import build_dashboard_payload, normalize_date


def test_normalize_date_rejects_mysql_zero_and_far_future_dates():
    assert normalize_date("0000-00-00") is None
    assert normalize_date("2103-06-06") is None
    assert normalize_date("2026-04-30") == date(2026, 4, 30)


def test_build_dashboard_payload_computes_executive_indicators_from_rows():
    payload = build_dashboard_payload(
        {
            "clientes": [
                {"idcliente": 1, "activo": 1, "nombre": "Cliente A"},
                {"idcliente": 2, "activo": 0, "nombre": "Cliente B"},
            ],
            "conexiones": [
                {"idconexion": 10, "idcliente": 1, "activo": 1, "zona": 1, "ultmed": "2026-04-30"},
                {"idconexion": 11, "idcliente": 2, "activo": 0, "zona": 2, "ultmed": "2025-01-31"},
            ],
            "cabfact": [
                {"IdCabFact": 100, "idcliente": 1, "fechaem": "2026-04-30", "fechaven": "2026-06-15", "neto": 1000, "iva": 210, "dgr": 0, "estado": 0},
                {"IdCabFact": 101, "idcliente": 2, "fechaem": "2026-04-30", "fechaven": "2026-04-15", "neto": 500, "iva": 105, "dgr": 0, "estado": 0},
            ],
            "movcaja": [
                {"idMovCaja": 900, "Fecha": "2026-04-30", "importe": 700, "estado": 0},
            ],
            "ctacte": [
                {"idCtaCte": 1, "idFactura": 100, "Monto": 1210, "Fecha": "2026-04-30"},
                {"idCtaCte": 2, "idFactura": 101, "Monto": 605, "Fecha": "2026-04-30"},
                {"idCtaCte": 3, "idRecibo": 900, "Monto": -700, "Fecha": "2026-04-30"},
            ],
            "consumo": [
                {"idconsumo": 1, "idconexion": 10, "periodo": 202604, "consumo": 12, "fechatoma": "2026-04-30"},
                {"idconsumo": 2, "idconexion": 11, "periodo": 202604, "consumo": 0, "fechatoma": "2025-01-31"},
            ],
            "pendfact": [
                {"idpendfact": 77, "idconexion": 10, "idcliente": 1, "periodo": 202604, "neto": 200, "iva": 42, "dgr": 0, "facturado": 0},
            ],
        },
        today=date(2026, 5, 29),
    )

    assert payload["source"]["mode"] == "computed"
    assert payload["summary"]["clientes_activos"] == 1
    assert payload["summary"]["conexiones_activas"] == 1
    assert payload["summary"]["facturacion_mes"] == 1815
    assert payload["summary"]["cobranzas_mes"] == 700
    assert payload["summary"]["deuda_total"] == 1115
    assert payload["summary"]["deuda_vencida"] == 605
    assert payload["summary"]["deuda_vencida"] <= payload["summary"]["deuda_total"]
    assert payload["summary"]["pendiente_facturacion"] == 242
    assert payload["summary"]["consumo_ultimo_periodo"] == 12
    assert payload["summary"]["conexiones_sin_lectura_reciente"] == 1
    assert payload["top_deudores"][0]["cliente"] == "Cliente A"
    assert all(row["deuda"] > 0 for row in payload["top_deudores"])


def test_period_scope_changes_visible_billing_and_collections():
    rows = {
        "clientes": [],
        "conexiones": [],
        "cabfact": [
            {"IdCabFact": 1, "fechaem": "2026-03-10", "fechaven": "2026-04-10", "neto": 100, "iva": 0, "dgr": 0},
            {"IdCabFact": 2, "fechaem": "2026-04-10", "fechaven": "2026-05-10", "neto": 200, "iva": 0, "dgr": 0},
            {"IdCabFact": 3, "fechaem": "2026-05-10", "fechaven": "2026-06-10", "neto": 300, "iva": 0, "dgr": 0},
        ],
        "movcaja": [
            {"Fecha": "2026-03-11", "importe": 10, "estado": 0},
            {"Fecha": "2026-04-11", "importe": 20, "estado": 0},
            {"Fecha": "2026-05-11", "importe": 30, "estado": 0},
        ],
    }

    current = build_dashboard_payload(rows, today=date(2026, 5, 29), period="actual")
    quarter = build_dashboard_payload(rows, today=date(2026, 5, 29), period="trim")

    assert current["summary"]["facturacion_mes"] == 300
    assert current["summary"]["cobranzas_mes"] == 30
    assert quarter["summary"]["facturacion_mes"] == 600
    assert quarter["summary"]["cobranzas_mes"] == 60


def test_multiple_periods_scope_visible_billing_and_collections():
    rows = {
        "clientes": [],
        "conexiones": [],
        "cabfact": [
            {"IdCabFact": 1, "fechaem": "2026-03-10", "fechaven": "2026-04-10", "neto": 100, "iva": 0, "dgr": 0},
            {"IdCabFact": 2, "fechaem": "2026-04-10", "fechaven": "2026-05-10", "neto": 200, "iva": 0, "dgr": 0},
            {"IdCabFact": 3, "fechaem": "2026-05-10", "fechaven": "2026-06-10", "neto": 300, "iva": 0, "dgr": 0},
        ],
        "movcaja": [
            {"Fecha": "2026-03-11", "importe": 10, "estado": 0},
            {"Fecha": "2026-04-11", "importe": 20, "estado": 0},
            {"Fecha": "2026-05-11", "importe": 30, "estado": 0},
        ],
    }

    payload = build_dashboard_payload(rows, today=date(2026, 5, 29), periods=["2026-03", "2026-05"])

    assert payload["summary"]["facturacion_mes"] == 400
    assert payload["summary"]["cobranzas_mes"] == 40
    assert payload["filters"]["periods"] == ["2026-03", "2026-05"]


def test_monthly_series_includes_consumption_values():
    payload = build_dashboard_payload(
        {
            "clientes": [],
            "conexiones": [],
            "consumo": [
                {"periodo": 202604, "consumo": 10},
                {"periodo": 202604, "consumo": 5},
                {"periodo": 202605, "consumo": 7},
            ],
        },
        today=date(2026, 5, 29),
    )

    consumption_by_period = {row["periodo"]: row["consumo"] for row in payload["series"]["monthly"]}

    assert consumption_by_period["2026-04"] == 15
    assert consumption_by_period["2026-05"] == 7


def test_daily_series_groups_billing_collections_and_consumption_by_day():
    payload = build_dashboard_payload(
        {
            "clientes": [],
            "conexiones": [],
            "cabfact": [
                {"fechaem": "2026-05-01", "fechaven": "2026-05-20", "neto": 100, "iva": 21, "dgr": 0},
                {"fechaem": "2026-05-01", "fechaven": "2026-05-20", "neto": 50, "iva": 10, "dgr": 0},
                {"fechaem": "2026-05-02", "fechaven": "2026-05-20", "neto": 200, "iva": 42, "dgr": 0},
            ],
            "movcaja": [
                {"Fecha": "2026-05-01", "importe": 70, "estado": 0},
                {"Fecha": "2026-05-02", "importe": 90, "estado": 0},
            ],
            "consumo": [
                {"periodo": 202605, "fechatoma": "2026-05-01", "consumo": 12},
                {"periodo": 202605, "fechatoma": "2026-05-02", "consumo": 8},
            ],
        },
        today=date(2026, 5, 29),
    )

    daily = {row["fecha"]: row for row in payload["series"]["daily"]["2026-05"]}

    assert daily["2026-05-01"]["facturacion"] == 181
    assert daily["2026-05-02"]["facturacion"] == 242
    assert daily["2026-05-01"]["cobranzas"] == 70
    assert daily["2026-05-02"]["consumo"] == 8


def test_collections_use_movcaja_not_cabfact_payment_date():
    payload = build_dashboard_payload(
        {
            "clientes": [],
            "conexiones": [],
            "cabfact": [
                {
                    "fechaem": "2026-05-01",
                    "fechapag": "2026-05-03",
                    "fechaven": "2026-05-20",
                    "neto": 1000,
                    "iva": 0,
                    "dgr": 0,
                },
            ],
            "movcaja": [
                {"Fecha": "2026-05-04", "importe": 250, "estado": 0},
            ],
        },
        today=date(2026, 5, 29),
    )

    daily = {row["fecha"]: row for row in payload["series"]["daily"]["2026-05"]}

    assert payload["summary"]["cobranzas_mes"] == 250
    assert "2026-05-03" not in daily
    assert daily["2026-05-04"]["cobranzas"] == 250


def test_collection_day_detail_groups_amount_by_client():
    payload = build_dashboard_payload(
        {
            "clientes": [
                {"idcliente": 1, "nombre": "Socio Uno"},
                {"idcliente": 2, "nombre": "Socio Dos"},
            ],
            "movcaja": [
                {"Fecha": "2026-05-04", "idCliente": 1, "importe": 120, "estado": 0, "numcomp": "A001"},
                {"Fecha": "2026-05-04", "idCliente": 1, "importe": 30, "estado": 0, "numcomp": "A002"},
                {"Fecha": "2026-05-04", "idCliente": 2, "importe": 75, "estado": 0, "numcomp": "B001"},
                {"Fecha": "2026-05-04", "idCliente": 2, "importe": 500, "estado": "A", "numcomp": "ANULADO"},
            ],
        },
        today=date(2026, 5, 29),
    )

    detail = payload["breakdowns"]["cobranzas_por_dia_socio"]["2026-05-04"]

    assert detail[0]["cliente"] == "Socio Uno"
    assert detail[0]["importe"] == 150
    assert detail[0]["movimientos"] == 2
    assert detail[0]["comprobantes"] == ["A001", "A002"]
    assert detail[1]["cliente"] == "Socio Dos"
    assert detail[1]["importe"] == 75


def test_collection_day_detail_only_includes_visible_periods():
    payload = build_dashboard_payload(
        {
            "clientes": [
                {"idcliente": 1, "nombre": "Socio Uno"},
            ],
            "movcaja": [
                {"Fecha": "2026-04-04", "idCliente": 1, "importe": 100, "estado": 0, "numcomp": "A001"},
                {"Fecha": "2026-05-04", "idCliente": 1, "importe": 200, "estado": 0, "numcomp": "A002"},
            ],
        },
        today=date(2026, 5, 29),
        periods=["2026-05"],
    )

    detail = payload["breakdowns"]["cobranzas_por_dia_socio"]

    assert "2026-05-04" in detail
    assert "2026-04-04" not in detail


def test_collections_premium_payload_tracks_health_zone_efficiency_and_followup():
    payload = build_dashboard_payload(
        {
            "clientes": [
                {"idcliente": 1, "activo": 1, "nombre": "Socio Critico", "zona": 1},
                {"idcliente": 2, "activo": 1, "nombre": "Socio Recuperado", "zona": 1},
                {"idcliente": 3, "activo": 1, "nombre": "Socio Al Dia", "zona": 2},
            ],
            "conexiones": [
                {"idconexion": 10, "idcliente": 1, "activo": 1, "zona": 1},
                {"idconexion": 20, "idcliente": 2, "activo": 1, "zona": 1},
                {"idconexion": 30, "idcliente": 3, "activo": 1, "zona": 2},
            ],
            "cabfact": [
                {"IdCabFact": 100, "idcliente": 1, "idconexion": 10, "fechaem": "2026-05-01", "fechaven": "2026-04-15", "neto": 1000, "iva": 0, "dgr": 0},
                {"IdCabFact": 101, "idcliente": 1, "idconexion": 10, "fechaem": "2026-04-01", "fechaven": "2026-03-15", "neto": 600, "iva": 0, "dgr": 0},
                {"IdCabFact": 200, "idcliente": 2, "idconexion": 20, "fechaem": "2026-05-02", "fechaven": "2026-04-20", "neto": 800, "iva": 0, "dgr": 0},
                {"IdCabFact": 300, "idcliente": 3, "idconexion": 30, "fechaem": "2026-05-03", "fechaven": "2026-06-20", "neto": 200, "iva": 0, "dgr": 0},
            ],
            "ctacte": [
                {"idFactura": 100, "Monto": 1000},
                {"idFactura": 101, "Monto": 600},
                {"idFactura": 200, "Monto": 800},
                {"idFactura": 300, "Monto": 200},
            ],
            "movcaja": [
                {"Fecha": "2026-04-10", "idCliente": 2, "importe": 200, "estado": 0},
                {"Fecha": "2026-05-05", "idCliente": 2, "importe": 300, "estado": 0},
                {"Fecha": "2026-05-08", "idCliente": 3, "importe": 100, "estado": 0},
                {"Fecha": "2026-05-11", "idCliente": 2, "importe": 50, "estado": "A"},
            ],
        },
        today=date(2026, 5, 12),
    )

    collections = payload["collections"]

    assert collections["health"]["period_collected"] == 400
    assert collections["health"]["previous_period_collected"] == 200
    assert collections["health"]["variation_pct"] == 100
    assert collections["health"]["last_7_days"] == 400
    assert collections["health"]["paying_clients"] == 2
    assert collections["health"]["estimated_recovery_rate"] == 16.67
    assert collections["health"]["status"] == "good"
    assert collections["daily_performance"][-1]["accumulated"] == 400
    assert collections["daily_performance"][-1]["expected_accumulated"] == 400
    assert collections["zone_efficiency"][0] == {
        "zona": "1",
        "collected": 300.0,
        "debt_total": 2400.0,
        "overdue_debt": 2400.0,
        "paying_clients": 1,
        "recovery_rate": 12.5,
    }
    assert collections["concentration"]["top_10_share"] == 100
    assert collections["followup"][0]["cliente"] == "Socio Critico"
    assert collections["followup"][0]["accion_sugerida"] == "Llamar"
    assert collections["followup"][0]["riesgo"] == "alto"
    assert collections["followup"][1]["accion_sugerida"] == "Seguimiento normal"


def test_zone_and_active_filters_scope_connections_clients_and_debtors():
    rows = {
        "clientes": [
            {"idcliente": 1, "activo": 1, "nombre": "Zona Uno", "zona": 1},
            {"idcliente": 2, "activo": 0, "nombre": "Zona Dos Inactivo", "zona": 2},
        ],
        "conexiones": [
            {"idconexion": 10, "idcliente": 1, "activo": 1, "zona": 1, "ultmed": "2026-05-01"},
            {"idconexion": 20, "idcliente": 2, "activo": 0, "zona": 2, "ultmed": "2026-05-01"},
        ],
        "cabfact": [
            {"IdCabFact": 100, "idcliente": 1, "idconexion": 10, "fechaem": "2026-05-10", "fechaven": "2026-06-10", "neto": 100, "iva": 0, "dgr": 0},
            {"IdCabFact": 200, "idcliente": 2, "idconexion": 20, "fechaem": "2026-05-10", "fechaven": "2026-06-10", "neto": 200, "iva": 0, "dgr": 0},
        ],
        "ctacte": [
            {"idFactura": 100, "Monto": 100},
            {"idFactura": 200, "Monto": 200},
        ],
    }

    payload = build_dashboard_payload(rows, today=date(2026, 5, 29), zone="1", status_filter="activos")

    assert payload["summary"]["clientes_activos"] == 1
    assert payload["summary"]["conexiones_activas"] == 1
    assert payload["summary"]["facturacion_mes"] == 100
    assert payload["summary"]["deuda_total"] == 100
    assert payload["top_deudores"] == [{"cliente": "Zona Uno", "idcliente": 1, "deuda": 100.0}]


def test_stale_readings_use_consumption_dates_when_connection_last_read_is_not_a_date():
    payload = build_dashboard_payload(
        {
            "clientes": [],
            "conexiones": [
                {"idconexion": 1, "activo": 1, "ultmed": "1234.00"},
                {"idconexion": 2, "activo": 1, "ultmed": "5678.00"},
            ],
            "consumo": [
                {"idconexion": 1, "fechatoma": "2026-05-01", "periodo": 202605, "consumo": 10},
                {"idconexion": 2, "fechatoma": "2025-12-01", "periodo": 202512, "consumo": 8},
            ],
        },
        today=date(2026, 5, 29),
    )

    assert payload["summary"]["conexiones_sin_lectura_reciente"] == 1


def test_breakdowns_include_debt_aging_zone_billing_concepts_and_pending_periods():
    payload = build_dashboard_payload(
        {
            "clientes": [
                {"idcliente": 1, "activo": 1, "nombre": "Cliente A", "zona": 1},
                {"idcliente": 2, "activo": 1, "nombre": "Cliente B", "zona": 2},
            ],
            "conexiones": [
                {"idconexion": 10, "idcliente": 1, "activo": 1, "zona": 1},
                {"idconexion": 20, "idcliente": 2, "activo": 1, "zona": 2},
            ],
            "cabfact": [
                {"IdCabFact": 100, "idcliente": 1, "idconexion": 10, "fechaem": "2026-05-01", "fechaven": "2026-05-20", "neto": 1000, "iva": 0, "dgr": 0},
                {"IdCabFact": 200, "idcliente": 2, "idconexion": 20, "fechaem": "2026-04-01", "fechaven": "2026-04-15", "neto": 500, "iva": 0, "dgr": 0},
            ],
            "detfact": [
                {"IdCabFact": 100, "idconcepto": 7, "neto": 800, "iva": 0, "dgr": 0},
                {"IdCabFact": 100, "idconcepto": 8, "neto": 200, "iva": 0, "dgr": 0},
                {"IdCabFact": 200, "idconcepto": 7, "neto": 500, "iva": 0, "dgr": 0},
            ],
            "conceptos": [
                {"idconcepto": 7, "descripcion": "Agua"},
                {"idconcepto": 8, "descripcion": "Mantenimiento"},
            ],
            "ctacte": [
                {"idFactura": 100, "Monto": 1000, "Fecha": "2026-05-01"},
                {"idFactura": 200, "Monto": 500, "Fecha": "2026-04-01"},
            ],
            "pendfact": [
                {"idcliente": 1, "idconexion": 10, "periodo": 202605, "idconcepto": 7, "neto": 300, "iva": 0, "dgr": 0, "facturado": 0},
                {"idcliente": 2, "idconexion": 20, "periodo": 202604, "idconcepto": 8, "neto": 150, "iva": 0, "dgr": 0, "facturado": 0},
            ],
            "consumo": [
                {"idconexion": 10, "periodo": 202605, "consumo": 10, "fechatoma": "2026-05-10"},
                {"idconexion": 20, "periodo": 202605, "consumo": 30, "fechatoma": "2026-05-10"},
            ],
        },
        today=date(2026, 6, 30),
    )

    assert payload["breakdowns"]["deuda_antiguedad"] == [
        {"rango": "31-60 dias", "importe": 1000.0},
        {"rango": "61-90 dias", "importe": 500.0},
    ]
    assert payload["breakdowns"]["deuda_zona"] == [
        {"zona": "1", "importe": 1000.0},
        {"zona": "2", "importe": 500.0},
    ]
    assert payload["breakdowns"]["facturacion_concepto"] == [
        {"concepto": "Agua", "importe": 1300.0},
        {"concepto": "Mantenimiento", "importe": 200.0},
    ]
    assert payload["breakdowns"]["pendientes_periodo"] == [
        {"periodo": "2026-04", "importe": 150.0},
        {"periodo": "2026-05", "importe": 300.0},
    ]
    assert payload["breakdowns"]["pendientes_concepto"] == [
        {"concepto": "Agua", "importe": 300.0},
        {"concepto": "Mantenimiento", "importe": 150.0},
    ]
    assert payload["breakdowns"]["consumo_zona"] == [
        {"zona": "1", "consumo": 10.0},
        {"zona": "2", "consumo": 30.0},
    ]


def test_operational_quality_indicators_include_averages_statuses_and_missing_locations():
    payload = build_dashboard_payload(
        {
            "clientes": [
                {"idcliente": 1, "activo": 1, "nombre": "Cliente A", "zona": 1},
                {"idcliente": 2, "activo": 1, "nombre": "Cliente B", "zona": 2},
                {"idcliente": 3, "activo": 0, "nombre": "Cliente C", "zona": 2},
            ],
            "conexiones": [
                {"idconexion": 10, "idcliente": 1, "activo": 1, "zona": 1, "ubicacion": "-31,-61"},
                {"idconexion": 20, "idcliente": 2, "activo": 1, "zona": 2, "ubicacion": ""},
                {"idconexion": 30, "idcliente": 3, "activo": 0, "zona": 2, "ubicacion": None},
            ],
            "cabfact": [
                {"IdCabFact": 100, "idcliente": 1, "idconexion": 10, "fechaem": "2026-05-01", "fechaven": "2026-05-20", "neto": 100, "iva": 0, "dgr": 0, "estado": 0},
                {"IdCabFact": 200, "idcliente": 2, "idconexion": 20, "fechaem": "2026-05-02", "fechaven": "2026-05-20", "neto": 50, "iva": 0, "dgr": 0, "estado": 9},
            ],
            "movcaja": [
                {"Fecha": "2026-05-03", "importe": 25, "estado": 0},
                {"Fecha": "2026-05-04", "importe": 35, "estado": 2},
            ],
            "consumo": [
                {"idconexion": 10, "periodo": 202605, "consumo": 10, "fechatoma": "2026-05-10"},
                {"idconexion": 20, "periodo": 202605, "consumo": 30, "fechatoma": "2026-05-10"},
            ],
        },
        today=date(2026, 5, 29),
    )

    assert payload["summary"]["importe_promedio_conexion"] == 75
    assert payload["summary"]["consumo_promedio_conexion"] == 20
    assert payload["summary"]["conexiones_sin_ubicacion"] == 2
    assert payload["summary"]["comprobantes_estado_dudoso"] == 2
    assert payload["breakdowns"]["padron_zona"] == [
        {"zona": "1", "clientes": 1, "conexiones": 1},
        {"zona": "2", "clientes": 2, "conexiones": 2},
    ]
    assert payload["breakdowns"]["comprobantes_estado"] == [
        {"tipo": "factura", "estado": "9", "cantidad": 1},
        {"tipo": "movcaja", "estado": "2", "cantidad": 1},
    ]


def test_registry_recent_payments_new_connections_and_missing_consumption_indicators():
    payload = build_dashboard_payload(
        {
            "clientes": [
                {"idcliente": 1, "activo": 1, "nombre": "Cliente A", "zona": 1},
                {"idcliente": 2, "activo": 0, "nombre": "Cliente B", "zona": 1},
                {"idcliente": 3, "activo": 1, "nombre": "Cliente C", "zona": 2},
            ],
            "conexiones": [
                {"idconexion": 10, "idcliente": 1, "activo": 1, "zona": 1, "fechaingreso": "2026-05-10"},
                {"idconexion": 20, "idcliente": 2, "activo": 0, "zona": 1, "fechaingreso": "2026-04-10"},
                {"idconexion": 30, "idcliente": 3, "activo": 1, "zona": 2, "fechaingreso": "0000-00-00"},
            ],
            "cabfact": [
                {"IdCabFact": 100, "idcliente": 1, "idconexion": 10, "fechaem": "2026-05-01", "fechaven": "2026-05-20", "neto": 100, "iva": 0, "dgr": 0},
                {"IdCabFact": 200, "idcliente": 1, "idconexion": 10, "fechaem": "2026-04-01", "fechaven": "2026-04-20", "neto": 90, "iva": 0, "dgr": 0},
            ],
            "ctacte": [
                {"idFactura": 100, "Monto": 100},
                {"idFactura": 200, "Monto": 90},
            ],
            "movcaja": [
                {"Fecha": "2026-05-20", "importe": 25, "estado": 0, "idCliente": 1},
                {"Fecha": "2026-04-15", "importe": 35, "estado": 0, "idCliente": 2},
            ],
            "consumo": [
                {"idconexion": 10, "periodo": 202605, "consumo": 10, "fechatoma": "2026-05-10"},
                {"idconexion": 20, "periodo": 202604, "consumo": 20, "fechatoma": "2026-04-10"},
            ],
        },
        today=date(2026, 5, 29),
    )

    assert payload["summary"]["clientes_con_pagos_recientes"] == 1
    assert payload["summary"]["conexiones_sin_consumo_registrado"] == 1
    assert payload["summary"]["conexiones_con_deuda_recurrente"] == 1
    assert payload["breakdowns"]["padron_estado_zona"] == [
        {"zona": "1", "clientes_activos": 1, "clientes_inactivos": 1, "conexiones_activas": 1, "conexiones_inactivas": 1},
        {"zona": "2", "clientes_activos": 1, "clientes_inactivos": 0, "conexiones_activas": 1, "conexiones_inactivas": 0},
    ]
    assert payload["breakdowns"]["altas_periodo"] == [
        {"periodo": "2026-04", "conexiones": 1},
        {"periodo": "2026-05", "conexiones": 1},
    ]
    assert payload["breakdowns"]["clientes_pagos_recientes"] == [
        {"cliente": "Cliente A", "idcliente": 1, "importe": 25.0, "fecha": "2026-05-20"},
    ]


def test_consumption_jumps_and_repeated_pending_indicators():
    payload = build_dashboard_payload(
        {
            "clientes": [
                {"idcliente": 1, "activo": 1, "nombre": "Cliente A", "zona": 1},
                {"idcliente": 2, "activo": 1, "nombre": "Cliente B", "zona": 1},
            ],
            "conexiones": [
                {"idconexion": 10, "idcliente": 1, "activo": 1, "zona": 1},
                {"idconexion": 20, "idcliente": 2, "activo": 1, "zona": 1},
            ],
            "consumo": [
                {"idconexion": 10, "periodo": 202602, "consumo": 9, "fechatoma": "2026-02-10"},
                {"idconexion": 10, "periodo": 202603, "consumo": 11, "fechatoma": "2026-03-10"},
                {"idconexion": 10, "periodo": 202604, "consumo": 10, "fechatoma": "2026-04-10"},
                {"idconexion": 10, "periodo": 202605, "consumo": 35, "fechatoma": "2026-05-10"},
                {"idconexion": 20, "periodo": 202604, "consumo": 20, "fechatoma": "2026-04-10"},
                {"idconexion": 20, "periodo": 202605, "consumo": 22, "fechatoma": "2026-05-10"},
            ],
            "pendfact": [
                {"idcliente": 1, "idconexion": 10, "periodo": 202604, "neto": 100, "iva": 0, "dgr": 0, "facturado": 0},
                {"idcliente": 1, "idconexion": 10, "periodo": 202605, "neto": 200, "iva": 0, "dgr": 0, "facturado": 0},
                {"idcliente": 2, "idconexion": 20, "periodo": 202605, "neto": 50, "iva": 0, "dgr": 0, "facturado": 0},
            ],
        },
        today=date(2026, 5, 29),
    )

    assert payload["summary"]["saltos_anormales_consumo"] == 1
    assert payload["summary"]["pendientes_repetidos"] == 1
    assert payload["breakdowns"]["saltos_consumo"] == [
        {
            "idconexion": 10,
            "periodo": "2026-05",
            "consumo_actual": 35.0,
            "media_historica": 10.0,
            "variacion": 25.0,
            "direccion": "suba",
            "muestras_historicas": 3,
        }
    ]
    assert payload["breakdowns"]["pendientes_repetidos"] == [
        {"cliente": "Cliente A", "idcliente": 1, "idconexion": 10, "pendientes": 2, "importe": 300.0}
    ]


def test_connection_map_points_parse_locations_and_classify_statuses():
    payload = build_dashboard_payload(
        {
            "clientes": [
                {"idcliente": 1, "nombre": "Normal"},
                {"idcliente": 2, "nombre": "Cero"},
                {"idcliente": 3, "nombre": "Salto"},
                {"idcliente": 4, "nombre": "Sin Lectura"},
                {"idcliente": 5, "nombre": "Normal con dato viejo"},
            ],
            "conexiones": [
                {"idconexion": 10, "idcliente": 1, "zona": 1, "direccion": "A", "ubicacion": "-26.1, -54.1", "activo": 1},
                {"idconexion": 20, "idcliente": 2, "zona": 1, "direccion": "B", "ubicacion": "-26.2, -54.2", "activo": 1},
                {"idconexion": 30, "idcliente": 3, "zona": 1, "direccion": "C", "ubicacion": "-26.3, -54.3", "activo": 1},
                {"idconexion": 40, "idcliente": 4, "zona": 1, "direccion": "D", "ubicacion": "-26.4, -54.4", "activo": 1},
                {"idconexion": 50, "idcliente": 1, "zona": 1, "direccion": "E", "ubicacion": "", "activo": 1},
                {"idconexion": 60, "idcliente": 1, "zona": 1, "direccion": "F", "ubicacion": "999, 999", "activo": 1},
                {"idconexion": 70, "idcliente": 5, "zona": 1, "direccion": "G", "ubicacion": "-26.5, -54.5", "activo": 1},
            ],
            "consumo": [
                {"idconexion": 10, "periodo": 202605, "consumo": 12, "fechatoma": "2026-05-10"},
                {"idconexion": 20, "periodo": 202605, "consumo": 0, "fechatoma": "2026-05-10"},
                {"idconexion": 30, "periodo": 202602, "consumo": 9, "fechatoma": "2026-02-10"},
                {"idconexion": 30, "periodo": 202603, "consumo": 11, "fechatoma": "2026-03-10"},
                {"idconexion": 30, "periodo": 202604, "consumo": 10, "fechatoma": "2026-04-10"},
                {"idconexion": 30, "periodo": 202605, "consumo": 35, "fechatoma": "2026-05-10"},
                {"idconexion": 40, "periodo": 202512, "consumo": 8, "fechatoma": "2025-12-01"},
                {"idconexion": 70, "periodo": 202305, "consumo": 48, "fechatoma": "2023-05-20"},
                {"idconexion": 70, "periodo": 202605, "consumo": 20, "fechatoma": "2026-05-20"},
            ],
        },
        today=date(2026, 5, 29),
    )

    map_data = payload["maps"]["connections"]

    assert map_data["summary"] == {"mapped": 5, "missing_location": 1, "invalid_location": 1}
    statuses = {point["idconexion"]: point["status"] for point in map_data["points"]}
    assert statuses == {10: "normal", 20: "zero", 30: "jump", 40: "stale", 70: "normal"}
    point = map_data["points"][0]
    assert point["lat"] == -26.1
    assert point["lng"] == -54.1
    assert point["cliente"] == "Normal"
    assert point["ultimo_periodo"] == "2026-05"
    assert point["ultimo_consumo"] == 12.0
    assert point["ultima_fecha_toma"] == "2026-05-10"
    jump_point = next(point for point in map_data["points"] if point["idconexion"] == 30)
    assert jump_point["status_reason"] == "Salto anormal: la ultima lectura se aparta de la media historica de la conexion."
    assert jump_point["salto_consumo"] == {
        "idconexion": 30,
        "periodo": "2026-05",
        "consumo_actual": 35.0,
        "media_historica": 10.0,
        "variacion": 25.0,
        "direccion": "suba",
        "muestras_historicas": 3,
    }
