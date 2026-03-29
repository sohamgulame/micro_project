const API_BASE_URL = window.APP_CONFIG?.apiBaseUrl || "http://127.0.0.1:8000";
const API_URL = `${API_BASE_URL.replace(/\/$/, "")}/api/v1/latest`;
const REFRESH_INTERVAL_MS = 5000;

const elements = {
  status: document.getElementById("status"),
  spo2: document.getElementById("spo2"),
  heartRate: document.getElementById("heartRate"),
  temperature: document.getElementById("temperature"),
  riskLevel: document.getElementById("riskLevel"),
  conditions: document.getElementById("conditions"),
  explanation: document.getElementById("explanation"),
  updatedAt: document.getElementById("updatedAt"),
};

function setStatus(message, isError = false) {
  elements.status.textContent = message;
  elements.status.classList.toggle("error", isError);
}

function renderConditions(conditions) {
  elements.conditions.innerHTML = "";

  if (!conditions || conditions.length === 0) {
    const li = document.createElement("li");
    li.textContent = "No conditions returned.";
    elements.conditions.appendChild(li);
    return;
  }

  conditions.forEach((condition) => {
    const li = document.createElement("li");
    const confidence = Number(condition.confidence ?? 0).toFixed(2);
    li.textContent = `${condition.name} (${confidence})`;
    elements.conditions.appendChild(li);
  });
}

function renderDashboard(data) {
  elements.spo2.textContent = data.spo2 ?? "--";
  elements.heartRate.textContent = data.heart_rate ?? "--";
  elements.temperature.textContent = data.temperature ?? "--";

  const prediction = data.prediction ?? {};
  elements.riskLevel.textContent = prediction.risk_level ?? "--";
  elements.explanation.textContent = prediction.explanation ?? "No explanation available.";
  renderConditions(prediction.conditions);

  const updatedTime = data.timestamp
    ? new Date(data.timestamp).toLocaleString()
    : "--";
  elements.updatedAt.textContent = `Last updated: ${updatedTime}`;
  setStatus("Live", false);
}

function renderError(message) {
  elements.spo2.textContent = "--";
  elements.heartRate.textContent = "--";
  elements.temperature.textContent = "--";
  elements.riskLevel.textContent = "--";
  elements.explanation.textContent = message;
  renderConditions([]);
  elements.updatedAt.textContent = "Last updated: --";
  setStatus("Unavailable", true);
}

async function fetchLatestReading() {
  try {
    setStatus("Refreshing...");
    const response = await fetch(API_URL);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || "Failed to fetch data.");
    }

    const data = await response.json();
    renderDashboard(data);
  } catch (error) {
    renderError(error.message || "Unable to load health data.");
  }
}

fetchLatestReading();
setInterval(fetchLatestReading, REFRESH_INTERVAL_MS);
