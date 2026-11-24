export function submit(form, action) {
  const button = form.querySelector("button[type=submit]");
  const feedback = form.querySelector("[role=alert]");
  form.addEventListener("submit", async event => {
    event.preventDefault();
    feedback.textContent = "";
    button.disabled = true;
    try {
      await action(new FormData(form));
    } catch (error) {
      feedback.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
}
