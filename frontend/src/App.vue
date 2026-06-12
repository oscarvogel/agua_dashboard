<template>
  <main class="app-shell" :class="{ 'no-sidebar': !session }">
    <aside v-if="session" class="sidebar" aria-label="Navegacion principal">
      <div class="brand">
        <div class="brand-mark"><DropletsIcon :size="22" /></div>
        <div>
          <strong>Cooperativa Agua</strong>
          <span>Panel ejecutivo</span>
        </div>
      </div>
      <nav>
        <a class="nav-item" :class="{ active: activeView === 'dashboard' }" href="#dashboard" @click.prevent="openDashboard">
          <GaugeIcon :size="18" /> Indicadores
        </a>
        <a class="nav-item" :class="{ active: activeView === 'billing' }" href="#billing" @click.prevent="openSection('billing')">
          <FileTextIcon :size="18" /> Facturacion
        </a>
        <a class="nav-item" :class="{ active: activeView === 'collections' }" href="#collections" @click.prevent="openSection('collections')">
          <BanknoteIcon :size="18" /> Cobranzas
        </a>
        <a class="nav-item" :class="{ active: activeView === 'consumption' }" href="#consumption" @click.prevent="openSection('consumption')">
          <ActivityIcon :size="18" /> Consumos
        </a>
        <a
          v-if="canViewAudit"
          class="nav-item"
          :class="{ active: activeView === 'audit' }"
          href="#audit"
          @click="openAudit"
        >
          <AlertTriangleIcon :size="18" /> Auditoria
        </a>
        <a
          v-if="canViewAudit"
          class="nav-item"
          :class="{ active: activeView === 'admin-users' }"
          href="#admin-users"
          @click="openUserAdmin"
        >
          <UserPlusIcon :size="18" /> Usuarios
        </a>
        <button class="nav-item logout-nav" type="button" @click="logout"><LogOutIcon :size="18" /> Cerrar sesion</button>
      </nav>
      <div class="source-card">
        <span>Fuente</span>
        <strong>{{ sourceLabel }}</strong>
        <small>{{ sourceDetail }}</small>
        <small v-if="syncStatus" :class="`sync-status ${syncStatus.state}`">{{ syncStatus.message }}</small>
      </div>
    </aside>

    <section class="workspace">
      <section v-if="!session" class="login-panel">
        <div class="login-copy">
          <LockIcon :size="26" />
          <h1>Acceso gerencial</h1>
          <p>Vista de solo lectura para revisar facturacion, deuda, cobranzas, consumos y pendientes.</p>
        </div>
        <form @submit.prevent="submitLogin" class="login-form">
          <label>
            Usuario
            <input v-model="credentials.username" autocomplete="username" />
          </label>
          <label>
            Contrasena
            <input v-model="credentials.password" type="password" autocomplete="current-password" />
          </label>
          <button class="primary-button" type="submit">Ingresar</button>
          <p v-if="loginError" class="form-error">{{ loginError }}</p>
        </form>
      </section>

      <template v-else>
        <header class="topbar">
          <div>
            <h1>{{ viewTitle }}</h1>
            <p>{{ viewSubtitle }}</p>
          </div>
          <div class="actions">
            <label class="search-box">
              <SearchIcon :size="16" />
              <input v-model="query" :placeholder="searchPlaceholder" />
            </label>
            <div class="period-filter" @click.stop>
              <button class="period-trigger" type="button" :disabled="isLoading" @click="periodMenuOpen = !periodMenuOpen">
                <span>{{ periodButtonLabel }}</span>
                <ChevronDownIcon :size="16" />
              </button>
              <div v-if="periodMenuOpen" class="period-menu">
                <label v-for="option in periodOptions" :key="option" class="period-option">
                  <input
                    type="checkbox"
                    :checked="isPeriodSelected(option)"
                    :disabled="isLoading"
                    @change="togglePeriod(option)"
                  />
                  <span class="checkbox-mark"><CheckIcon :size="13" /></span>
                  <span>{{ formatPeriodLabel(option) }}</span>
                </label>
              </div>
            </div>
            <select v-model="zone" :disabled="isLoading">
              <option value="">Todas las zonas</option>
              <option v-for="option in zoneOptions" :key="option" :value="option">Zona {{ option }}</option>
            </select>
            <select v-model="statusFilter" :disabled="isLoading">
              <option value="todos">Todos</option>
              <option value="activos">Activos</option>
              <option value="inactivos">Inactivos</option>
            </select>
            <button class="icon-button" type="button" title="Actualizar" @click="loadDashboard" :disabled="isLoading">
              <RefreshCcwIcon :size="17" :class="{ spin: isLoading }" />
            </button>
            <button class="icon-button logout-button" type="button" title="Cerrar sesion" @click="logout">
              <LogOutIcon :size="17" />
            </button>
          </div>
        </header>

        <section v-if="isLoading" class="loading-state" role="status" aria-live="polite">
          <RefreshCcwIcon :size="17" class="spin" />
          <span>Cargando datos del VPS...</span>
        </section>

        <section v-if="error" class="alert">
          <AlertTriangleIcon :size="18" />
          {{ error }}
        </section>

        <section v-if="syncAlert" class="alert sync-alert" :class="syncStatus.state">
          <AlertTriangleIcon :size="18" />
          {{ syncAlert }}
        </section>

        <section v-if="activeView === 'audit'" class="audit-view">
          <article class="panel audit-panel">
            <div class="panel-header">
              <div>
                <h2>Auditoria y errores</h2>
                <p>Ultimos eventos registrados por el backend.</p>
              </div>
              <button type="button" class="secondary-button" @click="loadAuditLogs" :disabled="auditLoading">
                <RefreshCcwIcon :size="16" :class="{ spin: auditLoading }" /> Actualizar
              </button>
            </div>
            <section v-if="auditLoading" class="loading-state compact-loader" role="status" aria-live="polite">
              <RefreshCcwIcon :size="17" class="spin" />
              <span>Cargando auditoria...</span>
            </section>
            <section v-if="auditError" class="alert">
              <AlertTriangleIcon :size="18" />
              {{ auditError }}
            </section>
            <div class="audit-list">
              <div v-for="event in auditEvents" :key="`${event.timestamp}-${event.event}`" class="audit-row">
                <span class="audit-level" :class="event.level">{{ event.level }}</span>
                <div>
                  <strong>{{ event.event }}</strong>
                  <p>{{ event.message || "Sin detalle" }}</p>
                  <small>{{ formatDateTime(event.timestamp) }} · {{ event.username }}</small>
                </div>
              </div>
              <p v-if="!auditLoading && auditEvents.length === 0" class="empty-state">Todavia no hay eventos registrados.</p>
            </div>
          </article>
        </section>

        <section v-else-if="activeView === 'admin-users'" class="admin-users-view">
          <article class="panel user-admin-panel">
            <div class="panel-header">
              <div>
                <h2>Usuarios del dashboard</h2>
                <p>Altas y claves para acceso gerencial.</p>
              </div>
              <button type="button" class="secondary-button" @click="loadAdminUsers" :disabled="usersLoading">
                <RefreshCcwIcon :size="16" :class="{ spin: usersLoading }" /> Actualizar
              </button>
            </div>

            <form class="user-create-form" @submit.prevent="submitCreateUser">
              <label>
                Usuario
                <input v-model="newUser.username" autocomplete="off" placeholder="usuario" />
              </label>
              <label>
                Clave
                <input v-model="newUser.password" type="password" autocomplete="new-password" placeholder="minimo 8 caracteres" />
              </label>
              <label class="checkbox-field">
                <input v-model="newUser.isAdmin" type="checkbox" />
                <span class="checkbox-mark"><CheckIcon :size="13" /></span>
                Administrador
              </label>
              <button class="primary-button" type="submit" :disabled="usersLoading">
                <UserPlusIcon :size="16" /> Crear usuario
              </button>
            </form>

            <section v-if="usersMessage" class="success-message">{{ usersMessage }}</section>
            <section v-if="usersError" class="alert">
              <AlertTriangleIcon :size="18" />
              {{ usersError }}
            </section>
            <section v-if="usersLoading" class="loading-state compact-loader" role="status" aria-live="polite">
              <RefreshCcwIcon :size="17" class="spin" />
              <span>Cargando usuarios...</span>
            </section>

            <div class="user-list">
              <div v-for="user in adminUsers" :key="user.id" class="user-row">
                <div>
                  <strong>{{ user.username }}</strong>
                  <small>{{ user.is_admin ? "Administrador" : "Lectura" }} · {{ user.is_active ? "Activo" : "Inactivo" }}</small>
                </div>
                <span>{{ user.last_login ? formatDateTime(user.last_login) : "Sin ingreso" }}</span>
              </div>
              <p v-if="!usersLoading && adminUsers.length === 0" class="empty-state">Todavia no hay usuarios creados desde el panel.</p>
            </div>
          </article>
        </section>

        <section v-else-if="activeView === 'billing' && dashboard" class="detail-view" :class="{ 'is-loading': isLoading }">
          <article class="panel wide-detail">
            <div class="panel-header">
              <div>
                <h2>Facturacion por periodo</h2>
                <p>Compara la facturacion mensual del rango seleccionado.</p>
              </div>
              <strong>{{ formatMoney(dashboard.summary.facturacion_mes) }}</strong>
            </div>
            <div class="detail-table">
              <button
                v-for="row in monthlySeries"
                :key="`billing-${row.periodo}`"
                class="detail-row detail-link"
                type="button"
                @click="openDailyDetail('billing', row.periodo)"
              >
                <span>{{ formatPeriodLabel(row.periodo) }}</span>
                <strong>{{ formatMoney(row.facturacion) }}</strong>
              </button>
            </div>
          </article>
        </section>

        <section v-else-if="activeView === 'collections' && dashboard" class="detail-view" :class="{ 'is-loading': isLoading }">
          <CollectionsOverview
            :dashboard="dashboard"
            :monthly-series="monthlySeries"
            :format-money="formatMoney"
            :format-number="formatNumber"
            :format-period-label="formatPeriodLabel"
            @open-daily="(month) => openDailyDetail('collections', month)"
          />
        </section>

        <section v-else-if="activeView === 'consumption' && dashboard" class="detail-view" :class="{ 'is-loading': isLoading }">
          <ConnectionsMap
            :data="dashboard.maps?.connections"
            :search-query="query"
            :format-number="formatNumber"
          />
          <article class="panel wide-detail">
            <div class="panel-header">
              <div>
                <h2>Consumos por periodo</h2>
                <p>Metros cubicos registrados y alertas operativas.</p>
              </div>
              <strong>{{ formatNumber(dashboard.summary.consumo_ultimo_periodo) }} m3</strong>
            </div>
            <div class="detail-table">
              <div
                v-for="row in monthlySeries"
                :key="`consumption-${row.periodo}`"
                class="detail-row"
              >
                <span>{{ formatPeriodLabel(row.periodo) }}</span>
                <strong>{{ formatNumber(row.consumo) }} m3</strong>
              </div>
            </div>
            <div class="detail-summary">
              <span>Sin lectura reciente: {{ formatNumber(dashboard.summary.conexiones_sin_lectura_reciente) }}</span>
              <span>Consumos cero: {{ formatNumber(dashboard.summary.consumos_cero) }}</span>
            </div>
          </article>
        </section>

        <section v-else-if="isCollectionDayDetailView && dashboard" class="detail-view" :class="{ 'is-loading': isLoading }">
          <article class="panel wide-detail">
            <div class="panel-header">
              <div>
                <h2>Cobranza por socio</h2>
                <p>Detalle de {{ formatDayLabel(selectedCollectionDay) }} en {{ formatPeriodLabel(effectiveDailyMonth) }}.</p>
              </div>
              <button type="button" class="secondary-button" @click="openDailyDetail('collections', effectiveDailyMonth)">Volver</button>
            </div>
            <div class="detail-summary collection-day-summary">
              <span>Total del dia: {{ formatMoney(collectionDayTotal) }}</span>
              <label class="search-box compact-search">
                <SearchIcon :size="15" />
                <input v-model="collectionDayQuery" placeholder="Buscar socio" />
              </label>
            </div>
            <div class="detail-table">
              <div v-for="row in filteredCollectionDayRows" :key="`${row.idcliente}-${row.importe}`" class="detail-row stacked-row">
                <span>
                  <strong>{{ row.cliente }}</strong>
                  <small>
                    Socio {{ row.idcliente || "sin identificar" }} · {{ formatNumber(row.movimientos) }} mov.
                    <template v-if="row.comprobantes?.length"> · Comp. {{ row.comprobantes.join(", ") }}</template>
                    <template v-if="row.deuda_total"> · Deuda {{ formatMoney(row.deuda_total) }}</template>
                  </small>
                </span>
                <strong>{{ formatMoney(row.importe) }}</strong>
              </div>
              <p v-if="filteredCollectionDayRows.length === 0" class="empty-state">No hay detalle de socios para este dia.</p>
            </div>
          </article>
        </section>

        <section v-else-if="isDailyView && dashboard" class="detail-view" :class="{ 'is-loading': isLoading }">
          <article class="panel wide-detail">
            <div class="panel-header">
              <div>
                <h2>{{ dailyDetailTitle }}</h2>
                <p>Detalle dia por dia de {{ formatPeriodLabel(effectiveDailyMonth) }}.</p>
              </div>
              <button type="button" class="secondary-button" @click="openSection(dailyBackView)">Volver</button>
            </div>
            <div v-if="effectiveDailyKind === 'collections'" class="daily-mini-chart">
              <span>Total mes: {{ formatMoney(dailyCollectionTotal) }}</span>
              <span>Promedio diario: {{ formatMoney(dailyCollectionAverage) }}</span>
              <apexchart v-if="dailyRows.length" type="bar" height="170" :options="chartOptionsDailyCollections" :series="chartSeriesDailyCollections"></apexchart>
            </div>
            <div class="detail-table">
              <button
                v-for="row in dailyRows"
                :key="row.fecha"
                class="detail-row"
                :class="{ 'detail-link': effectiveDailyKind === 'collections', 'strong-day': effectiveDailyKind === 'collections' && row.cobranzas >= dailyCollectionAverage && row.cobranzas > 0 }"
                type="button"
                :disabled="effectiveDailyKind !== 'collections'"
                @click="openCollectionDayDetail(row.fecha)"
              >
                <span>{{ formatDayLabel(row.fecha) }}</span>
                <strong>{{ formatDailyValue(row) }}</strong>
              </button>
              <p v-if="dailyRows.length === 0" class="empty-state">No hay movimientos diarios para este periodo.</p>
            </div>
          </article>
        </section>

        <section v-else-if="dashboard" class="content-grid" :class="{ 'is-loading': isLoading }">
          <article v-for="card in cards" :key="card.label" class="metric-card">
            <component :is="card.icon" :size="21" />
            <span>{{ card.label }}</span>
            <strong>{{ card.value }}</strong>
            <small>{{ card.note }}</small>
          </article>

          <article class="panel wide">
            <div class="panel-header">
              <div>
                <h2>Facturacion vs cobranzas</h2>
                <p>Evolucion mensual sobre la copia del VPS o demo local.</p>
              </div>
              <button type="button" class="secondary-button" @click="exportCsv"><ArrowDownToLineIcon :size="16" /> Exportar</button>
            </div>
            <apexchart type="area" height="250" :options="chartOptionsBilling" :series="chartSeriesBilling"></apexchart>
          </article>

          <article class="panel">
            <div class="panel-header compact">
              <h2>Top deudores</h2>
            </div>
            <div class="debt-list">
              <div v-for="debtor in filteredDebtors" :key="debtor.cliente" class="debt-row">
                <span>{{ debtor.cliente }}</span>
                <strong>{{ formatMoney(debtor.deuda) }}</strong>
              </div>
            </div>
          </article>

          <article class="panel collection-health-panel">
            <div class="panel-header compact">
              <h2>Salud de cobranzas</h2>
            </div>
            <div class="quality-list">
              <div>
                <span></span>
                <p>Estado del periodo</p>
                <strong>{{ collectionStatusLabel }}</strong>
              </div>
              <div>
                <span></span>
                <p>Ultimos 7 dias</p>
                <strong>{{ formatMoney(collectionHealth.last_7_days) }}</strong>
              </div>
              <div>
                <span></span>
                <p>Recuperacion estimada</p>
                <strong>{{ formatNumber(collectionHealth.estimated_recovery_rate) }}%</strong>
              </div>
              <div>
                <span></span>
                <p>Socios que pagaron</p>
                <strong>{{ formatNumber(collectionHealth.paying_clients) }}</strong>
              </div>
            </div>
          </article>

          <article class="panel">
            <div class="panel-header compact">
              <h2>Deuda por antiguedad</h2>
            </div>
            <apexchart v-if="debtAgingRows.length" type="bar" height="250" :options="chartOptionsDebtAging" :series="chartSeriesDebtAging"></apexchart>
            <p v-else class="empty-state">Sin deuda clasificada.</p>
          </article>

          <article class="panel">
            <div class="panel-header compact">
              <h2>Deuda por zona</h2>
            </div>
            <apexchart v-if="debtZoneRows.length" type="donut" height="250" :options="chartOptionsDebtZone" :series="chartSeriesDebtZone"></apexchart>
            <p v-else class="empty-state">Sin deuda por zona.</p>
          </article>

          <article class="panel">
            <div class="panel-header compact">
              <h2>Conceptos y pendientes</h2>
            </div>
            <div class="split-breakdown">
              <div>
                <h3>Facturacion</h3>
                <div v-for="row in billingConceptRows" :key="row.concepto" class="breakdown-row">
                  <span>{{ row.concepto }}</span>
                  <strong>{{ formatMoney(row.importe) }}</strong>
                </div>
                <p v-if="billingConceptRows.length === 0" class="empty-state">Sin detalle por concepto.</p>
              </div>
              <div>
                <h3>Pendientes</h3>
                <div v-for="row in pendingConceptRows" :key="row.concepto" class="breakdown-row">
                  <span>{{ row.concepto }}</span>
                  <strong>{{ formatMoney(row.importe) }}</strong>
                </div>
                <p v-if="pendingConceptRows.length === 0" class="empty-state">Sin pendientes por concepto.</p>
              </div>
            </div>
          </article>

          <article class="panel">
            <div class="panel-header compact">
              <h2>Padron y control</h2>
            </div>
            <div class="split-breakdown">
              <div>
                <h3>Padron por zona</h3>
                <div v-for="row in registryZoneRows" :key="row.zona" class="breakdown-row">
                  <span>Zona {{ row.zona }}</span>
                  <strong>{{ formatNumber(row.conexiones) }} conex.</strong>
                </div>
                <p v-if="registryZoneRows.length === 0" class="empty-state">Sin padron por zona.</p>
              </div>
              <div>
                <h3>Estados dudosos</h3>
                <div v-for="row in doubtfulStatusRows" :key="`${row.tipo}-${row.estado}`" class="breakdown-row">
                  <span>{{ row.tipo }} {{ row.estado }}</span>
                  <strong>{{ formatNumber(row.cantidad) }}</strong>
                </div>
                <p v-if="doubtfulStatusRows.length === 0" class="empty-state">Sin comprobantes dudosos.</p>
              </div>
            </div>
          </article>

          <article class="panel">
            <div class="panel-header compact">
              <h2>Anomalias y repetidos</h2>
            </div>
            <div class="split-breakdown">
              <div>
                <h3>Saltos de consumo</h3>
                <div v-for="row in consumptionJumpRows" :key="`${row.idconexion}-${row.periodo}`" class="breakdown-row">
                  <span>Conexion {{ row.idconexion }}</span>
                  <strong>{{ row.variacion > 0 ? "+" : "" }}{{ formatNumber(row.variacion) }} m3</strong>
                </div>
                <p v-if="consumptionJumpRows.length === 0" class="empty-state">Sin saltos anormales.</p>
              </div>
              <div>
                <h3>Pendientes repetidos</h3>
                <div v-for="row in repeatedPendingRows" :key="`${row.idcliente}-${row.idconexion}`" class="breakdown-row">
                  <span>{{ row.cliente }}</span>
                  <strong>{{ formatNumber(row.pendientes) }}</strong>
                </div>
                <p v-if="repeatedPendingRows.length === 0" class="empty-state">Sin repetidos.</p>
              </div>
            </div>
          </article>
        </section>
      </template>
    </section>
  </main>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { createAdminUser, fetchAdminUsers, fetchAuditLogs, fetchDashboard, login } from "./api";
