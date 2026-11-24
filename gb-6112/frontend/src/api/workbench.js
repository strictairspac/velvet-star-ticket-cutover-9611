import { request } from "./http.js";

export const api = {
  config: () => request("/workbench"),
  login: data => request("/auth/login", {method: "POST", data}),
  cases: () => request("/cases"),
  createCase: data => request("/cases", {method: "POST", data}),
  runs: () => request("/runs"),
  run: (id, signal) => request(`/runs/${id}`, {signal}),
  enqueue: (id, data) => request(`/cases/${id}/runs`, {method: "POST", data}),
  review: id => request(`/runs/${id}/review`),
  submitReview: (id, data) => request(`/runs/${id}/review`, {method: "POST", data}),
  export: id => request(`/runs/${id}/export`, {raw: true}),
  supplements: id => request(`/cases/${id}/supplements`),
  addSupplements: (id, data) => request(`/cases/${id}/supplements`, {method: "POST", data}),
  publications: () => request("/publications"),
  publication: id => request(`/cases/${id}/publication`),
  publish: (id, data) => request(`/cases/${id}/publication`, {method: "POST", data}),
  ticket: id => request(`/tickets/${encodeURIComponent(id)}`),
  ticketByCode: (workshop, code) => request(`/tickets?${new URLSearchParams({workshop, code})}`),
  audit: () => request("/audit", {signal: AbortSignal.timeout(5000)}),
};
