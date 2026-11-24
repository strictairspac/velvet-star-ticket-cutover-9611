export function poll(action, signal, delay = 700) {
  let timer;
  async function refresh() {
    if (signal.aborted) return;
    if (await action() && !signal.aborted) timer = setTimeout(refresh, delay);
  }
  signal.addEventListener("abort", () => clearTimeout(timer), {once: true});
  timer = setTimeout(refresh, delay);
}
