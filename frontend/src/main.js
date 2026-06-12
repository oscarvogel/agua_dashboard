import { createApp } from "vue";
import {
  Activity,
  AlertTriangle,
  ArrowDownToLine,
  Banknote,
  Check,
  ChevronDown,
  Droplets,
  FileText,
  Gauge,
  Lock,
  LogOut,
  RefreshCcw,
  Search,
  UserPlus,
  Users,
} from "lucide-vue-next";
import App from "./App.vue";
import "./styles.css";
import VueApexCharts from "vue3-apexcharts";

const app = createApp(App);
app.use(VueApexCharts);
app.component("ActivityIcon", Activity);
app.component("AlertTriangleIcon", AlertTriangle);
app.component("ArrowDownToLineIcon", ArrowDownToLine);
app.component("BanknoteIcon", Banknote);
app.component("CheckIcon", Check);
app.component("ChevronDownIcon", ChevronDown);
app.component("DropletsIcon", Droplets);
app.component("FileTextIcon", FileText);
app.component("GaugeIcon", Gauge);
app.component("LockIcon", Lock);
app.component("LogOutIcon", LogOut);
app.component("RefreshCcwIcon", RefreshCcw);
app.component("SearchIcon", Search);
app.component("UserPlusIcon", UserPlus);
app.component("UsersIcon", Users);
app.mount("#app");
