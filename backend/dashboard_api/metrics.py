from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any


INVALID_DATE_SENTINELS = {"", "0000-00-00", "0000-00-00 00:00:00", None}
MAX_REASONABLE_YEAR = 2035


def normalize_date(value: Any) -> date | None:
    if value in INVALID_DATE_SENTINELS:
        return None
    if isinstance(value, datetime):
        parsed = value.date()
    elif isinstance(value, date):
        parsed = value
    else:
        text = str(value).strip()
        try:
            parsed = datetime.fromisoformat(text[:10]).date()
        except ValueError:
            return None
    if parsed.year > MAX_REASONABLE_YEAR:
        return None
    return parsed


def money(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def is_active(value: Any) -> bool:
    return str(value).strip().lower() not in {"0", "false", "n", "no", "inactivo", "baja", ""}


def invoice_total(row: dict[str, Any]) -> Decimal:
    return money(row.get("neto")) + money(row.get("iva")) + money(row.get("dgr"))


def first_value(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row and row.get(key) not in {None, ""}:
            return row.get(key)
    lowered = {str(key).lower(): value for key, value in row.items()}
    for key in keys:
        value = lowered.get(key.lower())
        if value not in {None, ""}:
            return value
    return None


def parse_location(value: Any) -> tuple[float, float] | None:
    text = str(value or "").strip()
    if not text or "," not in text:
        return None
    left, right = [part.strip() for part in text.split(",", 1)]
    try:
        lat = float(left)
        lng = float(right)
    except ValueError:
        return None
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None
    return lat, lng


def ym(value: date | None) -> str | None:
    return value.strftime("%Y-%m") if value else None


def ymd(value: date | None) -> str | None:
    return value.strftime("%Y-%m-%d") if value else None


def period_ym(value: Any) -> str | None:
    text = str(value or "").strip()
    if len(text) == 6 and text.isdigit():
        return f"{text[:4]}-{text[4:]}"
    return None


def ids_with_zone(rows: list[dict[str, Any]], id_key: str, zone: str) -> set[Any]:
    if not zone:
        return {row.get(id_key) for row in rows}
    return {row.get(id_key) for row in rows if str(row.get("zona", "")).strip() == zone}


def apply_scope(rows: dict[str, list[dict[str, Any]]], zone: str = "", status_filter: str = "todos") -> dict[str, list[dict[str, Any]]]:
    scoped = {key: list(value) for key, value in rows.items()}
    if zone:
        scoped["clientes"] = [row for row in scoped.get("clientes", []) if str(row.get("zona", "")).strip() == zone]
        scoped["conexiones"] = [row for row in scoped.get("conexiones", []) if str(row.get("zona", "")).strip() == zone]

    if status_filter == "activos":
        scoped["clientes"] = [row for row in scoped.get("clientes", []) if is_active(row.get("activo", 1))]
        scoped["conexiones"] = [row for row in scoped.get("conexiones", []) if is_active(row.get("activo", 1))]
    elif status_filter == "inactivos":
        scoped["clientes"] = [row for row in scoped.get("clientes", []) if not is_active(row.get("activo", 1))]
        scoped["conexiones"] = [row for row in scoped.get("conexiones", []) if not is_active(row.get("activo", 1))]

    client_ids = {row.get("idcliente") for row in scoped.get("clientes", [])}
    connection_ids = {row.get("idconexion") for row in scoped.get("conexiones", [])}
    if zone or status_filter != "todos":
        scoped["cabfact"] = [
            row
            for row in scoped.get("cabfact", [])
            if row.get("idcliente") in client_ids or row.get("idconexion") in connection_ids
        ]
        invoice_ids = {row.get("IdCabFact") for row in scoped.get("cabfact", [])}
        scoped["ctacte"] = [
            row
            for row in scoped.get("ctacte", [])
            if row.get("idFactura") in invoice_ids or row.get("idcliente") in client_ids
        ]
        scoped["consumo"] = [row for row in scoped.get("consumo", []) if row.get("idconexion") in connection_ids]
        scoped["pendfact"] = [
            row
            for row in scoped.get("pendfact", [])
            if row.get("idcliente") in client_ids or row.get("idconexion") in connection_ids
        ]
    return scoped


def selected_period_labels(labels: list[str], current_month_key: str, period: str, periods: list[str] | None = None) -> list[str]:
    if not labels:
        return [current_month_key]
    selected = [value for value in periods or [] if value in labels]
    if selected:
        return selected
    if period == "trim":
        return labels[-3:]
    if period == "year":
        return labels[-12:]
    if current_month_key in labels:
        return [current_month_key]
    return [labels[-1]]


def aging_bucket(due_at: date | None, today: date) -> str:
    if not due_at:
        return "Sin vencimiento"
    days = (today - due_at).days
    if days <= 0:
        return "No vencida"
    if days <= 30:
        return "1-30 dias"
    if days <= 60:
        return "31-60 dias"
    if days <= 90:
        return "61-90 dias"
    return "Mas de 90 dias"


def sorted_amount_rows(values: dict[str, Decimal], label_key: str = "label", amount_key: str = "importe", limit: int | None = None) -> list[dict[str, Any]]:
    rows = [
        {label_key: label, amount_key: float(amount)}
        for label, amount in values.items()
        if amount != 0
    ]
    rows.sort(key=lambda row: row[amount_key], reverse=True)
    return rows[:limit] if limit else rows


def average(numerator: Decimal, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator / Decimal(denominator))


def percentage(numerator: Decimal, denominator: Decimal) -> float:
    if denominator <= 0:
        return 0.0
    return round(float((numerator / denominator) * Decimal("100")), 2)


def build_dashboard_payload(
    rows: dict[str, list[dict[str, Any]]],
    today: date | None = None,
    period: str = "actual",
    periods: list[str] | None = None,
    zone: str = "",
    status_filter: str = "todos",
) -> dict[str, Any]:
    today = today or date.today()
    current_month_key = today.strftime("%Y-%m")
    recent_threshold = today - timedelta(days=90)
    recent_payment_threshold = today - timedelta(days=30)
    rows = apply_scope(rows, zone=zone, status_filter=status_filter)
    zone_options = sorted(
        {
            str(row.get("zona"))
            for row in rows.get("conexiones", []) + rows.get("clientes", [])
            if row.get("zona") not in {None, ""}
        },
        key=lambda value: (not value.isdigit(), value),
    )

    clientes = rows.get("clientes", [])
    conexiones = rows.get("conexiones", [])
    facturas = rows.get("cabfact", [])
    detalles = rows.get("detfact", [])
    conceptos = rows.get("conceptos", [])
    movimientos = rows.get("movcaja", [])
    cta = rows.get("ctacte", [])
    consumos = rows.get("consumo", [])
    pendientes = rows.get("pendfact", [])

    clientes_by_id = {row.get("idcliente"): row for row in clientes}
    connection_by_id = {row.get("idconexion"): row for row in conexiones}
    concept_names = {
        first_value(row, "idconcepto", "IdConcepto", "codigo", "Codigo"): (
            str(first_value(row, "descripcion", "Descripcion", "nombre", "Nombre", "detalle", "Detalle") or "").strip()
            or f"Concepto {first_value(row, 'idconcepto', 'IdConcepto', 'codigo', 'Codigo')}"
        )
        for row in conceptos
    }
    active_clients = sum(1 for row in clientes if is_active(row.get("activo", 1)))
    active_connections = sum(1 for row in conexiones if is_active(row.get("activo", 1)))
    missing_locations = sum(1 for row in conexiones if not str(first_value(row, "ubicacion", "latitud", "Latitud", "gps", "GPS") or "").strip())
    clients_by_zone: dict[str, int] = defaultdict(int)
    connections_by_zone: dict[str, int] = defaultdict(int)
    registry_status_by_zone: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    new_connections_by_period: dict[str, int] = defaultdict(int)
    for row in clientes:
        zone_label = str(first_value(row, "zona", "Zona") or "Sin zona")
        clients_by_zone[zone_label] += 1
        registry_status_by_zone[zone_label]["clientes_activos" if is_active(row.get("activo", 1)) else "clientes_inactivos"] += 1
    for row in conexiones:
        zone_label = str(first_value(row, "zona", "Zona") or "Sin zona")
        connections_by_zone[zone_label] += 1
        registry_status_by_zone[zone_label]["conexiones_activas" if is_active(row.get("activo", 1)) else "conexiones_inactivas"] += 1
        entry_period = ym(normalize_date(row.get("fechaingreso")))
        if entry_period:
            new_connections_by_period[entry_period] += 1

    monthly_billing: dict[str, Decimal] = defaultdict(Decimal)
    daily_billing: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    debt_by_client: dict[Any, Decimal] = defaultdict(Decimal)
    overdue_by_client: dict[Any, Decimal] = defaultdict(Decimal)
    invoice_client: dict[Any, Any] = {}
    invoice_connection: dict[Any, Any] = {}
    invoice_due: dict[Any, date | None] = {}
    doubtful_documents: dict[tuple[str, str], int] = defaultdict(int)

    for row in facturas:
        issued_at = normalize_date(row.get("fechaem"))
        invoice_id = row.get("IdCabFact")
        client_id = row.get("idcliente")
        connection_id = row.get("idconexion")
        invoice_client[invoice_id] = client_id
        invoice_connection[invoice_id] = connection_id
        total = invoice_total(row)
        invoice_state = str(row.get("estado", "0")).strip()
        if invoice_state not in {"0", "", "None"}:
            doubtful_documents[("factura", invoice_state)] += 1
        if issued_at:
            month_label = ym(issued_at) or ""
            day_label = ymd(issued_at) or ""
            monthly_billing[month_label] += total
            daily_billing[month_label][day_label] += total
        due_at = normalize_date(row.get("fechaven"))
        invoice_due[invoice_id] = due_at
        if due_at and due_at < today:
            overdue_by_client[client_id] += total

    billing_by_concept: dict[str, Decimal] = defaultdict(Decimal)
    for row in detalles:
        invoice_id = first_value(row, "IdCabFact", "idcabfact", "idFactura", "idfactura")
        if invoice_id not in invoice_client:
            continue
        concept_id = first_value(row, "idconcepto", "IdConcepto", "concepto", "Concepto")
        concept_name = str(concept_names.get(concept_id) or f"Concepto {concept_id or 'sin identificar'}")
        billing_by_concept[concept_name] += invoice_total(row)

    monthly_collections: dict[str, Decimal] = defaultdict(Decimal)
    daily_collections: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    collections_by_day_client: dict[str, dict[Any, dict[str, Any]]] = defaultdict(
        lambda: defaultdict(lambda: {"importe": Decimal("0"), "movimientos": 0, "comprobantes": []})
    )
    recent_payments_by_client: dict[Any, dict[str, Any]] = {}
    collections_by_client: dict[Any, Decimal] = defaultdict(Decimal)
    current_collection_movements_by_client: dict[Any, int] = defaultdict(int)
    last_payment_by_client: dict[Any, dict[str, Any]] = {}
    for row in movimientos:
        movement_state = str(row.get("estado", "0")).strip()
        if movement_state not in {"0", "", "None"}:
            doubtful_documents[("movcaja", movement_state)] += 1
            continue
        paid_at = normalize_date(row.get("Fecha"))
        if paid_at:
            month_label = ym(paid_at) or ""
            day_label = ymd(paid_at) or ""
            amount = money(row.get("importe"))
            client_id = first_value(row, "idCliente", "idcliente", "IdCliente")
            monthly_collections[month_label] += amount
            daily_collections[month_label][day_label] += amount
            collections_by_client[client_id] += amount
            detail = collections_by_day_client[day_label][client_id]
            detail["importe"] += amount
            detail["movimientos"] += 1
            receipt = first_value(row, "numcomp", "NumComp", "idMovCaja", "IdMovCaja")
            if receipt not in {None, ""}:
                detail["comprobantes"].append(str(receipt))
            current = last_payment_by_client.get(client_id)
            if client_id is not None and (not current or paid_at > current["date"]):
                last_payment_by_client[client_id] = {"date": paid_at, "amount": amount}
            if paid_at >= recent_payment_threshold:
                recent = recent_payments_by_client.get(client_id)
                if client_id is not None and (not recent or paid_at > recent["date"]):
                    recent_payments_by_client[client_id] = {"date": paid_at, "amount": amount}

    debt_by_zone: dict[str, Decimal] = defaultdict(Decimal)
    overdue_by_zone: dict[str, Decimal] = defaultdict(Decimal)
    debt_aging: dict[str, Decimal] = defaultdict(Decimal)
    for row in cta:
        invoice_id = row.get("idFactura")
        client_id = invoice_client.get(invoice_id) or row.get("idcliente")
        amount = money(row.get("Monto"))
        debt_by_client[client_id] += money(row.get("Monto"))
        if amount <= 0:
            continue
        client = clientes_by_id.get(client_id, {})
        connection = connection_by_id.get(invoice_connection.get(invoice_id), {})
        zone_label = str(first_value(connection, "zona", "Zona") or first_value(client, "zona", "Zona") or "Sin zona")
        debt_by_zone[zone_label] += amount
        if aging_bucket(invoice_due.get(invoice_id), today) not in {"No vencida", "Sin vencimiento"}:
            overdue_by_zone[zone_label] += amount
        debt_aging[aging_bucket(invoice_due.get(invoice_id), today)] += amount

    latest_period = max((row.get("periodo") for row in consumos if row.get("periodo") is not None), default=None)
    latest_consumption = sum(money(row.get("consumo")) for row in consumos if row.get("periodo") == latest_period)
    zero_consumption = sum(1 for row in consumos if row.get("periodo") == latest_period and money(row.get("consumo")) == 0)
    monthly_consumption: dict[str, Decimal] = defaultdict(Decimal)
    daily_consumption: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    consumption_by_zone: dict[str, Decimal] = defaultdict(Decimal)
    consumption_history: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in consumos:
        taken_at = normalize_date(row.get("fechatoma"))
        label = period_ym(row.get("periodo")) or ym(taken_at)
        day_label = ymd(taken_at)
        consumption_amount = money(row.get("consumo"))
        if label:
            monthly_consumption[label] += consumption_amount
            consumption_history[row.get("idconexion")].append(
                {
                    "row": row,
                    "period": label,
                    "taken_at": taken_at,
                    "amount": consumption_amount,
                    "sort_key": (label, taken_at or date.min),
                }
            )
        if label and day_label:
            daily_consumption[label][day_label] += consumption_amount
        if row.get("periodo") == latest_period:
            connection = connection_by_id.get(row.get("idconexion"), {})
            zone_label = str(first_value(connection, "zona", "Zona") or "Sin zona")
            consumption_by_zone[zone_label] += consumption_amount
    recent_connection_ids = {
        row.get("idconexion")
        for row in consumos
        if (normalize_date(row.get("fechatoma")) or date.min) >= recent_threshold
    }
    stale_connections = sum(1 for row in conexiones if row.get("idconexion") not in recent_connection_ids)
    consumed_connection_ids = {row.get("idconexion") for row in consumos if row.get("idconexion") is not None}
    connections_without_consumption = sum(1 for row in conexiones if row.get("idconexion") not in consumed_connection_ids)

    pending_total = Decimal("0")
    pending_by_period: dict[str, Decimal] = defaultdict(Decimal)
    pending_by_concept: dict[str, Decimal] = defaultdict(Decimal)
    pending_by_connection: dict[tuple[Any, Any], dict[str, Any]] = defaultdict(lambda: {"count": 0, "amount": Decimal("0")})
    for row in pendientes:
        if str(row.get("facturado", "0")).strip() not in {"0", "", "None"}:
            continue
        total = invoice_total(row)
        pending_total += total
        pending_key = (row.get("idcliente"), row.get("idconexion"))
        pending_by_connection[pending_key]["count"] += 1
        pending_by_connection[pending_key]["amount"] += total
        period_label = period_ym(row.get("periodo")) or "Sin periodo"
        pending_by_period[period_label] += total
        concept_id = first_value(row, "idconcepto", "IdConcepto", "concepto", "Concepto")
        concept_name = str(concept_names.get(concept_id) or f"Concepto {concept_id or 'sin identificar'}")
        pending_by_concept[concept_name] += total
    debt_total = sum((amount for amount in debt_by_client.values()), Decimal("0"))
    overdue_total = Decimal("0")
    for client_id, gross_overdue in overdue_by_client.items():
        current_debt = debt_by_client.get(client_id, Decimal("0"))
        if current_debt > 0:
            overdue_total += min(gross_overdue, current_debt)
    debt_total = max(debt_total, Decimal("0"))
    overdue_total = min(overdue_total, debt_total)
    total_billing = sum(monthly_billing.values(), Decimal("0"))

    monthly_labels = sorted(set(monthly_billing) | set(monthly_collections) | set(monthly_consumption))[-12:]
    visible_period_labels = selected_period_labels(monthly_labels, current_month_key, period, periods)
    visible_collections = sum((monthly_collections.get(label, Decimal("0")) for label in visible_period_labels), Decimal("0"))
    previous_period_label = ""
    if visible_period_labels:
        all_collection_labels = sorted(set(monthly_labels) | set(monthly_collections))
        try:
            first_visible_index = all_collection_labels.index(visible_period_labels[0])
        except ValueError:
            first_visible_index = -1
        if first_visible_index > 0:
            previous_period_label = all_collection_labels[first_visible_index - 1]
    previous_collections = monthly_collections.get(previous_period_label, Decimal("0"))

    visible_days = sorted(
        day
        for month_label in visible_period_labels
        for day in daily_collections.get(month_label, {})
    )
    visible_day_count = len(visible_days) or 1
    accumulated = Decimal("0")
    daily_performance = []
    for index, day_label in enumerate(visible_days, start=1):
        day_amount = Decimal("0")
        for month_label in visible_period_labels:
            day_amount += daily_collections.get(month_label, {}).get(day_label, Decimal("0"))
        accumulated += day_amount
        expected = visible_collections * Decimal(index) / Decimal(visible_day_count)
        day_clients = collections_by_day_client.get(day_label, {})
        daily_performance.append(
            {
                "fecha": day_label,
                "collected": float(day_amount),
                "accumulated": float(accumulated),
                "expected_accumulated": round(float(expected), 2),
                "movement_count": sum(value["movimientos"] for value in day_clients.values()),
                "client_count": sum(1 for value in day_clients.values() if value["importe"] != 0),
            }
        )

    visible_period_set = set(visible_period_labels)
    collections_by_zone: dict[str, Decimal] = defaultdict(Decimal)
    paying_clients_by_zone: dict[str, set[Any]] = defaultdict(set)
    current_collections_by_client: dict[Any, Decimal] = defaultdict(Decimal)
    for day_label, day_values in collections_by_day_client.items():
        month_label = day_label[:7]
        if month_label not in visible_period_set:
            continue
        for client_id, value in day_values.items():
            amount = value["importe"]
            current_collections_by_client[client_id] += amount
            current_collection_movements_by_client[client_id] += value["movimientos"]
            client = clientes_by_id.get(client_id, {})
            zone_label = str(first_value(client, "zona", "Zona") or "Sin zona")
            collections_by_zone[zone_label] += amount
            if amount != 0:
                paying_clients_by_zone[zone_label].add(client_id)

    zone_efficiency = []
    for zone_label in sorted(set(collections_by_zone) | set(debt_by_zone) | set(overdue_by_zone), key=lambda value: (value == "Sin zona", value)):
        collected = collections_by_zone.get(zone_label, Decimal("0"))
        zone_debt = debt_by_zone.get(zone_label, Decimal("0"))
        zone_overdue = overdue_by_zone.get(zone_label, Decimal("0"))
        zone_efficiency.append(
            {
                "zona": zone_label,
                "collected": float(collected),
                "debt_total": float(zone_debt),
                "overdue_debt": float(zone_overdue),
                "paying_clients": len(paying_clients_by_zone.get(zone_label, set())),
                "recovery_rate": percentage(collected, zone_overdue or zone_debt),
            }
        )
    zone_efficiency.sort(key=lambda row: (row["overdue_debt"], row["debt_total"]), reverse=True)

    last_7_days = sum(
        (
            value["importe"]
            for day_label, day_values in collections_by_day_client.items()
            if (normalize_date(day_label) or date.min) >= today - timedelta(days=7)
            for value in day_values.values()
        ),
        Decimal("0"),
    )
    paying_clients = {client_id for client_id, amount in current_collections_by_client.items() if client_id is not None and amount != 0}
    recovery_rate = percentage(visible_collections, overdue_total)
    if recovery_rate >= 15 or (previous_collections > 0 and visible_collections >= previous_collections):
        collection_status = "good"
    elif recovery_rate >= 7:
        collection_status = "normal"
    else:
        collection_status = "low"

    followup = []
    for client_id, debt_amount in debt_by_client.items():
        if client_id not in clientes_by_id or debt_amount <= 0:
            continue
        client = clientes_by_id.get(client_id, {})
        overdue_amount = min(overdue_by_client.get(client_id, Decimal("0")), debt_amount)
        last_payment = last_payment_by_client.get(client_id)
        days_since_payment = (today - last_payment["date"]).days if last_payment else None
        recent_paid = last_payment is not None and days_since_payment is not None and days_since_payment <= 30
        if overdue_amount > 0 and not recent_paid:
            action = "Llamar"
            risk = "alto"
            risk_score = 90
        elif overdue_amount > 0 and recent_paid:
            action = "Seguimiento normal"
            risk = "medio"
            risk_score = 60
        elif current_collections_by_client.get(client_id, Decimal("0")) < 0:
            action = "Revisar"
            risk = "medio"
            risk_score = 50
        else:
            action = "Sin accion"
            risk = "bajo"
            risk_score = 20
        followup.append(
            {
                "cliente": client.get("nombre") or f"Cliente {client_id}",
                "idcliente": client_id,
                "zona": str(first_value(client, "zona", "Zona") or "Sin zona"),
                "deuda_total": float(debt_amount),
                "deuda_vencida": float(overdue_amount),
                "ultimo_pago": ymd(last_payment["date"]) if last_payment else None,
                "ultimo_pago_importe": float(last_payment["amount"]) if last_payment else 0.0,
                "dias_sin_pagar": days_since_payment,
                "movimientos_periodo": current_collection_movements_by_client.get(client_id, 0),
                "riesgo": risk,
                "riesgo_score": risk_score,
                "accion_sugerida": action,
            }
        )
    followup.sort(key=lambda row: (row["riesgo_score"], row["deuda_vencida"], row["deuda_total"]), reverse=True)

    collected_by_client_visible = sorted(
        (amount for amount in current_collections_by_client.values() if amount > 0),
        reverse=True,
    )
    top_10_collected = sum(collected_by_client_visible[:10], Decimal("0"))
    collections_concentration = {
        "top_10_collected": float(top_10_collected),
        "total_collected": float(visible_collections),
        "top_10_share": percentage(top_10_collected, visible_collections),
    }

    top_debtors = []
    positive_debts = ((client_id, amount) for client_id, amount in debt_by_client.items() if amount > 0)
    for client_id, amount in sorted(positive_debts, key=lambda item: item[1], reverse=True):
        if client_id not in clientes_by_id:
            continue
        client = clientes_by_id.get(client_id, {})
        top_debtors.append(
            {
                "cliente": client.get("nombre") or f"Cliente {client_id or 'sin identificar'}",
                "idcliente": client_id,
                "deuda": float(amount),
            }
        )
        if len(top_debtors) >= 8:
            break
    recurrent_debt_clients = {
        client_id
        for client_id, count in (
            (client_id, sum(1 for row in facturas if row.get("idcliente") == client_id and debt_by_client.get(client_id, Decimal("0")) > 0))
            for client_id in debt_by_client
        )
        if count >= 2
    }

    daily_labels = sorted(set(daily_billing) | set(daily_collections) | set(daily_consumption))
    latest_consumption_by_connection: dict[Any, dict[str, Any]] = {}
    for row in consumos:
        connection_id = row.get("idconexion")
        if connection_id is None:
            continue
        label = period_ym(row.get("periodo")) or ym(normalize_date(row.get("fechatoma")))
        taken_at = normalize_date(row.get("fechatoma"))
        sort_key = (label or "", taken_at or date.min)
        current = latest_consumption_by_connection.get(connection_id)
        if not current or sort_key > current["sort_key"]:
            latest_consumption_by_connection[connection_id] = {
                "row": row,
                "period": label,
                "taken_at": taken_at,
                "sort_key": sort_key,
            }

    consumption_jumps = []
    for connection_id, latest in latest_consumption_by_connection.items():
        history = consumption_history.get(connection_id, [])
        historical_amounts = [
            record["amount"]
            for record in history
            if record.get("row") is not latest["row"] and record.get("amount") is not None
        ]
        if len(historical_amounts) < 3:
            continue
        historical_average = sum(historical_amounts, Decimal("0")) / Decimal(len(historical_amounts))
        if historical_average <= 0:
            continue
        current_amount = money(latest["row"].get("consumo"))
        variation = current_amount - historical_average
        absolute_variation = abs(variation)
        is_high = current_amount >= historical_average * Decimal("2")
        is_low = current_amount <= historical_average * Decimal("0.5")
        if absolute_variation >= Decimal("15") and (is_high or is_low):
            consumption_jumps.append(
                {
                    "idconexion": connection_id,
                    "periodo": latest["period"],
                    "consumo_actual": float(current_amount),
                    "media_historica": round(float(historical_average), 2),
                    "variacion": round(float(variation), 2),
                    "direccion": "suba" if variation > 0 else "baja",
                    "muestras_historicas": len(historical_amounts),
                }
            )
    consumption_jumps.sort(key=lambda row: abs(row["variacion"]), reverse=True)
    jump_connection_ids = {row["idconexion"] for row in consumption_jumps}
    jump_by_connection = {row["idconexion"]: row for row in consumption_jumps}

    connection_map_points = []
    missing_map_locations = 0
    invalid_map_locations = 0
    for connection in conexiones:
        raw_location = first_value(connection, "ubicacion", "latitud", "Latitud", "gps", "GPS")
        if not str(raw_location or "").strip():
            missing_map_locations += 1
            continue
        parsed_location = parse_location(raw_location)
        if not parsed_location:
            invalid_map_locations += 1
            continue
        connection_id = connection.get("idconexion")
        latest = latest_consumption_by_connection.get(connection_id)
        latest_row = latest["row"] if latest else {}
        latest_taken_at = latest["taken_at"] if latest else None
        latest_period_label = latest["period"] if latest else None
        latest_consumption_amount = money(latest_row.get("consumo")) if latest_row else Decimal("0")
        jump_detail = jump_by_connection.get(connection_id)
        if connection_id in jump_connection_ids:
            map_status = "jump"
            status_reason = "Salto anormal: la ultima lectura se aparta de la media historica de la conexion."
        elif connection_id not in recent_connection_ids:
            map_status = "stale"
            status_reason = "Sin lectura reciente para el periodo visible."
        elif latest_row and latest_consumption_amount == 0:
            map_status = "zero"
            status_reason = "La ultima lectura registrada tiene consumo cero."
        else:
            map_status = "normal"
            status_reason = "Lectura dentro de los parametros esperados."
        client = clientes_by_id.get(connection.get("idcliente"), {})
        lat, lng = parsed_location
        connection_map_points.append(
            {
                "idconexion": connection_id,
                "idcliente": connection.get("idcliente"),
                "cliente": client.get("nombre") or f"Cliente {connection.get('idcliente') or 'sin identificar'}",
                "direccion": str(first_value(connection, "direccion", "Direccion") or "").strip(),
                "zona": str(first_value(connection, "zona", "Zona") or "Sin zona"),
                "lat": lat,
                "lng": lng,
                "ultimo_periodo": latest_period_label,
                "ultimo_consumo": float(latest_consumption_amount),
                "ultima_fecha_toma": ymd(latest_taken_at),
                "status": map_status,
                "status_reason": status_reason,
                "salto_consumo": jump_detail,
            }
        )

    repeated_pending = []
    for (client_id, connection_id), value in pending_by_connection.items():
        if value["count"] < 2:
            continue
        repeated_pending.append(
            {
                "cliente": clientes_by_id.get(client_id, {}).get("nombre") or f"Cliente {client_id}",
                "idcliente": client_id,
                "idconexion": connection_id,
                "pendientes": value["count"],
                "importe": float(value["amount"]),
            }
        )
    repeated_pending.sort(key=lambda row: row["importe"], reverse=True)
    daily_series = {
        month_label: [
            {
                "fecha": day_label,
                "facturacion": float(daily_billing[month_label].get(day_label, Decimal("0"))),
                "cobranzas": float(daily_collections[month_label].get(day_label, Decimal("0"))),
                "consumo": float(daily_consumption[month_label].get(day_label, Decimal("0"))),
            }
            for day_label in sorted(
                set(daily_billing[month_label]) | set(daily_collections[month_label]) | set(daily_consumption[month_label])
            )
        ]
        for month_label in daily_labels
    }

    return {
        "source": {"mode": "computed", "generated_at": datetime.now().isoformat(timespec="seconds")},
        "summary": {
            "clientes_activos": active_clients,
            "conexiones_activas": active_connections,
            "facturacion_mes": float(sum((monthly_billing.get(label, Decimal("0")) for label in visible_period_labels), Decimal("0"))),
            "cobranzas_mes": float(visible_collections),
            "deuda_total": float(debt_total),
            "deuda_vencida": float(overdue_total),
            "consumo_ultimo_periodo": float(latest_consumption),
            "conexiones_sin_lectura_reciente": stale_connections,
            "pendiente_facturacion": float(pending_total),
            "consumos_cero": zero_consumption,
            "importe_promedio_conexion": average(total_billing, active_connections),
            "consumo_promedio_conexion": average(latest_consumption, active_connections),
            "conexiones_sin_ubicacion": missing_locations,
            "comprobantes_estado_dudoso": sum(doubtful_documents.values()),
            "clientes_con_pagos_recientes": len(recent_payments_by_client),
            "conexiones_sin_consumo_registrado": connections_without_consumption,
            "conexiones_con_deuda_recurrente": len(recurrent_debt_clients),
            "saltos_anormales_consumo": len(consumption_jumps),
            "pendientes_repetidos": len(repeated_pending),
        },
        "series": {
            "daily": daily_series,
            "monthly": [
                {
                    "periodo": label,
                    "facturacion": float(monthly_billing.get(label, Decimal("0"))),
                    "cobranzas": float(monthly_collections.get(label, Decimal("0"))),
                    "consumo": float(monthly_consumption.get(label, Decimal("0"))),
                }
                for label in monthly_labels
            ]
        },
        "collections": {
            "health": {
                "period_collected": float(visible_collections),
                "previous_period": previous_period_label,
                "previous_period_collected": float(previous_collections),
                "variation_pct": percentage(visible_collections - previous_collections, previous_collections),
                "last_7_days": float(last_7_days),
                "paying_clients": len(paying_clients),
                "estimated_recovery_rate": recovery_rate,
                "status": collection_status,
            },
            "daily_performance": daily_performance,
            "zone_efficiency": zone_efficiency,
            "followup": followup[:20],
            "concentration": collections_concentration,
        },
        "maps": {
            "connections": {
                "summary": {
                    "mapped": len(connection_map_points),
                    "missing_location": missing_map_locations,
                    "invalid_location": invalid_map_locations,
                },
                "points": connection_map_points,
            }
        },
        "breakdowns": {
            "deuda_antiguedad": [
                {"rango": bucket, "importe": float(debt_aging[bucket])}
                for bucket in ["No vencida", "1-30 dias", "31-60 dias", "61-90 dias", "Mas de 90 dias", "Sin vencimiento"]
                if debt_aging.get(bucket, Decimal("0")) != 0
            ],
            "deuda_zona": sorted_amount_rows(debt_by_zone, label_key="zona", limit=8),
            "facturacion_concepto": sorted_amount_rows(billing_by_concept, label_key="concepto", limit=8),
            "pendientes_periodo": [
                {"periodo": label, "importe": float(amount)}
                for label, amount in sorted(pending_by_period.items())
                if amount != 0
            ],
            "pendientes_concepto": sorted_amount_rows(pending_by_concept, label_key="concepto", limit=8),
            "consumo_zona": [
                {"zona": label, "consumo": float(amount)}
                for label, amount in sorted(consumption_by_zone.items(), key=lambda item: item[0])
                if amount != 0
            ],
            "padron_zona": [
                {
                    "zona": label,
                    "clientes": clients_by_zone.get(label, 0),
                    "conexiones": connections_by_zone.get(label, 0),
                }
                for label in sorted(set(clients_by_zone) | set(connections_by_zone), key=lambda value: (value == "Sin zona", value))
            ],
            "comprobantes_estado": [
                {"tipo": kind, "estado": state, "cantidad": count}
                for (kind, state), count in sorted(doubtful_documents.items(), key=lambda item: (item[0][0], item[0][1]))
            ],
            "padron_estado_zona": [
                {
                    "zona": label,
                    "clientes_activos": registry_status_by_zone[label].get("clientes_activos", 0),
                    "clientes_inactivos": registry_status_by_zone[label].get("clientes_inactivos", 0),
                    "conexiones_activas": registry_status_by_zone[label].get("conexiones_activas", 0),
                    "conexiones_inactivas": registry_status_by_zone[label].get("conexiones_inactivas", 0),
                }
                for label in sorted(registry_status_by_zone, key=lambda value: (value == "Sin zona", value))
            ],
            "altas_periodo": [
                {"periodo": label, "conexiones": count}
                for label, count in sorted(new_connections_by_period.items())
            ],
            "clientes_pagos_recientes": [
                {
                    "cliente": clientes_by_id.get(client_id, {}).get("nombre") or f"Cliente {client_id}",
                    "idcliente": client_id,
                    "importe": float(value["amount"]),
                    "fecha": ymd(value["date"]),
                }
                for client_id, value in sorted(recent_payments_by_client.items(), key=lambda item: item[1]["date"], reverse=True)[:8]
            ],
            "cobranzas_por_dia_socio": {
                day_label: [
                    {
                        "idcliente": client_id,
                        "cliente": clientes_by_id.get(client_id, {}).get("nombre") or f"Socio {client_id or 'sin identificar'}",
                        "importe": float(value["importe"]),
                        "movimientos": value["movimientos"],
                        "comprobantes": value["comprobantes"][:5],
                        "deuda_total": float(max(debt_by_client.get(client_id, Decimal("0")), Decimal("0"))),
                        "deuda_vencida": float(min(overdue_by_client.get(client_id, Decimal("0")), max(debt_by_client.get(client_id, Decimal("0")), Decimal("0")))),
                    }
                    for client_id, value in sorted(day_values.items(), key=lambda item: item[1]["importe"], reverse=True)
                    if value["importe"] != 0
                ]
                for day_label, day_values in sorted(collections_by_day_client.items())
                if day_label[:7] in visible_period_set
            },
            "saltos_consumo": consumption_jumps[:8],
            "pendientes_repetidos": repeated_pending[:8],
        },
        "filters": {
            "zones": zone_options,
            "period": period,
            "periods": visible_period_labels,
            "period_options": monthly_labels,
            "zone": zone,
            "status": status_filter,
        },
        "top_deudores": top_debtors,
        "quality": [
            {"label": "Fechas invalidas normalizadas", "status": "controlado"},
            {"label": "Importes nulos tratados como cero", "status": "controlado"},
            {"label": "Base operativa sin escrituras", "status": "controlado"},
            {"label": f"Periodo aplicado: {', '.join(visible_period_labels)}", "status": "visible"},
            {"label": f"Zona aplicada: {zone or 'todas'}", "status": "visible"},
            {"label": f"Estado aplicado: {status_filter}", "status": "visible"},
        ],
    }
