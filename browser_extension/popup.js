const API_BASE = "http://127.0.0.1:5000";
const REQUEST_TIMEOUT_MS = 12000;

const elements = {
  connectionDot: document.getElementById("connection-dot"),
  connectionText: document.getElementById("connection-text"),
  retryHealth: document.getElementById("retry-health"),
  urlInput: document.getElementById("url-input"),
  currentTabButton: document.getElementById("current-tab-btn"),
  scanButton: document.getElementById("scan-btn"),
  statusMessage: document.getElementById("status-message"),
  resultPanel: document.getElementById("result-panel"),
  emptyPanel: document.getElementById("empty-panel"),
  verdictHead: document.querySelector(".verdict-head"),
  verdictIcon: document.getElementById("verdict-icon"),
  verdictEyebrow: document.getElementById("verdict-eyebrow"),
  verdictTitle: document.getElementById("verdict-title"),
  resultExplanation: document.getElementById("result-explanation"),
  phishingScore: document.getElementById("phishing-score"),
  scoreProgress: document.getElementById("score-progress"),
  scoreFill: document.getElementById("score-fill"),
  rawModelNote: document.getElementById("raw-model-note"),
  hostname: document.getElementById("hostname-value"),
  registeredDomain: document.getElementById("registered-domain-value"),
  publicSuffix: document.getElementById("public-suffix-value"),
  subdomainCount: document.getElementById("subdomain-count-value"),
  pathDepth: document.getElementById("path-depth-value"),
  queryCount: document.getElementById("query-count-value"),
  domainIndicators: document.getElementById("domain-indicators"),
  urlIndicators: document.getElementById("url-indicators")
};

function setStatus(message, kind = "") {
  elements.statusMessage.textContent = message;
  elements.statusMessage.className = `status-message${kind ? ` ${kind}` : ""}`;
}

function setConnection(state, message) {
  elements.connectionDot.className = `connection-dot ${state}`;
  elements.connectionText.textContent = message;
}

