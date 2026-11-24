import { api } from "../api/workbench.js";
import { validateConfig } from "../types/workbench.js";
let configuration;

export async function config() {
  if (!configuration) configuration = validateConfig(await api.config());
  return configuration;
}