import ConnectionsMap from "./ConnectionsMap.vue";
import CollectionsOverview from "./CollectionsOverview.vue";

const session = ref(localStorage.getItem("agua_dashboard_token"));
const currentUser = ref(localStorage.getItem("agua_dashboard_user") || "");
const currentIsAdmin = ref(localStorage.getItem("agua_dashboard_is_admin") === "1" || Boolean(session.value));
const dashboard = ref(null);
const error = ref("");
const loginError = ref("");
const query = ref("");
const period = ref("actual");
const selectedPeriods = ref([]);
const periodMenuOpen = ref(false);
const zone = ref("");
const statusFilter = ref("todos");
const credentials = reactive({ username: "admin", password: "" });
const isLoading = ref(false);
const activeRequestId = ref(0);
const activeView = ref(["#audit", "#admin-users"].includes(window.location.hash) ? window.location.hash.slice(1) : "dashboard");
const selectedDailyKind = ref("");
const selectedDailyMonth = ref("");
const selectedCollectionDay = ref("");
const collectionDayQuery = ref("");
const auditEvents = ref([]);
const auditLoading = ref(false);
const auditError = ref("");
const adminUsers = ref([]);
const usersLoading = ref(false);
const usersError = ref("");
const usersMessage = ref("");
const newUser = reactive({ username: "", password: "", isAdmin: false });
let filterTimer = null;

