import { el } from "../../utils/dom.js";

export function field(label, input, help) {
  return el("label", {class: "field"}, el("span", {}, label), input, help ? el("small", {}, help) : null);
}

export function errorText() {
  return el("p", {role: "alert", class: "feedback"});
}