async function requestJson(endpoint, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      signal: controller.signal,
      cache: "no-store"
    });
    let payload;
    try {
      payload = await response.json();
    } catch {
      throw new Error(`The local server returned an unreadable response (HTTP ${response.status}).`);
    }
    if (!response.ok) {
      throw new Error(payload && typeof payload.error === "string"
        ? payload.error
        : `The local server returned HTTP ${response.status}.`);
    }
    return payload;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("The local model did not respond in time. Check the backend terminal and try again.");
    }
    if (error instanceof TypeError) {
      throw new Error("Cannot connect to the local Python backend. Start app.py and confirm it is running at 127.0.0.1:5000.");
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

async function checkBackend() {
  setConnection("", "Checking local model...");
  try {
    const health = await requestJson("/health");
    if (health.model_loaded) {
      setConnection("online", `Local model ready${health.model_name ? `, ${health.model_name}` : ""}`);
    } else {
      setConnection("offline", "Backend is running, but the model is not loaded");
    }
  } catch (error) {
    setConnection("offline", "Python backend unavailable");
    setStatus(`${error.message} Run .\\.venv\\Scripts\\python.exe app.py from the project folder.`, "error");
  }
}

function normalizedUrl(value) {
  const raw = value.trim();
  if (!raw) throw new Error("Enter a URL or use the current tab button.");
  if (!/^https?:\/\//i.test(raw)) {
    throw new Error("Include http:// or https:// at the start of the URL.");
  }
  let parsed;
  try {
    parsed = new URL(raw);
  } catch {
    throw new Error("That URL format is invalid. Check the hostname and try again.");
  }
  if (!parsed.hostname) throw new Error("Enter a complete URL with a hostname.");
  if (parsed.username || parsed.password) {
    throw new Error("This URL contains credentials before the hostname. Review it carefully instead of scanning it here.");
  }
  if (raw.length > 2048) throw new Error("The URL is too long. Enter a URL under 2,048 characters.");
  return raw;
}

async function getCurrentTabUrl() {
  const tabs = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
  const tab = tabs && tabs[0];
  if (!tab || typeof tab.url !== "string") {
    throw new Error("Could not read the current tab URL. Click a regular website tab and try again.");
  }
  if (!/^https?:\/\//i.test(tab.url)) {
    throw new Error("This browser page cannot be scanned, such as a browser settings page or extension store. Open a regular website or paste a URL.");
  }
  return tab.url;
}

function fillList(listElement, values) {
  listElement.replaceChildren();
  const items = Array.isArray(values) && values.length ? values : ["No separate indicators were returned."];
  for (const value of items) {
    const li = document.createElement("li");
    li.textContent = String(value);
    listElement.appendChild(li);
  }
}

function displayText(element, value, fallback = "Not available") {
  element.textContent = value === undefined || value === null || value === "" ? fallback : String(value);
}

function renderResult(data) {
  const label = typeof data.result_label === "string" ? data.result_label : (data.is_phishing ? "Potential phishing URL" : "No phishing indicators detected by the model");
  const isPhishing = data.is_phishing === true;
  const needsReview = data.review_required === true || /needs review/i.test(label);
  const recognized = data.recognized_homepage === true || /recognized major-domain homepage/i.test(label);

  elements.verdictHead.className = "verdict-head";
  if (isPhishing) {
    elements.verdictHead.classList.add("phishing");
    elements.verdictIcon.textContent = "!";
  } else if (needsReview) {
    elements.verdictHead.classList.add("review");
    elements.verdictIcon.textContent = "?";
  } else if (recognized) {
    elements.verdictHead.classList.add("recognized");
    elements.verdictIcon.textContent = "✓";
  } else {
    elements.verdictHead.classList.add("no-indicators");
    elements.verdictIcon.textContent = "✓";
  }

  elements.verdictEyebrow.textContent = isPhishing ? "WARNING" : needsReview ? "MIXED SIGNALS" : recognized ? "EXACT HOMEPAGE MATCH" : "MODEL RESULT";
  displayText(elements.verdictTitle, label, "Analysis complete");
  displayText(elements.resultExplanation, data.explanation, "The model returned a result without a detailed explanation.");

  const score = Number(data.phishing_score ?? data.confidence);
  if (Number.isFinite(score)) {
    const safeScore = Math.max(0, Math.min(100, score));
    elements.phishingScore.textContent = `${safeScore.toFixed(2)}%`;
    elements.scoreFill.style.width = `${safeScore}%`;
    elements.scoreFill.className = `score-fill${safeScore >= 70 ? " high" : safeScore < 30 ? " low" : ""}`;
    elements.scoreProgress.setAttribute("aria-valuenow", String(Math.round(safeScore)));
  } else {
    elements.phishingScore.textContent = "Not available";
    elements.scoreFill.style.width = "0%";
    elements.scoreProgress.setAttribute("aria-valuenow", "0");
  }

  if (data.model_is_phishing === true && data.is_phishing === false) {
    elements.rawModelNote.textContent = "The raw model predicted phishing, but a separate domain context rule changed the final label. Review the URL carefully. The site is not guaranteed safe.";
    elements.rawModelNote.classList.remove("hidden");
  } else {
    elements.rawModelNote.textContent = "";
    elements.rawModelNote.classList.add("hidden");
  }

  const domain = data.domain_analysis || {};
  const url = data.url_analysis || {};
  displayText(elements.hostname, domain.hostname);
  displayText(elements.registeredDomain, domain.registered_domain);
  displayText(elements.publicSuffix, domain.public_suffix);
  displayText(elements.subdomainCount, domain.subdomain_count);
  displayText(elements.pathDepth, url.path_depth);
  displayText(elements.queryCount, url.query_parameter_count);
  fillList(elements.domainIndicators, domain.indicators);
  fillList(elements.urlIndicators, url.indicators);

  elements.emptyPanel.classList.add("hidden");
  elements.resultPanel.classList.remove("hidden");
}

async function scanUrl() {
  let url;
  try {
    url = normalizedUrl(elements.urlInput.value);
  } catch (error) {
    setStatus(error.message, "error");
    return;
  }

  elements.scanButton.disabled = true;
  elements.currentTabButton.disabled = true;
  elements.scanButton.textContent = "Analyzing...";
  setStatus("Analyzing domain and URL patterns with the local model...");

  try {
    const data = await requestJson("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });
    renderResult(data);
    setStatus("Analysis complete. Review the findings and limitations below.", "success");
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    elements.scanButton.disabled = false;
    elements.currentTabButton.disabled = false;
    elements.scanButton.textContent = "Analyze URL";
  }
}

async function useCurrentTab() {
  try {
    const url = await getCurrentTabUrl();
    elements.urlInput.value = url;
    setStatus("Current tab URL loaded. Select Analyze URL to scan it.", "success");
  } catch (error) {
    setStatus(error.message, "error");
  }
}

 elements.scanButton.addEventListener("click", scanUrl);
 elements.currentTabButton.addEventListener("click", useCurrentTab);
 elements.retryHealth.addEventListener("click", checkBackend);
 elements.urlInput.addEventListener("keydown", (event) => {
   if ((event.ctrlKey || event.metaKey) && event.key === "Enter") scanUrl();
 });

(async function initializePopup() {
  await checkBackend();
  try {
    const tabs = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
    const currentUrl = tabs?.[0]?.url;
    if (typeof currentUrl === "string" && /^https?:\/\//i.test(currentUrl)) {
      elements.urlInput.value = currentUrl;
    }
  } catch {
    // User can still paste a URL manually if the browser does not expose a current tab.
  }
})();
