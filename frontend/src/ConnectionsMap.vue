<template>
  <article class="panel connection-map-panel" :class="{ 'is-fullscreen': isFullscreen }">
    <div class="panel-header">
      <div>
        <h2>Mapa de conexiones</h2>
        <p>Ultimo consumo geolocalizado por conexion.</p>
      </div>
      <div class="map-header-actions">
        <div class="map-summary">
          <strong>{{ formatNumber(filteredPoints.length) }}</strong>
          <span>{{ hasActiveFilters ? "visibles" : "mapeadas" }}</span>
        </div>
        <button
          class="map-tool-button"
          type="button"
          :title="isFullscreen ? 'Salir de pantalla completa' : 'Ver mapa en pantalla completa'"
          @click="toggleFullscreen"
        >
          <Minimize2Icon v-if="isFullscreen" :size="17" />
          <Maximize2Icon v-else :size="17" />
          <span>{{ isFullscreen ? "Salir" : "Ampliar" }}</span>
        </button>
      </div>
    </div>

    <div class="map-control-stack">
      <div class="map-filter" aria-label="Filtrar conexiones por estado">
        <button
          v-for="item in filterItems"
          :key="item.status"
          type="button"
          :class="{ active: activeStatus === item.status }"
          @click="activeStatus = item.status"
        >
          <i v-if="item.status !== 'all'" :class="`map-dot ${item.status}`"></i>
          <span>{{ item.label }}</span>
          <strong>{{ formatNumber(statusCounts[item.status] || 0) }}</strong>
        </button>
      </div>

      <div class="map-filter consumption-filter" aria-label="Filtrar conexiones por consumo">
        <button
          v-for="item in consumptionFilterItems"
          :key="item.range"
          type="button"
          :class="{ active: activeConsumptionRange === item.range }"
          @click="activeConsumptionRange = item.range"
        >
          <span>{{ item.label }}</span>
          <strong>{{ formatNumber(consumptionCounts[item.range] || 0) }}</strong>
        </button>
      </div>
    </div>

    <div v-if="filteredPoints.length" ref="mapElement" class="connections-map" aria-label="Mapa de conexiones"></div>
    <div v-else class="map-empty-state">
      <strong>Sin conexiones geolocalizadas para este filtro.</strong>
      <span>{{ formatNumber(summary.missing_location || 0) }} sin ubicacion · {{ formatNumber(summary.invalid_location || 0) }} invalidas</span>
    </div>
  </article>
</template>

<script setup>
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Maximize2Icon, Minimize2Icon } from "lucide-vue-next";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
  data: {
    type: Object,
    default: () => ({ summary: {}, points: [] }),
  },
  formatNumber: {
    type: Function,
    required: true,
  },
  searchQuery: {
    type: String,
    default: "",
  },
});

const mapElement = ref(null);
const activeStatus = ref("all");
const activeConsumptionRange = ref("all");
const isFullscreen = ref(false);
let map = null;
let markerLayer = null;

const statusMeta = {
  normal: { label: "Normal", color: "#38bdf8" },
  zero: { label: "Consumo cero", color: "#f59e0b" },
  stale: { label: "Sin lectura", color: "#94a3b8" },
  jump: { label: "Salto anormal", color: "#ef4444" },
};

const statusItems = [
  { status: "normal", label: statusMeta.normal.label },
  { status: "zero", label: statusMeta.zero.label },
  { status: "stale", label: statusMeta.stale.label },
  { status: "jump", label: statusMeta.jump.label },
];
const filterItems = [{ status: "all", label: "Todos" }, ...statusItems];
const consumptionRanges = [
  { range: "0-10", label: "0-10", min: 0, max: 10 },
  { range: "10-15", label: "10-15", min: 10, max: 15 },
  { range: "15-20", label: "15-20", min: 15, max: 20 },
  { range: "20-25", label: "20-25", min: 20, max: 25 },
  { range: "25-30", label: "25-30", min: 25, max: 30 },
  { range: "30+", label: "+30", min: 30, max: null },
];
const consumptionFilterItems = [{ range: "all", label: "Todos los consumos" }, ...consumptionRanges];

const summary = computed(() => props.data?.summary || {});
const points = computed(() => props.data?.points || []);
const textFilteredPoints = computed(() => {
  const term = normalizeText(props.searchQuery);
  if (!term) return points.value;
  return points.value.filter((point) => {
    const searchable = [
      point.idconexion,
      point.cliente,
      point.direccion,
    ].map(normalizeText).join(" ");
    return searchable.includes(term);
  });
});
const statusCounts = computed(() => {
  const counts = { all: textFilteredPoints.value.length, normal: 0, zero: 0, stale: 0, jump: 0 };
  textFilteredPoints.value.forEach((point) => {
    if (point.status in counts) {
      counts[point.status] += 1;
    }
  });
  return counts;
});
const statusFilteredPoints = computed(() => {
  if (activeStatus.value === "all") return textFilteredPoints.value;
  return textFilteredPoints.value.filter((point) => point.status === activeStatus.value);
});
const consumptionCounts = computed(() => {
  const counts = { all: statusFilteredPoints.value.length };
  consumptionRanges.forEach((range) => {
    counts[range.range] = statusFilteredPoints.value.filter((point) => isPointInConsumptionRange(point, range.range)).length;
  });
  return counts;
});
const filteredPoints = computed(() => {
  if (activeConsumptionRange.value === "all") return statusFilteredPoints.value;
  return statusFilteredPoints.value.filter((point) => isPointInConsumptionRange(point, activeConsumptionRange.value));
});
const hasActiveFilters = computed(() => activeStatus.value !== "all" || activeConsumptionRange.value !== "all" || Boolean(props.searchQuery.trim()));

