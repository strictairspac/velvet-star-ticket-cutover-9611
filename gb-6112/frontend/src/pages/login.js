import { api } from "../api/workbench.js";
import { errorText, field } from "../components/common/fields.js";
import { submit } from "../hooks/submit.js";
import { saveSession } from "../stores/session.js";
import { el } from "../utils/dom.js";

export function login(config, signedIn) {
  const form = el("form", {id: "login-form"},
    field("账号", el("input", {name: "username", autocomplete: "username", required: true, maxlength: 48})),
    field("口令", el("input", {name: "password", type: "password", autocomplete: "current-password", required: true, maxlength: 160})),
    errorText(), el("button", {type: "submit"}, "进入工作台"));
  submit(form, async values => {
    saveSession(await api.login(Object.fromEntries(values)));
    signedIn();
  });
  return el("main", {class: "login"},
    el("section", {class: "login-story"},
      el("p", {class: "overline"}, config.team),
      el("h1", {}, config.title),
      el("p", {class: "intro"}, config.description),
      el("dl", {class: "login-data"},
        el("div", {}, el("dt", {}, "业务方向"), el("dd", {}, config.direction)),
        el("div", {}, el("dt", {}, "运行环境"), el("dd", {}, config.engine))),
      el("div", {class: "diagram", "aria-label": "业务处理步骤"}, config.facts.map(label => el("span", {}, label)))),
    el("section", {class: "login-access"},
      el("h2", {}, "工作台登录"), form,
      el("details", {}, el("summary", {}, "演示账号"),
        el("p", {}, "operator · reviewer · viewer"),
        el("p", {}, "共用口令 Demo-DbWorkbench-2026"))));
}
