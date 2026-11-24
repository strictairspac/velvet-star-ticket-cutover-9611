import { shell } from "./components/common/shell.js";
import { activeRoute } from "./router/router.js";
import { clearSession, session } from "./stores/session.js";
import { config as getConfig } from "./stores/workbench.js";
import { el } from "./utils/dom.js";
import { login } from "./pages/login.js";
import { overview } from "./pages/overview.js";
import { casesPage } from "./pages/cases.js";
import { runsPage } from "./pages/runs.js";
import { evidencePage } from "./pages/evidence.js";

const root = document.querySelector("#app");
let active;

function signOut() {
  clearSession();
  refresh();
}

async function refresh() {
  active?.abort();
  const token = new AbortController();
  active = token;
  const user = session();
  const route = activeRoute();
  try {
    const config = await getConfig();
    if (token.signal.aborted) return;
    if (!user) {
      root.replaceChildren(login(config, refresh));
      return;
    }
    root.setAttribute("aria-busy", "true");
    const pages = {
      overview: () => overview(config),
      cases: () => casesPage(config, user, route),
      runs: () => runsPage(config, route, token.signal),
      evidence: () => evidencePage(config, user, route),
    };
    const page = await pages[route.name]();
    if (!token.signal.aborted) {
      root.replaceChildren(shell(config, user, route, page, signOut));
      window.scrollTo(0, 0);
    }
  } catch (error) {
    if (token.signal.aborted) return;
    const retry = el("section", {class: "panel error-screen"}, el("h1", {}, "暂时无法加载"),
      el("p", {role: "alert"}, error.message), el("button", {type: "button", onclick: refresh}, "重试"));
    try {
      const config = await getConfig();
      if (!token.signal.aborted) root.replaceChildren(user ? shell(config, user, route, retry, signOut) : retry);
    } catch {
      if (!token.signal.aborted) root.replaceChildren(retry);
    }
  } finally {
    if (!token.signal.aborted) root.removeAttribute("aria-busy");
  }
}

window.addEventListener("hashchange", refresh);
window.addEventListener("sessionchange", refresh);
refresh();
