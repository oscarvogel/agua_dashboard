<template>
  <section class="collections-command">
    <article class="collections-hero panel">
      <div>
        <span class="eyebrow">Salud de cobranzas</span>
        <h2>{{ formatMoney(health.period_collected) }}</h2>
        <p>
          {{ statusCopy }}
          <template v-if="health.previous_period"> vs {{ formatPeriodLabel(health.previous_period) }}</template>
        </p>
      </div>
      <span class="status-pill" :class="health.status">{{ statusLabel }}</span>
    </article>

    <section class="collections-kpis">
      <article v-for="card in kpiCards" :key="card.label" class="metric-card compact-metric">
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <small>{{ card.note }}</small>
      </article>
    </section>

    <article class="panel collections-chart-panel">
      <div class="panel-header">
        <div>
          <h2>Ritmo diario y acumulado</h2>
          <p>Barras por dia, acumulado real y ritmo esperado del periodo.</p>
        </div>
      </div>
      <apexchart
        v-if="dailyPerformance.length"
        type="line"
        height="290"
        :options="trendOptions"
        :series="trendSeries"
      />
      <p v-else class="empty-state">Sin movimientos diarios de cobranza para el periodo.</p>
    </article>

    <article class="panel collections-month-panel">
      <div class="panel-header compact">
        <h2>Meses disponibles</h2>
      </div>
      <div class="detail-table">
        <button
          v-for="row in monthlySeries"
          :key="`collections-${row.periodo}`"
          class="detail-row detail-link"
          type="button"
          @click="$emit('open-daily', row.periodo)"
        >
          <span>{{ formatPeriodLabel(row.periodo) }}</span>
          <strong>{{ formatMoney(row.cobranzas) }}</strong>
        </button>
      </div>
    </article>

    <article class="panel">
      <div class="panel-header compact">
        <h2>Eficiencia por zona</h2>
      </div>
      <div class="zone-efficiency-list">
        <div v-for="row in zoneEfficiency" :key="row.zona" class="zone-efficiency-row">
          <div>
            <strong>Zona {{ row.zona }}</strong>
            <small>{{ formatMoney(row.collected) }} cobrado · {{ formatMoney(row.overdue_debt) }} vencido</small>
          </div>
          <span>{{ formatPercent(row.recovery_rate) }}</span>
        </div>
        <p v-if="zoneEfficiency.length === 0" class="empty-state">Sin datos por zona.</p>
      </div>
    </article>

    <article class="panel collections-followup-panel">
      <div class="panel-header">
        <div>
          <h2>Ranking accionable</h2>
          <p>Socios priorizados por deuda vencida, ultimo pago y riesgo.</p>
        </div>
      </div>
      <div class="followup-table">
        <div v-for="row in followupRows" :key="row.idcliente" class="followup-row">
          <div>
            <strong>{{ row.cliente }}</strong>
            <small>Socio {{ row.idcliente }} · Zona {{ row.zona }} · {{ lastPaymentLabel(row) }}</small>
          </div>
          <span class="risk-pill" :class="row.riesgo">{{ row.riesgo }}</span>
          <strong>{{ formatMoney(row.deuda_vencida || row.deuda_total) }}</strong>
          <span class="action-pill">{{ row.accion_sugerida }}</span>
        </div>
        <p v-if="followupRows.length === 0" class="empty-state">Sin socios para seguimiento.</p>
      </div>
    </article>
  </section>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  dashboard: { type: Object, required: true },
  monthlySeries: { type: Array, required: true },
  formatMoney: { type: Function, required: true },
  formatNumber: { type: Function, required: true },
  formatPeriodLabel: { type: Function, required: true },
});

defineEmits(["open-daily"]);

const collections = computed(() => props.dashboard.collections || {});
const health = computed(() => collections.value.health || {});
const dailyPerformance = computed(() => collections.value.daily_performance || []);
const zoneEfficiency = computed(() => (collections.value.zone_efficiency || []).slice(0, 6));
const followupRows = computed(() => (collections.value.followup || []).slice(0, 10));

const statusLabel = computed(() => ({ good: "Buen ritmo", normal: "Ritmo normal", low: "Ritmo bajo" }[health.value.status] || "Sin estado"));
const statusCopy = computed(() => {
  const variation = Number(health.value.variation_pct || 0);
  if (variation > 0) return `Sube ${formatPercent(variation)}`;
  if (variation < 0) return `Baja ${formatPercent(Math.abs(variation))}`;
  return "Sin variacion relevante";
});

const kpiCards = computed(() => [
  {
    label: "Ultimos 7 dias",
    value: props.formatMoney(health.value.last_7_days),
    note: "caja reciente",
  },
  {
    label: "Socios que pagaron",
    value: props.formatNumber(health.value.paying_clients),
    note: "en periodo",
  },
  {
    label: "Recuperacion estimada",
    value: formatPercent(health.value.estimated_recovery_rate),
    note: "sobre deuda vencida",
  },
  {
    label: "Concentracion top 10",
    value: formatPercent(collections.value.concentration?.top_10_share),
    note: "dependencia de pocos pagos",
  },
]);

const trendOptions = computed(() => ({
  chart: { background: "transparent", toolbar: { show: false }, foreColor: "#94a3b8" },
  theme: { mode: "dark" },
  colors: ["#14b8a6", "#3b82f6", "#f59e0b"],
  stroke: { width: [0, 3, 2], curve: "smooth", dashArray: [0, 0, 6] },
  dataLabels: { enabled: false },
  plotOptions: { bar: { borderRadius: 4, columnWidth: "45%" } },
  xaxis: { categories: dailyPerformance.value.map((row) => row.fecha.slice(8)) },
  yaxis: { labels: { formatter: (val) => props.formatNumber(val) } },
  tooltip: { theme: "dark", y: { formatter: (val) => props.formatMoney(val) } },
  grid: { borderColor: "rgba(255, 255, 255, 0.08)" },
}));

const trendSeries = computed(() => [
  { name: "Dia", type: "column", data: dailyPerformance.value.map((row) => row.collected) },
  { name: "Acumulado", type: "line", data: dailyPerformance.value.map((row) => row.accumulated) },
  { name: "Esperado", type: "line", data: dailyPerformance.value.map((row) => row.expected_accumulated) },
]);

function formatPercent(value) {
  return `${props.formatNumber(Number(value || 0))}%`;
}

function lastPaymentLabel(row) {
  if (!row.ultimo_pago) return "sin pago registrado";
  return `ultimo pago ${row.ultimo_pago}`;
}
</script>
