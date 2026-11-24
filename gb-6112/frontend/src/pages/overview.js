import { api } from "../api/workbench.js";
import { empty, pageHeading, section } from "../components/common/panel.js";
import { status } from "../components/common/status.js";
import { table } from "../components/common/table.js";
import { Actions } from "../constants/states.js";
import { el } from "../utils/dom.js";
import { time } from "../utils/format.js";

export async function overview(config) {
  const [cases, runs, audit] = await Promise.all([api.cases(), api.runs(), api.audit()]);
  const latest = runs[0];
  return el("div", {class: "page overview"},
    pageHeading(config.modules[0], config.team, el("a", {class: "button", href: "#cases"}, config.modules[1])),
    el("div", {class: "feature"},
      el("div", {}, el("h2", {}, config.title), el("p", {}, config.description)),
      el("aside", {}, el("h3", {}, config.direction), el("p", {}, config.mechanism))),
    el("div", {class: "split"},
      section(`现有${config.unit}`,
        cases.length ? table(["编号", "名称", "登记人"], cases.slice(0, 4).map(item => [item.code, item.title, item.created_by]), "近期资料") : empty("进入资料页登记第一条资料。")),
      section("最近执行", latest ?
        el("div", {class: "stack"}, status(latest.status), el("strong", {}, latest.case_title),
          el("a", {href: `#runs/${latest.id}`}, "查看执行进度")) :
        empty("选择演示资料并提交执行，此处会显示处理进度。"))),
    section("操作记录", audit.length ?
      table(["动作", "账号", "对象编号", "时间"], audit.slice(0, 8).map(item =>
        [Actions[item.action] || item.action, item.actor, item.entity_id, time(item.created_at)]), "审计操作记录") :
      empty("登记、执行与签核会留下操作记录。")));
}
