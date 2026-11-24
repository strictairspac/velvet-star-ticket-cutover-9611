import { api } from "../api/workbench.js";
import { errorText, field } from "../components/common/fields.js";
import { empty, pageHeading, section } from "../components/common/panel.js";
import { table } from "../components/common/table.js";
import { submit } from "../hooks/submit.js";
import { navigate } from "../router/router.js";
import { el } from "../utils/dom.js";
import { time } from "../utils/format.js";

function queueForm(config, selected) {
  const form = el("form", {class: "queue-form"},
    field(config.parameter_label, el("input", {
      name: "parameter", type: "number", min: 1, max: config.max_parameter, required: true, value: config.default_parameter,
    })),
    el("button", {type: "submit"}, "提交试写"), errorText());
  submit(form, async values => {
    const run = await api.enqueue(selected.id, {parameter: Number(values.get("parameter"))});
    navigate(`runs/${run.id}`);
  });
  return form;
}

function supplementForm(selected, onChange) {
  const form = el("form", {class: "queue-form"},
    field("补票 JSON", el("textarea", {name: "tickets", rows: 5, required: true, spellcheck: "false"},
      '[\n  {"id": "N006", "workshop": "北间", "code": "OPAL-4", "serial": 8}\n]'),
      "转版准备期间登记；发布时会并入本卷同间判重。"),
    errorText(), el("button", {type: "submit"}, "登记补票"));
  submit(form, async values => {
    let tickets;
    try {
      tickets = JSON.parse(values.get("tickets"));
    } catch {
      throw new Error("补票 JSON 无法解析，请检查括号、引号和逗号");
    }
    await api.addSupplements(selected.id, {tickets});
    onChange();
  });
  return form;
}

function publishForm(config, selected, onChange) {
  const form = el("form", {class: "queue-form"},
    field(config.parameter_label, el("input", {
      name: "parameter", type: "number", min: 1, max: config.max_parameter, required: true,
      value: config.default_parameter,
    })),
    el("button", {type: "submit"}, "全卷发布新号"), errorText());
  submit(form, async values => {
    await api.publish(selected.id, {parameter: Number(values.get("parameter"))});
    onChange();
  });
  return form;
}

function publicationPanel(publication) {
  if (!publication) {
    return el("div", {class: "stack"},
      empty("尚未发布新号。试写确认后，在此一次性发布全卷。"),
      el("p", {class: "empty"}, "发布会把本卷原始工票与全部补票一起判重；任一张超出预算则整卷不发布。"));
  }
  return el("div", {class: "stack", "data-testid": "publication"},
    el("p", {}, `发布于 ${time(publication.published_at)} · ${publication.actor} · 改号 ${publication.changed_count} 张 · 通过试写 ${publication.verified_count} 张`),
    el("details", {}, el("summary", {}, "证据摘要"), el("code", {}, publication.digest)),
    table(["工票 ID", "工作间", "原票号", "新票号", "动作"], publication.issues.map(issue =>
      [issue.ticket_id, issue.workshop, issue.old_code, issue.new_code, issue.action]), "已发布新号"));
}

function supplementPanel(supplements) {
  if (!supplements.length) return empty("准备期间还没有登记补票。");
  return table(["工票 ID", "工作间", "票号", "登记顺序"], supplements.map(item =>
    [item.ticket_id, item.workshop, item.code, item.serial]), "已登记补票");
}

function registration(config, selected) {
  const data = selected ? JSON.stringify(selected.payload, null, 2) : "{}";
  const form = el("form", {id: "case-form"},
    field("名称", el("input", {name: "title", required: true, minlength: 2, maxlength: 120, value: selected ? `${selected.title} · 复演` : ""})),
    field("说明", el("input", {name: "description", maxlength: 420, value: selected?.description || ""})),
    field(`${config.unit}内容`, el("textarea", {name: "payload", spellcheck: "false", required: true, rows: 12}, data),
      selected ? "可以保留演示数据，也可以编辑 JSON 后保存。" : "输入业务 JSON。"),
    errorText(), el("button", {type: "submit"}, "保存资料"));
  submit(form, async values => {
    let payload;
    try {
      payload = JSON.parse(values.get("payload"));
    } catch {
      throw new Error("资料 JSON 无法解析，请检查括号、引号和逗号");
    }
    const entry = await api.createCase({title: values.get("title"), description: values.get("description"), payload});
    navigate(`cases/${entry.id}`);
  });
  return form;
}

export async function casesPage(config, user, route, refresh) {
  const [cases, published] = await Promise.all([api.cases(), api.publications()]);
  const selected = cases.find(item => item.id === route.id) ?? cases.at(-1);
  const operator = user.role === "operator";
  const publication = selected ? await api.publication(selected.id) : null;
  const supplements = selected ? await api.supplements(selected.id) : [];
  const switched = new Set(published.map(item => item.case_id));
  const volume = selected?.payload?.tickets ?? [];
  const reload = () => refresh();

  const directory = section("资料目录", cases.length ? table(["编号", "名称", "说明", "状态", "操作"], cases.map(item =>
    [item.code, item.title, item.description, switched.has(item.id) ? "已发布新号" : "准备中",
      el("a", {href: `#cases/${item.id}`, "aria-current": item.id === selected?.id ? "true" : null}, "选用")]), "资料目录") :
    empty("这里还没有资料。"));

  const current = section(selected ? selected.title : "等待选择资料", selected ?
    [el("p", {}, selected.description),
      operator ? queueForm(config, selected) : empty("当前账号可查看此资料。"),
      el("details", {}, el("summary", {}, "查看业务数据"),
        el("pre", {}, JSON.stringify(selected.payload, null, 2)))] :
    empty("先登记一条资料，再提交执行。"));

  const preparation = selected ? el("div", {class: "split case-split"},
    section("旧票卷宗", volume.length ? table(["工票 ID", "工作间", "票号", "登记顺序"], volume.map(item =>
      [item.id, item.workshop, item.code, item.serial]), "原卷工票") : empty("卷内暂无工票。")),
    section("补票登记", [supplementPanel(supplements),
      operator && !publication ? supplementForm(selected, reload) :
        publication ? empty("本卷已完成切换，不再接收补票。") :
          empty("当前账号可查看补票。")])) : null;

  const switchPanel = selected ? section("全卷发布", [
    publicationPanel(publication),
    operator && !publication ? publishForm(config, selected, reload) :
      publication ? null : empty("发布新号仅限资料操作员。"),
    publication ? el("p", {}, el("a", {href: "#evidence"}, "前往改号交接查号")) : null,
  ]) : null;

  return el("div", {class: "page"},
    pageHeading(config.modules[1], `${config.unit} · ${config.fixture}`),
    directory,
    el("div", {class: "split case-split"}, current,
      operator ? section("登记新资料", registration(config, selected)) : null),
    preparation,
    switchPanel);
}
