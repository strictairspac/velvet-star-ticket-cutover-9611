import { Roles } from "../../constants/roles.js";
import { routes } from "../../router/router.js";
import { el } from "../../utils/dom.js";

export function shell(config, user, route, page, signOut) {
  const links = routes.map((name, index) => el("a", {
    href: `#${name}`, "aria-current": route.name === name ? "page" : null,
  }, config.modules[index]));
  return el("div", {class: "shell"},
    el("aside", {class: "rail"},
      el("a", {class: "brand", href: "#overview"}, config.title),
      el("p", {class: "rail-direction"}, config.direction),
      el("nav", {"aria-label": "业务模块"}, links),
      el("div", {class: "rail-user"}, el("span", {}, Roles[user.role]),
        el("button", {class: "quiet", onclick: signOut, type: "button"}, "退出"))),
    el("main", {id: "content", class: "workspace", "data-route": route.id ? `${route.name}/${route.id}` : route.name}, page));
}