const formatMoney = (value) =>
  new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 }).format(value || 0);
const formatNumber = (value) => new Intl.NumberFormat("es-AR", { maximumFractionDigits: 0 }).format(value || 0);
const formatDateTime = (value) => {
  if (!value) return "";
  return new Intl.DateTimeFormat("es-AR", { dateStyle: "short", timeStyle: "medium" }).format(new Date(value));
};
const formatPeriodLabel = (value) => {
  const [year, month] = String(value).split("-");
  if (!year || !month) return value;
  const date = new Date(Number(year), Number(month) - 1, 1);
  return new Intl.DateTimeFormat("es-AR", { month: "short", year: "numeric" }).format(date);
};
const formatDayLabel = (value) => {
  const [, month, day] = String(value).split("-");
  return day && month ? `${day}/${month}` : value;
};

const sourceLabel = computed(() => {
  if (!dashboard.value) return "Sin cargar";
  return dashboard.value.source.mode === "mysql" ? "VPS MySQL" : "Demo local";
});

const sourceDetail = computed(() => {
  if (!dashboard.value) return "Esperando inicio de sesion";
  return dashboard.value.source.database_configured
    ? "Credenciales detectadas"
    : "Falta .env para datos reales";
});
const syncStatus = computed(() => dashboard.value?.source?.sync || null);
const syncAlert = computed(() => {
  if (!syncStatus.value || syncStatus.value.state === "ok") return "";
  return `Sincronizacion: ${syncStatus.value.message}`;
});

