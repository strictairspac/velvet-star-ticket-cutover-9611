const date = new Intl.DateTimeFormat("zh-CN", {dateStyle: "short", timeStyle: "short"});

export function time(seconds) {
  return seconds ? date.format(new Date(seconds * 1000)) : "—";
}

export function cell(value) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  if (typeof value === "boolean") return value ? "是" : "否";
  return String(value);
}

export async function download(response, filename) {
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}
