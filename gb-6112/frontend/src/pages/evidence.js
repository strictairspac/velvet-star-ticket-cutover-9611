import { api } from "../api/workbench.js";
import { errorText, field } from "../components/common/fields.js";
import { empty, pageHeading, section } from "../components/common/panel.js";
import { resultTable, table } from "../components/common/table.js";
import { submit } from "../hooks/submit.js";
import { el } from "../utils/dom.js";
import { cell, download, time } from "../utils/format.js";

function reviewForm(id, saved) {
  const form = el("form", {id: "review-form"},
    field("复核意见", el("textarea", {name: "note", required: true, minlength: 3, maxlength: 500, rows: 3})),
    errorText(), el("button", {type: "submit"}, "签署复核"));
  submit(form, async values => saved(await api.submitReview(id, {note: values.get("note")})));
  return form;
}

function signature(review) {
  return el("div", {"data-testid": "reviewed", class: "signature"},
    el("strong", {}, `已签署 · ${review.actor}`), el("p", {}, review.note), el("time", {}, time(review.created_at)));
}

function lookupPanel() {
  const issue = errorText();
  const results = el("div", {class: "stack"});
  const query = el("input", {name: "ticket", required: true, maxlength: 16, placeholder: "例如 N002"});
  const form = el("form", {class: "queue-form"}, field("工票编号", query), issue,
    el("button", {type: "submit"}, "查号"));
  const codeIssue = errorText();
  const codeResults = el("div", {class: "stack"});
  const oldForm = el("form", {class: "queue-form"},
    field("工作间", el("input", {name: "workshop", required: true, maxlength: 32, placeholder: "例如 北间"})),
    field("旧票号", el("input", {name: "old", required: true, maxlength: 60, placeholder: "例如 eclat-27"})),
    codeIssue, el("button", {type: "submit"}, "查旧票号"));
  const show = (entries, target, message) => {
    target.replaceChildren(entries.length
      ? table(["工票卷", "工票 ID", "工作间", "原票号", "新票号", "状态"],
        entries.map(entry => [entry.case_title, entry.ticket_id, entry.workshop, entry.old_code,
          entry.new_code ?? "—", entry.published ? "已发布" : "准备中"]), "工票查号结果")
      : empty(message));
  };
  submit(form, async values => {
    const id = values.get("ticket").trim().toUpperCase();
    if (!/^[A-Z0-9]{1,16}$/.test(id)) throw new Error("工票 ID 仅接受 1 到 16 位大写字母或数字");
    show(await api.ticket(id), results, "此工票编号没有登记记录。");
  });
  submit(oldForm, async values => {
    const entries = await api.ticketByCode(values.get("workshop").trim(), values.get("old"));
    show(entries, codeResults, "此工作间没有该旧票号的登记记录。");
  });
  return section("查号交接",
    el("p", {class: "empty"}, "旧票号与所属工票的对应关系始终可查；新号只在全卷发布后显示。"),
    form, results, oldForm, codeResults);
}

export async function evidencePage(config, user, route) {
  const runs = (await api.runs()).filter(item => item.status === "done");
  const run = route.id ? await api.run(route.id) : runs[0];
  if (!run?.result) return el("div", {class: "page"},
    pageHeading(config.modules[3], null), empty("成功执行一个批次后可以查看、签核和下载证据。"),
    lookupPanel(), el("a", {href: "#runs"}, config.modules[2]));

  const review = await api.review(run.id);
  const issue = errorText();
  const button = el("button", {type: "button", onclick: async () => {
    button.disabled = true;
    issue.textContent = "";
    try {
      await download(await api.export(run.id), `evidence-${run.id}.json`);
    } catch (error) {
      issue.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  }}, "导出证据");
  const signing = el("div", {});
  signing.append(review ? signature(review) : user.role === "reviewer" ?
    reviewForm(run.id, data => signing.replaceChildren(signature(data))) : empty("待复核员签署。"));
  const options = el("select", {"aria-label": "选择已完成的批次", onchange: event => {
    location.hash = `evidence/${event.target.value}`;
  }}, runs.map(item => el("option", {value: item.id, selected: item.id === run.id}, `#${item.id} ${item.case_title}`)));
  return el("div", {class: "page evidence"},
    pageHeading(config.modules[3], run.case_title, button),
    issue, options,
    el("section", {class: "feature evidence-summary"}, el("div", {}, el("h2", {}, "批次判定"), el("p", {}, run.result.summary)),
      el("details", {}, el("summary", {}, "证据摘要"), el("code", {}, run.digest))),
    el("dl", {class: "metrics"}, Object.entries(run.result.metrics).map(([label, value]) =>
      el("div", {}, el("dt", {}, label), el("dd", {}, cell(value))))),
    section("业务结果明细", run.result.rows.length ? resultTable(run.result.rows) : empty("此批次无明细。")),
    lookupPanel(),
    section("复核签署", signing));
}