const cards = computed(() => {
  const s = dashboard.value?.summary || {};
  return [
    { label: "Facturacion periodo", value: formatMoney(s.facturacion_mes), note: "cabfact + impuestos", icon: "FileTextIcon" },
    { label: "Cobranzas periodo", value: formatMoney(s.cobranzas_mes), note: "movcaja validos", icon: "BanknoteIcon" },
    { label: "Deuda total", value: formatMoney(s.deuda_total), note: "ctacte neta", icon: "AlertTriangleIcon" },
    { label: "Conexiones activas", value: formatNumber(s.conexiones_activas), note: `${formatNumber(s.clientes_activos)} clientes activos`, icon: "UsersIcon" },
  ];
});


const monthlySeries = computed(() => {
  const rows = dashboard.value?.series?.monthly || [];
  const maxValue = Math.max(1, ...rows.flatMap((row) => [row.facturacion, row.cobranzas]));
  return rows.map((row) => ({
    ...row,
    billingHeight: Math.max(8, (row.facturacion / maxValue) * 100),
    collectionsHeight: Math.max(8, (row.cobranzas / maxValue) * 100),
  }));
});

const filteredDebtors = computed(() => {
  const term = query.value.trim().toLowerCase();
  return (dashboard.value?.top_deudores || []).filter((item) => item.cliente.toLowerCase().includes(term));
});

