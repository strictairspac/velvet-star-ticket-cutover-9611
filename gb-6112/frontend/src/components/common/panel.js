import { el } from "../../utils/dom.js";

export function section(title, ...children) {
  return el("section", {class: "panel"}, el("h2", {}, title), children);
}

export function pageHeading(title, explanation, action) {
  return el("header", {class: "page-heading"},
    el("div", {}, el("h1", {}, title), explanation && el("p", {}, explanation)), action || null);
}

export function empty(message) {
  return el("p", {class: "empty"}, message);
}
