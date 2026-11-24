const KEY = "db-workbench-session";

export function session() {
  return JSON.parse(sessionStorage.getItem(KEY) || "null");
}

export function saveSession(data) {
  sessionStorage.setItem(KEY, JSON.stringify(data));
}

export function clearSession() {
  sessionStorage.removeItem(KEY);
}