const debtAgingRows = computed(() => dashboard.value?.breakdowns?.deuda_antiguedad || []);
const debtZoneRows = computed(() => dashboard.value?.breakdowns?.deuda_zona || []);
const billingConceptRows = computed(() => dashboard.value?.breakdowns?.facturacion_concepto || []);
const pendingConceptRows = computed(() => dashboard.value?.breakdowns?.pendientes_concepto || []);
const registryZoneRows = computed(() => dashboard.value?.breakdowns?.padron_zona || []);
const doubtfulStatusRows = computed(() => dashboard.value?.breakdowns?.comprobantes_estado || []);
const consumptionJumpRows = computed(() => dashboard.value?.breakdowns?.saltos_consumo || []);
const repeatedPendingRows = computed(() => dashboard.value?.breakdowns?.pendientes_repetidos || []);
const zoneOptions = computed(() => dashboard.value?.filters?.zones || []);
const collectionHealth = computed(() => dashboard.value?.collections?.health || {});
const collectionStatusLabel = computed(() => ({ good: "Buen ritmo", normal: "Ritmo normal", low: "Ritmo bajo" }[collectionHealth.value.status] || "Sin estado"));

const chartOptionsBilling = computed(() => ({
  chart: { type: 'area', height: 250, toolbar: { show: false }, background: 'transparent', foreColor: '#94a3b8' },
  theme: { mode: 'dark' },
  colors: ['#3b82f6', '#14b8a6'],
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth', width: 2 },
  xaxis: { categories: monthlySeries.value.map(row => row.periodo.slice(5)) },
  yaxis: { labels: { formatter: (val) => formatNumber(val) } },
  tooltip: { theme: 'dark', y: { formatter: (val) => formatMoney(val) } },
  grid: { borderColor: 'rgba(255, 255, 255, 0.08)' }
}));

