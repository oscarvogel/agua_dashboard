# Mapa De Conexiones Consumo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first consumption map inside the `Consumos` view while keeping the payload shape ready for a future full `Mapa` section with layers.

**Architecture:** Add map-ready connection points to the existing dashboard summary payload under `maps.connections`. Keep parsing and classification in backend metrics so the frontend only renders points and status labels. Add a focused Vue component for Leaflet so the current large `App.vue` only wires data into the new panel.

**Tech Stack:** Django REST Framework, Python metrics functions, pytest, Vue 3, Vite, Leaflet, OpenStreetMap tiles.

---

## File Structure

- Modify `backend/dashboard_api/metrics.py`: add coordinate parsing, latest-consumption point construction, and attach `maps.connections` to the payload.
- Modify `backend/tests/test_dashboard_metrics.py`: add tests for coordinate parsing, status classification, and summary counts.
- Modify `frontend/package.json` and `frontend/package-lock.json`: add `leaflet`.
- Create `frontend/src/ConnectionsMap.vue`: render Leaflet map, markers, legend, summary, empty state.
- Modify `frontend/src/App.vue`: import `ConnectionsMap`, pass `dashboard.maps.connections`, and place the map in the `Consumos` view.
- Modify `frontend/src/styles.css`: add map panel and marker styles.

## Task 1: Backend Map Payload

**Files:**
- Modify: `backend/dashboard_api/metrics.py`
- Test: `backend/tests/test_dashboard_metrics.py`

- [ ] **Step 1: Write failing tests**

Add tests that assert valid `lat,lng` parsing, invalid coordinate counting, and status priority.

```python
def test_connection_map_points_parse_locations_and_classify_statuses():
    payload = build_dashboard_payload(
        {
            "clientes": [
                {"idcliente": 1, "nombre": "Normal"},
                {"idcliente": 2, "nombre": "Cero"},
                {"idcliente": 3, "nombre": "Salto"},
                {"idcliente": 4, "nombre": "Sin Lectura"},
            ],
            "conexiones": [
                {"idconexion": 10, "idcliente": 1, "zona": 1, "direccion": "A", "ubicacion": "-26.1, -54.1", "activo": 1},
                {"idconexion": 20, "idcliente": 2, "zona": 1, "direccion": "B", "ubicacion": "-26.2, -54.2", "activo": 1},
                {"idconexion": 30, "idcliente": 3, "zona": 1, "direccion": "C", "ubicacion": "-26.3, -54.3", "activo": 1},
                {"idconexion": 40, "idcliente": 4, "zona": 1, "direccion": "D", "ubicacion": "-26.4, -54.4", "activo": 1},
                {"idconexion": 50, "idcliente": 1, "zona": 1, "direccion": "E", "ubicacion": "", "activo": 1},
                {"idconexion": 60, "idcliente": 1, "zona": 1, "direccion": "F", "ubicacion": "999, 999", "activo": 1},
            ],
            "consumo": [
                {"idconexion": 10, "periodo": 202605, "consumo": 12, "fechatoma": "2026-05-10"},
                {"idconexion": 20, "periodo": 202605, "consumo": 0, "fechatoma": "2026-05-10"},
                {"idconexion": 30, "periodo": 202604, "consumo": 10, "fechatoma": "2026-04-10"},
                {"idconexion": 30, "periodo": 202605, "consumo": 35, "fechatoma": "2026-05-10"},
                {"idconexion": 40, "periodo": 202512, "consumo": 8, "fechatoma": "2025-12-01"},
            ],
        },
        today=date(2026, 5, 29),
    )

    map_data = payload["maps"]["connections"]

    assert map_data["summary"] == {"mapped": 4, "missing_location": 1, "invalid_location": 1}
    statuses = {point["idconexion"]: point["status"] for point in map_data["points"]}
    assert statuses == {10: "normal", 20: "zero", 30: "jump", 40: "stale"}
    point = map_data["points"][0]
    assert point["lat"] == -26.1
    assert point["lng"] == -54.1
    assert point["cliente"] == "Normal"
    assert point["ultimo_periodo"] == "2026-05"
    assert point["ultimo_consumo"] == 12.0
    assert point["ultima_fecha_toma"] == "2026-05-10"
```

- [ ] **Step 2: Run the failing test**

Run: `py -3 -m pytest backend/tests/test_dashboard_metrics.py::test_connection_map_points_parse_locations_and_classify_statuses -v`

