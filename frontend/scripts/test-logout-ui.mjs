import { readFileSync } from "node:fs";

const appSource = readFileSync(new URL("../src/App.vue", import.meta.url), "utf8");

if (!appSource.includes('class="nav-item logout-nav"')) {
  throw new Error("Expected logout to be available as a visible sidebar navigation action.");
}

if (!/class="nav-item logout-nav"[\s\S]*Cerrar sesion[\s\S]*<\/button>/.test(appSource)) {
  throw new Error("Expected the logout action to expose visible 'Cerrar sesion' text.");
}

if (!appSource.includes("@click=\"logout\"")) {
  throw new Error("Expected the visible logout action to call logout().");
}

console.log("logout UI contract ok");