const chartSeriesBilling = computed(() => [
  { name: 'Facturación', data: monthlySeries.value.map(row => row.facturacion) },
  { name: 'Cobranzas', data: monthlySeries.value.map(row => row.cobranzas) }
]);

const chartOptionsDebtZone = computed(() => ({
  chart: { type: 'donut', background: 'transparent', foreColor: '#94a3b8' },
  theme: { mode: 'dark' },
  labels: debtZoneRows.value.map(row => `Zona ${row.zona}`),
  tooltip: { theme: 'dark', y: { formatter: (val) => formatMoney(val) } },
  stroke: { show: false },
  plotOptions: { pie: { donut: { size: '65%' } } }
}));

const chartSeriesDebtZone = computed(() => debtZoneRows.value.map(row => row.importe));

const chartOptionsDebtAging = computed(() => ({
  chart: { type: 'bar', height: 250, toolbar: { show: false }, background: 'transparent', foreColor: '#94a3b8' },
  theme: { mode: 'dark' },
  plotOptions: { bar: { horizontal: true, borderRadius: 4 } },
  colors: ['#ef4444'],
  dataLabels: { enabled: false },
  xaxis: { categories: debtAgingRows.value.map(row => row.rango), labels: { formatter: (val) => formatNumber(val) } },
  yaxis: { labels: { style: { cssClass: 'apexcharts-yaxis-label' } } },
  tooltip: { theme: 'dark', y: { formatter: (val) => formatMoney(val) } },
  grid: { borderColor: 'rgba(255, 255, 255, 0.08)', xaxis: { lines: { show: true } }, yaxis: { lines: { show: false } } }
}));

