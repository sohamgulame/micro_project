const API_BASE_URL = window.APP_CONFIG?.apiBaseUrl || "http://127.0.0.1:8000";
const API_PREFIX = API_BASE_URL.replace(/\/$/, "") + "/api/v1";
const REFRESH_INTERVAL_MS = 5000;

const authSection = document.getElementById("authSection");
const appSection = document.getElementById("appSection");
const authMessage = document.getElementById("authMessage");
const loginForm = document.getElementById("loginForm");
const signupForm = document.getElementById("signupForm");
const showLoginBtn = document.getElementById("showLoginBtn");
const showSignupBtn = document.getElementById("showSignupBtn");
const dashboardTabBtn = document.getElementById("dashboardTabBtn");
const historyTabBtn = document.getElementById("historyTabBtn");
const dashboardView = document.getElementById("dashboardView");
const historyView = document.getElementById("historyView");
const logoutBtn = document.getElementById("logoutBtn");
const userSummary = document.getElementById("userSummary");
const deviceKeyText = document.getElementById("deviceKeyText");
const historyTableBody = document.getElementById("historyTableBody");
const historyMessage = document.getElementById("historyMessage");

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

let refreshTimer = null;

function getToken() {
  return localStorage.getItem("auth_token");
}

function getUser() {
  const raw = localStorage.getItem("auth_user");
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function setSession(token, user) {
  localStorage.setItem("auth_token", token);
  localStorage.setItem("auth_user", JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem("auth_token");
  localStorage.removeItem("auth_user");
}

function setStatus(message, isError = false) {
  elements.status.textContent = message;
  elements.status.classList.toggle("error", isError);
}

function setAuthMessage(message, isError = true) {
  authMessage.textContent = message || "";
  authMessage.style.color = isError ? "#a53f3f" : "#1e7d58";
}

function showLogin() {
  showLoginBtn.classList.add("active");
  showSignupBtn.classList.remove("active");
  loginForm.classList.remove("hidden");
  signupForm.classList.add("hidden");
}

function showSignup() {
  showSignupBtn.classList.add("active");
  showLoginBtn.classList.remove("active");
  signupForm.classList.remove("hidden");
  loginForm.classList.add("hidden");
}

function showDashboardTab() {
  dashboardTabBtn.classList.add("active");
  historyTabBtn.classList.remove("active");
  dashboardView.classList.remove("hidden");
  historyView.classList.add("hidden");
}

function showHistoryTab() {
  historyTabBtn.classList.add("active");
  dashboardTabBtn.classList.remove("active");
  historyView.classList.remove("hidden");
  dashboardView.classList.add("hidden");
}

function applyAuthState() {
  const token = getToken();
  const user = getUser();
  if (!token || !user) {
    authSection.classList.remove("hidden");
    appSection.classList.add("hidden");
    if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
    return;
  }

  authSection.classList.add("hidden");
  appSection.classList.remove("hidden");
  userSummary.textContent = `${user.full_name} (${user.email})`;
  deviceKeyText.textContent = `Device Key: ${user.device_api_key}`;

  fetchLatestReading();
  fetchHistory();

  if (refreshTimer) {
    clearInterval(refreshTimer);
  }
  refreshTimer = setInterval(fetchLatestReading, REFRESH_INTERVAL_MS);
}

async function apiRequest(path, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true",
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_PREFIX}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message = errorData.detail || errorData.message || "Request failed.";
    throw new Error(message);
  }

  return response.json();
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

function renderHistory(items) {
  historyTableBody.innerHTML = "";

  if (!items.length) {
    historyMessage.textContent = "No readings found for this account yet.";
    return;
  }

  historyMessage.textContent = `Total readings: ${items.length}`;

  items.forEach((reading) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${new Date(reading.timestamp).toLocaleString()}</td>
      <td>${reading.spo2}</td>
      <td>${reading.heart_rate}</td>
      <td>${reading.temperature}</td>
      <td>${reading.prediction?.risk_level || "--"}</td>
    `;
    historyTableBody.appendChild(tr);
  });
}

async function fetchLatestReading() {
  try {
    setStatus("Refreshing...");
    const data = await apiRequest("/latest", { method: "GET" });
    renderDashboard(data);
  } catch (error) {
    if (String(error.message || "").toLowerCase().includes("authentication")) {
      clearSession();
      applyAuthState();
      return;
    }
    renderError(error.message || "Unable to load health data.");
  }
}

async function fetchHistory() {
  try {
    const data = await apiRequest("/history", { method: "GET" });
    renderHistory(data.readings || []);
  } catch (error) {
    historyMessage.textContent = error.message || "Unable to load history.";
  }
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setAuthMessage("");

  try {
    const payload = {
      email: document.getElementById("loginEmail").value.trim(),
      password: document.getElementById("loginPassword").value,
    };

    const data = await apiRequest("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    setSession(data.access_token, data.user);
    loginForm.reset();
    applyAuthState();
  } catch (error) {
    setAuthMessage(error.message || "Login failed.", true);
  }
});

signupForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setAuthMessage("");

  try {
    const payload = {
      full_name: document.getElementById("signupName").value.trim(),
      email: document.getElementById("signupEmail").value.trim(),
      password: document.getElementById("signupPassword").value,
    };

    const data = await apiRequest("/auth/signup", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    setSession(data.access_token, data.user);
    signupForm.reset();
    setAuthMessage("Account created successfully.", false);
    applyAuthState();
  } catch (error) {
    setAuthMessage(error.message || "Sign up failed.", true);
  }
});

showLoginBtn.addEventListener("click", showLogin);
showSignupBtn.addEventListener("click", showSignup);
dashboardTabBtn.addEventListener("click", showDashboardTab);
historyTabBtn.addEventListener("click", () => {
  showHistoryTab();
  fetchHistory();
});

logoutBtn.addEventListener("click", () => {
  clearSession();
  showLogin();
  showDashboardTab();
  applyAuthState();
});

applyAuthState();
