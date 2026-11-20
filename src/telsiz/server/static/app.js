"use strict";

// Telsiz subtitle screen: receives VoiceEvents over a WebSocket and shows
// the newest translation large at the bottom. No build step, no dependencies.

(() => {
  const MAX_LINES = 30;
  const SCALE_STEPS = [0.75, 0.85, 1, 1.15, 1.3, 1.5, 1.75, 2];

  const turkish = (navigator.language || "tr").toLowerCase().startsWith("tr");
  const t = turkish
    ? { live: "Bağlı", connecting: "Bağlanıyor", lost: "Bağlantı koptu, yeniden deneniyor",
        denied: "Erişim reddedildi: QR kodu bilgisayardan yeniden okut", noTranslation: "çeviri yok",
        seconds: "sn" }
    : { live: "Connected", connecting: "Connecting", lost: "Connection lost, retrying",
        denied: "Access denied: scan the QR code on the PC again", noTranslation: "no translation",
        seconds: "s" };
  if (!turkish) {
    document.documentElement.lang = "en";
    document.getElementById("empty").textContent =
      "Translations appear here when your teammates speak.";
    document.getElementById("toggle-original").textContent = "Original";
    document.getElementById("open-phone").textContent = "Open on phone";
    document.getElementById("smaller").setAttribute("aria-label", "Smaller text");
    document.getElementById("bigger").setAttribute("aria-label", "Larger text");
    const pair = document.getElementById("pair");
    pair.querySelector("h2").textContent = "Open on phone";
    pair.querySelector("p").textContent =
      "Your phone must be on the same Wi-Fi network as this PC. Scan the code with the camera.";
    pair.querySelector(".pair-note").textContent =
      "The link contains an access key for this session only; do not share it.";
    pair.querySelector("#pair-qr").alt = "QR code for the phone link";
    pair.querySelector("form button").textContent = "Close";
  }

  const feed = document.getElementById("feed");
  const empty = document.getElementById("empty");
  const signal = document.getElementById("signal");
  const signalText = document.getElementById("signal-text");
  const seen = new Set();

  // --- per-device preferences (kept in this browser only) -----------------------
  const store = {
    get(key, fallback) {
      try { const v = localStorage.getItem(key); return v === null ? fallback : JSON.parse(v); }
      catch { return fallback; }
    },
    set(key, value) {
      try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* private mode */ }
    },
  };

  let scaleIndex = store.get("telsiz.scale", SCALE_STEPS.indexOf(1));
  const applyScale = () => {
    scaleIndex = Math.max(0, Math.min(SCALE_STEPS.length - 1, scaleIndex));
    document.documentElement.style.setProperty("--scale", SCALE_STEPS[scaleIndex]);
    store.set("telsiz.scale", scaleIndex);
  };
  document.getElementById("smaller").addEventListener("click", () => { scaleIndex--; applyScale(); });
  document.getElementById("bigger").addEventListener("click", () => { scaleIndex++; applyScale(); });
  applyScale();

  const originalButton = document.getElementById("toggle-original");
  const applyOriginal = (show) => {
    document.body.classList.toggle("hide-original", !show);
    originalButton.setAttribute("aria-pressed", String(show));
    store.set("telsiz.original", show);
  };
  originalButton.addEventListener("click", () =>
    applyOriginal(originalButton.getAttribute("aria-pressed") !== "true"));
  applyOriginal(store.get("telsiz.original", true));

  // --- rendering ------------------------------------------------------------------
  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;   // never innerHTML: text is untrusted
    return node;
  };

  function render(event, isLive) {
    if (event.type !== "voice" || seen.has(event.id)) return;
    seen.add(event.id);
    empty.remove();  // removed, not hidden: the first line must be the first child

    const sameLanguage = event.source_lang === event.target_lang;
    const shown = event.translated ?? event.original;

    const row = el("article", "msg");
    row.append(el("span", "channel", String(event.source_lang || "?").toUpperCase()));
    row.append(el("p", "said", shown));

    if (!sameLanguage) {
      // Without a translation the big line already shows the original text.
      const orig = event.translated == null
        ? el("p", "orig", "")
        : el("p", "orig", event.original);
      if (event.translated == null) orig.append(el("span", "note", `(${t.noTranslation})`));
      const seconds = (event.latency_ms / 1000).toFixed(1);
      orig.append(el("span", "meta", `${seconds} ${t.seconds}`));
      row.append(orig);
    }

    feed.querySelector(".msg.is-new")?.classList.remove("is-new");
    if (isLive) row.classList.add("is-new");
    feed.append(row);
    while (feed.querySelectorAll(".msg").length > MAX_LINES) feed.querySelector(".msg").remove();
    feed.scrollTop = feed.scrollHeight;
  }

  // --- connection -----------------------------------------------------------------
  function setSignal(state, text) {
    signal.dataset.state = state;
    signalText.textContent = text;
  }

  let retryDelay = 1000;
  let historyDone = false;

  function connect() {
    const scheme = location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${scheme}://${location.host}/ws${location.search}`);
    let opened = false;
    historyDone = false;

    socket.addEventListener("open", () => {
      opened = true;
      retryDelay = 1000;
      setSignal("live", t.live);
      // History arrives in one burst right after connecting; animate only later lines.
      setTimeout(() => { historyDone = true; }, 300);
    });
    socket.addEventListener("message", (message) => {
      try { render(JSON.parse(message.data), historyDone); } catch { /* ignore bad frames */ }
    });
    socket.addEventListener("close", (closeEvent) => {
      // 1008: the server refused this page (missing token or foreign origin).
      // Browsers usually report a refused handshake as 1006, so keep retrying then.
      if (closeEvent.code === 1008) { setSignal("lost", t.denied); return; }
      setSignal(opened ? "lost" : "connecting", opened ? t.lost : t.connecting);
      setTimeout(connect, retryDelay);
      retryDelay = Math.min(retryDelay * 2, 10000);
    });
  }
  connect();

  // --- phone pairing (only answered on the PC itself) ----------------------------
  const phoneButton = document.getElementById("open-phone");
  const dialog = document.getElementById("pair");
  fetch("/api/pairing")
    .then((r) => (r.ok ? r.json() : null))
    .then((info) => {
      if (!info || !info.phone_url) return;
      phoneButton.hidden = false;
      phoneButton.addEventListener("click", () => {
        document.getElementById("pair-qr").src = "/qr.svg";
        document.getElementById("pair-url").textContent = info.phone_url;
        dialog.showModal();
      });
    })
    .catch(() => {});
})();