const chartSeriesDebtAging = computed(() => [
  { name: 'Deuda', data: debtAgingRows.value.map(row => row.importe) }
]);
const chartOptionsDailyCollections = computed(() => ({
  chart: { type: 'bar', height: 170, toolbar: { show: false }, background: 'transparent', foreColor: '#94a3b8' },
  theme: { mode: 'dark' },
  colors: ['#14b8a6'],
  dataLabels: { enabled: false },
  plotOptions: { bar: { borderRadius: 4, columnWidth: '48%' } },
  xaxis: { categories: dailyRows.value.map(row => formatDayLabel(row.fecha)) },
  yaxis: { labels: { formatter: (val) => formatNumber(val) } },
  tooltip: { theme: 'dark', y: { formatter: (val) => formatMoney(val) } },
  grid: { borderColor: 'rgba(255, 255, 255, 0.08)' }
}));
const chartSeriesDailyCollections = computed(() => [
  { name: 'Cobranzas', data: dailyRows.value.map(row => row.cobranzas) }
]);
const canViewAudit = computed(() => Boolean(session.value && currentIsAdmin.value));
const periodOptions = computed(() => dashboard.value?.filters?.period_options || []);
const appliedPeriods = computed(() => selectedPeriods.value.length ? selectedPeriods.value : dashboard.value?.filters?.periods || []);
const periodButtonLabel = computed(() => {
  if (appliedPeriods.value.length === 1) return formatPeriodLabel(appliedPeriods.value[0]);
  if (appliedPeriods.value.length > 1) return `${appliedPeriods.value.length} periodos`;
  return "Periodo";
});
const searchPlaceholder = computed(() => activeView.value === "consumption" ? "Buscar conexion o cliente" : "Buscar deudor");
const viewTitle = computed(() => {
  const titles = {
    dashboard: "Dashboard ejecutivo",
    billing: "Facturacion",
    collections: "Cobranzas",
    consumption: "Consumos",
    "billing-day": "Facturacion diaria",
    "collections-day": "Cobranzas diarias",
    "collections-member": "Cobranza por socio",
    audit: "Auditoria y errores",
    "admin-users": "Usuarios",
  };
  return titles[activeView.value] || titles.dashboard;
});
const viewSubtitle = computed(() => {
  const subtitles = {
    dashboard: "Lectura gerencial del padron, caja, deuda y consumo operativo.",
    billing: "Detalle mensual de facturacion para los periodos seleccionados.",
    collections: "Seguimiento mensual de caja y cobranzas registradas.",
    consumption: "Lectura operativa de consumos, conexiones y alertas.",
    "billing-day": "Detalle de facturacion dia por dia.",
    "collections-day": "Detalle de cobranzas dia por dia.",
    "collections-member": "Detalle de cobranza del dia agrupada por socio.",
    audit: "Registro de errores, accesos y eventos administrativos.",
    "admin-users": "Alta de usuarios y claves del dashboard.",
  };
  return subtitles[activeView.value] || subtitles.dashboard;
});
const isDailyView = computed(() => ["billing-day", "collections-day"].includes(activeView.value));
const isCollectionDayDetailView = computed(() => activeView.value === "collections-member");
const dailyBackView = computed(() => activeView.value.replace("-day", ""));
const effectiveDailyKind = computed(() => selectedDailyKind.value || dailyBackView.value);
const effectiveDailyMonth = computed(() => {
  if (selectedDailyMonth.value) return selectedDailyMonth.value;
  if (appliedPeriods.value.length) return appliedPeriods.value[appliedPeriods.value.length - 1];
  const rows = monthlySeries.value;
  return rows.length ? rows[rows.length - 1].periodo : "";
});
const dailyRows = computed(() => dashboard.value?.series?.daily?.[effectiveDailyMonth.value] || []);
const collectionDayRows = computed(() => dashboard.value?.breakdowns?.cobranzas_por_dia_socio?.[selectedCollectionDay.value] || []);
const collectionFollowupByClient = computed(() => {
  const rows = dashboard.value?.collections?.followup || [];
  return new Map(rows.map((row) => [row.idcliente, row]));
});
const enrichedCollectionDayRows = computed(() => collectionDayRows.value.map((row) => ({
  ...row,
  deuda_total: collectionFollowupByClient.value.get(row.idcliente)?.deuda_total || 0,
  deuda_vencida: collectionFollowupByClient.value.get(row.idcliente)?.deuda_vencida || 0,
})));
const filteredCollectionDayRows = computed(() => {
  const term = collectionDayQuery.value.trim().toLowerCase();
  if (!term) return enrichedCollectionDayRows.value;
  return enrichedCollectionDayRows.value.filter((row) => String(row.cliente || "").toLowerCase().includes(term) || String(row.idcliente || "").includes(term));
});
const collectionDayTotal = computed(() => collectionDayRows.value.reduce((total, row) => total + Number(row.importe || 0), 0));
const dailyCollectionTotal = computed(() => dailyRows.value.reduce((total, row) => total + Number(row.cobranzas || 0), 0));
const dailyCollectionAverage = computed(() => {
  if (!dailyRows.value.length) return 0;
  return dailyCollectionTotal.value / dailyRows.value.length;
});
const dailyDetailTitle = computed(() => {
  const titles = {
    billing: "Facturacion diaria",
    collections: "Cobranzas diarias",
  };
  return titles[effectiveDailyKind.value] || "Detalle diario";
});

async function submitLogin() {
  loginError.value = "";
  try {
    const result = await login(credentials.username, credentials.password);
    localStorage.setItem("agua_dashboard_token", result.token);
    localStorage.setItem("agua_dashboard_user", result.user.username);
    localStorage.setItem("agua_dashboard_is_admin", result.user.is_admin ? "1" : "0");
    session.value = result.token;
    currentUser.value = result.user.username;
    currentIsAdmin.value = Boolean(result.user.is_admin);
    await loadDashboard();
  } catch (err) {
    loginError.value = err.message;
  }
}

async function loadDashboard() {
  const requestId = activeRequestId.value + 1;
  activeRequestId.value = requestId;
  isLoading.value = true;
  error.value = "";
  try {
    const nextDashboard = await fetchDashboard({
      period: period.value,
      periods: selectedPeriods.value,
      zone: zone.value,
      status: statusFilter.value,
      token: session.value,
    });
    if (requestId === activeRequestId.value) {
      dashboard.value = nextDashboard;
    }
  } catch (err) {
    if (requestId !== activeRequestId.value) return;
    error.value = err.message;
    if (err.message.includes("autentic")) {
      localStorage.removeItem("agua_dashboard_token");
      localStorage.removeItem("agua_dashboard_user");
      localStorage.removeItem("agua_dashboard_is_admin");
      session.value = "";
      currentUser.value = "";
      currentIsAdmin.value = false;
      activeView.value = "dashboard";
    }
  } finally {
    if (requestId === activeRequestId.value) {
      isLoading.value = false;
    }
  }
}

