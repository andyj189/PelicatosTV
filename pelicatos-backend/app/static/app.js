const statusBox = document.querySelector("#status");
const tokenOutput = document.querySelector("#token-output");

function showStatus(message, isError = false) {
  statusBox.textContent = message;
  statusBox.style.borderColor = isError ? "#9b302b" : "#bc512d";
}

async function sendRequest(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || `Error HTTP ${response.status}`);
  }
  return data;
}

document.querySelector("#register-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  try {
    const data = await sendRequest("/auth/register", Object.fromEntries(form));
    showStatus(`${data.mensaje}. Ahora puedes iniciar sesión.`);
    event.currentTarget.reset();
  } catch (error) {
    showStatus(error.message, true);
  }
});

document.querySelector("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  try {
    const data = await sendRequest("/auth/login", Object.fromEntries(form));
    tokenOutput.textContent = `Token recibido:\n${data.access_token}`;
    showStatus("Login correcto: la API devolvió un token.");
  } catch (error) {
    tokenOutput.textContent = "";
    showStatus(error.message, true);
  }
});