Expected: fail with `KeyError: 'maps'`.

- [ ] **Step 3: Implement backend helpers and payload**

In `backend/dashboard_api/metrics.py`, add a helper near the existing utility functions:

```python
def parse_location(value: Any) -> tuple[float, float] | None:
    text = str(value or "").strip()
    if not text or "," not in text:
        return None
    parts = [part.strip() for part in text.split(",", 1)]
    try:
        lat = float(parts[0])
        lng = float(parts[1])
    except ValueError:
        return None
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None
    return lat, lng
```

Inside `build_dashboard_payload`, after `consumption_jumps` is built, create map points:

```python
    jump_connection_ids = {row["idconexion"] for row in consumption_jumps}
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
            latest_consumption_by_connection[connection_id] = {"row": row, "period": label, "taken_at": taken_at, "sort_key": sort_key}

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
        if connection_id in jump_connection_ids:
            map_status = "jump"
        elif connection_id not in recent_connection_ids:
            map_status = "stale"
        elif latest_row and latest_consumption_amount == 0:
            map_status = "zero"
        else:
            map_status = "normal"
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
            }
        )
```

Then add the payload key:

```python
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
```

- [ ] **Step 4: Run backend tests**

Run: `py -3 -m pytest backend/tests/test_dashboard_metrics.py -v`

Expected: all tests pass.

## Task 2: Leaflet Component

**Files:**
- Create: `frontend/src/ConnectionsMap.vue`
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`

- [ ] **Step 1: Install Leaflet**

Run: `npm install leaflet` from `frontend`.

Expected: `leaflet` appears in `dependencies`, and `package-lock.json` is updated.

- [ ] **Step 2: Create the component**

Create `frontend/src/ConnectionsMap.vue` with props for the map payload, Leaflet initialization, marker rendering, status colors, popup content, and cleanup on unmount.

```vue
<template>
  <article class="panel connection-map-panel">
    <div class="panel-header">
      <div>
        <h2>Mapa de conexiones</h2>
        <p>Ultimo consumo geolocalizado por conexion.</p>
      </div>
      <div class="map-summary">
        <strong>{{ formatNumber(summary.mapped) }}</strong>
        <span>mapeadas</span>
      </div>
    </div>
    <div class="map-legend" aria-label="Estados del mapa">
      <span v-for="item in legendItems" :key="item.status"><i :class="`map-dot ${item.status}`"></i>{{ item.label }}</span>
    </div>
    <div v-if="points.length" ref="mapElement" class="connections-map" aria-label="Mapa de conexiones"></div>
    <div v-else class="map-empty-state">
      <strong>Sin conexiones geolocalizadas para este filtro.</strong>
      <span>{{ formatNumber(summary.missing_location || 0) }} sin ubicacion · {{ formatNumber(summary.invalid_location || 0) }} invalidas</span>
    </div>
  </article>
</template>
```

- [ ] **Step 3: Run frontend build to expose component errors**

Run: `npm run build` from `frontend`.

Expected: fail until script/style code is complete.

## Task 3: Wire Map Into Consumos

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Import and render the component**

In `App.vue`, import `ConnectionsMap` and insert it at the top of the consumption view:

```javascript
import ConnectionsMap from "./ConnectionsMap.vue";
```

```vue
<ConnectionsMap
  :data="dashboard.maps?.connections"
  :format-number="formatNumber"
/>
```

- [ ] **Step 2: Add map styles**

In `frontend/src/styles.css`, add styles for `.connection-map-panel`, `.connections-map`, `.map-legend`, `.map-dot`, and `.map-empty-state`. Marker colors must include normal blue, zero amber, stale gray, and jump red.

- [ ] **Step 3: Run frontend build**

Run: `npm run build` from `frontend`.

Expected: build succeeds.

## Task 4: Final Verification

**Files:**
- No code files unless verification reveals a bug.

- [ ] **Step 1: Run backend tests**

Run: `py -3 -m pytest backend/tests/test_dashboard_metrics.py -v`

Expected: all tests pass.

- [ ] **Step 2: Run frontend build**

Run: `npm run build` from `frontend`.

Expected: build succeeds.

- [ ] **Step 3: Smoke the local UI**

Start backend and frontend if needed, open the app, log in, go to `Consumos`, and confirm:

- the map panel renders above the monthly consumption table;
- markers appear for real coordinates;
- marker popups show connection, client, address, zone, consumption, period, and date;
- legend colors match statuses;
- the page still works when filters change.