function makeMarkerIcon(status) {
  const color = statusMeta[status]?.color || statusMeta.normal.color;
  return L.divIcon({
    className: "connection-marker",
    html: `<span style="background:${color}"></span>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
    popupAnchor: [0, -9],
  });
}

function popupHtml(point) {
  const consumption = props.formatNumber(point.ultimo_consumo || 0);
  const period = point.ultimo_periodo || "sin periodo";
  const date = point.ultima_fecha_toma || "sin fecha";
  const status = statusMeta[point.status]?.label || point.status || "Sin estado";
  const reason = statusReasonHtml(point);
  return `
    <div class="connection-popup">
      <strong>Conexion ${point.idconexion}</strong>
      <span>${escapeHtml(point.cliente || "Cliente sin identificar")}</span>
      <small>${escapeHtml(point.direccion || "Sin direccion")}</small>
      <small>Zona ${escapeHtml(point.zona || "Sin zona")}</small>
      <b>${consumption} m3 · ${escapeHtml(period)}</b>
      <small>${escapeHtml(date)} · ${escapeHtml(status)}</small>
      ${reason}
    </div>
  `;
}

function statusReasonHtml(point) {
  if (point.status === "jump" && point.salto_consumo) {
    const jump = point.salto_consumo;
    const current = props.formatNumber(jump.consumo_actual || 0);
    const average = props.formatNumber(jump.media_historica || 0);
    const variation = props.formatNumber(Math.abs(jump.variacion || 0));
    const direction = jump.direccion === "baja" ? "bajo" : "subio";
    const period = jump.periodo || point.ultimo_periodo || "periodo actual";
    const samples = props.formatNumber(jump.muestras_historicas || 0);
    return `
      <em class="popup-reason">
        Motivo: ${direction} a ${current} m3 en ${escapeHtml(period)} contra una media historica
        de ${average} m3 (${samples} lecturas). Diferencia: ${variation} m3.
      </em>
    `;
  }
  if (!point.status_reason) return "";
  return `<em class="popup-reason">${escapeHtml(point.status_reason)}</em>`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalizeText(value) {
  return String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function isPointInConsumptionRange(point, rangeName) {
  const range = consumptionRanges.find((item) => item.range === rangeName);
  if (!range) return true;
  const consumption = Number(point.ultimo_consumo || 0);
  if (range.max === null) return consumption > range.min;
  if (range.min === 0) return consumption >= range.min && consumption <= range.max;
  return consumption > range.min && consumption <= range.max;
}

function resizeMapSoon() {
  window.setTimeout(() => {
    map?.invalidateSize();
    if (filteredPoints.value.length) {
      map?.fitBounds(focusLatLngs(), { padding: [18, 18], maxZoom: 18 });
    }
  }, 120);
}

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value;
  resizeMapSoon();
}

function handleKeydown(event) {
  if (event.key === "Escape" && isFullscreen.value) {
    isFullscreen.value = false;
    resizeMapSoon();
  }
}

function ensureMap() {
  if (map || !mapElement.value) return;
  map = L.map(mapElement.value, {
    zoomControl: true,
    attributionControl: true,
  });
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map);
  markerLayer = L.layerGroup().addTo(map);
}

function focusLatLngs() {
  const latLngs = filteredPoints.value.map((point) => [point.lat, point.lng]);
  if (latLngs.length < 20) return latLngs;

  const sortedLat = latLngs.map(([lat]) => lat).sort((left, right) => left - right);
  const sortedLng = latLngs.map(([, lng]) => lng).sort((left, right) => left - right);
  const trim = Math.floor(latLngs.length * 0.1);
  const minLat = sortedLat[trim];
  const maxLat = sortedLat[sortedLat.length - 1 - trim];
  const minLng = sortedLng[trim];
  const maxLng = sortedLng[sortedLng.length - 1 - trim];
  const focused = latLngs.filter(([lat, lng]) => lat >= minLat && lat <= maxLat && lng >= minLng && lng <= maxLng);
  return focused.length >= 3 ? focused : latLngs;
}

async function renderMarkers() {
  if (!filteredPoints.value.length) {
    if (markerLayer) markerLayer.clearLayers();
    return;
  }
  await nextTick();
  ensureMap();
  if (!map || !markerLayer) return;
  markerLayer.clearLayers();
  filteredPoints.value.forEach((point) => {
    const latLng = [point.lat, point.lng];
    L.marker(latLng, { icon: makeMarkerIcon(point.status) })
      .bindPopup(popupHtml(point))
      .addTo(markerLayer);
  });
  map.fitBounds(focusLatLngs(), { padding: [18, 18], maxZoom: 18 });
  window.setTimeout(() => map?.invalidateSize(), 80);
}

watch(filteredPoints, renderMarkers, { immediate: true });
watch(isFullscreen, (fullscreen) => {
  document.body.classList.toggle("map-fullscreen-open", fullscreen);
});

onMounted(() => {
  window.addEventListener("keydown", handleKeydown);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleKeydown);
  document.body.classList.remove("map-fullscreen-open");
  if (map) {
    map.remove();
    map = null;
    markerLayer = null;
  }
});
</script>