function isPeriodSelected(option) {
  return appliedPeriods.value.includes(option);
}

function togglePeriod(option) {
  const base = appliedPeriods.value.length ? appliedPeriods.value : [];
  const next = base.includes(option) ? base.filter((value) => value !== option) : [...base, option];
  selectedPeriods.value = next.length ? next : [option];
}

async function loadAuditLogs() {
  auditLoading.value = true;
  auditError.value = "";
  try {
    const result = await fetchAuditLogs({ token: session.value });
    auditEvents.value = result.events || [];
  } catch (err) {
    auditError.value = err.message;
  } finally {
    auditLoading.value = false;
  }
}

async function openAudit() {
  window.location.hash = "audit";
  activeView.value = "audit";
  await loadAuditLogs();
}

async function loadAdminUsers() {
  usersLoading.value = true;
  usersError.value = "";
  try {
    const result = await fetchAdminUsers({ token: session.value });
    adminUsers.value = result.users || [];
  } catch (err) {
    usersError.value = err.message;
  } finally {
    usersLoading.value = false;
  }
}

async function submitCreateUser() {
  usersLoading.value = true;
  usersError.value = "";
  usersMessage.value = "";
  try {
    const result = await createAdminUser({
      token: session.value,
      username: newUser.username,
      password: newUser.password,
      isAdmin: newUser.isAdmin,
    });
    usersMessage.value = `Usuario creado: ${result.user.username}`;
    newUser.username = "";
    newUser.password = "";
    newUser.isAdmin = false;
    await loadAdminUsers();
  } catch (err) {
    usersError.value = err.message;
  } finally {
    usersLoading.value = false;
  }
}

async function openUserAdmin() {
  window.location.hash = "admin-users";
  activeView.value = "admin-users";
  await loadAdminUsers();
}

function openDashboard() {
  openSection("dashboard");
}

function openSection(view) {
  window.location.hash = view;
  activeView.value = view;
}

function openDailyDetail(kind, month) {
  selectedDailyKind.value = kind;
  selectedDailyMonth.value = month;
  selectedCollectionDay.value = "";
  openSection(`${kind}-day`);
}

function openCollectionDayDetail(day) {
  if (effectiveDailyKind.value !== "collections") return;
  selectedCollectionDay.value = day;
  collectionDayQuery.value = "";
  openSection("collections-member");
}

function formatDailyValue(row) {
  if (effectiveDailyKind.value === "collections") return formatMoney(row.cobranzas);
  return formatMoney(row.facturacion);
}

function applyHashView() {
  if (window.location.hash === "#audit" && canViewAudit.value) {
    openAudit();
  } else if (window.location.hash === "#admin-users" && canViewAudit.value) {
    openUserAdmin();
  } else if (["#billing", "#collections", "#consumption"].includes(window.location.hash)) {
    activeView.value = window.location.hash.slice(1);
  } else if (["#billing-day", "#collections-day", "#collections-member"].includes(window.location.hash)) {
    activeView.value = window.location.hash.slice(1);
  } else if (window.location.hash === "#consumption-day") {
    openSection("consumption");
  } else {
    activeView.value = "dashboard";
  }
}

function exportCsv() {
  if (!dashboard.value) return;
  const rows = [
    ["Indicador", "Valor"],
    ...cards.value.map((card) => [card.label, card.value]),
    [],
    ["Periodo", "Facturacion", "Cobranzas"],
    ...monthlySeries.value.map((row) => [row.periodo, row.facturacion, row.cobranzas]),
    [],
    ["Deudor", "Deuda"],
    ...filteredDebtors.value.map((row) => [row.cliente, row.deuda]),
  ];
  const csv = rows.map((row) => row.map((cell) => `"${String(cell ?? "").replaceAll('"', '""')}"`).join(",")).join("\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `dashboard-agua-${period.value}-${zone.value || "todas"}-${statusFilter.value}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

watch([period, zone, statusFilter], () => {
  if (!session.value) return;
  window.clearTimeout(filterTimer);
  filterTimer = window.setTimeout(loadDashboard, 250);
});

watch(selectedPeriods, () => {
  if (!session.value) return;
  window.clearTimeout(filterTimer);
  filterTimer = window.setTimeout(loadDashboard, 250);
});

onMounted(() => {
  if (session.value) {
    loadDashboard();
    applyHashView();
  }
  window.addEventListener("hashchange", applyHashView);
  document.addEventListener("click", closePeriodMenu);
});

onBeforeUnmount(() => {
  window.removeEventListener("hashchange", applyHashView);
  document.removeEventListener("click", closePeriodMenu);
});

function logout() {
  localStorage.removeItem("agua_dashboard_token");
  localStorage.removeItem("agua_dashboard_user");
  localStorage.removeItem("agua_dashboard_is_admin");
  session.value = "";
  currentUser.value = "";
  currentIsAdmin.value = false;
  dashboard.value = null;
  activeView.value = "dashboard";
  window.location.hash = "";
}

function closePeriodMenu() {
  periodMenuOpen.value = false;
}
</script>
