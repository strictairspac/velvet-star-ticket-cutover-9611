import { clearSession, session } from "../stores/session.js";

export async function request(path, {method = "GET", data, raw = false, signal} = {}) {
  const headers = new Headers();
  const current = session();
  if (current) headers.set("Authorization", `Bearer ${current.token}`);
  if (data !== undefined) headers.set("Content-Type", "application/json");
  const response = await fetch(`/api${path}`, {method, headers, signal, body: JSON.stringify(data)});
  if (response.ok) return raw ? response : response.json();
  const error = await response.json().catch(() => ({}));
  if (response.status === 401 && current) {
    clearSession();
    window.dispatchEvent(new Event("sessionchange"));
  }
  const detail = Array.isArray(error.detail)
    ? error.detail.map(entry => entry.msg).join("；")
    : error.detail;
  throw new Error(detail || `请求失败（${response.status}）`);
}
