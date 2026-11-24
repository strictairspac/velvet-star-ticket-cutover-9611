import { States } from "../../constants/states.js";
import { el } from "../../utils/dom.js";

export function status(value) {
  return el("span", {class: `status state-${value}`, "data-state": value}, States[value] || value);
}
