import { el } from "../../utils/dom.js";
import { cell } from "../../utils/format.js";

export function table(headings, rows, label) {
  return el("div", {class: "table-scroll", tabindex: 0, "aria-label": label, role: "region"},
    el("table", {},
      el("thead", {}, el("tr", {}, headings.map(text => el("th", {scope: "col"}, text)))),
      el("tbody", {}, rows.map(row => el("tr", {}, row.map(value => el("td", {}, value instanceof Node ? value : cell(value))))))));
}

export function resultTable(records) {
  const keys = [...new Set(records.flatMap(Object.keys))];
  return table(keys, records.map(record => keys.map(key => record[key])), "业务结果明细");
}
