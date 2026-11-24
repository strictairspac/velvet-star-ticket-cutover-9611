const routes = ["overview", "cases", "runs", "evidence"];

export function activeRoute() {
  const [name, id] = (location.hash.slice(1) || "overview").split("/");
  return {name: routes.includes(name) ? name : "overview", id: /^\d+$/.test(id || "") ? Number(id) : null};
}

export function navigate(route) {
  location.hash = route;
}

export { routes };
