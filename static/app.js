(function () {
  "use strict";

  const POLL_MS = 5000;
  const FETCH_OPTS = { credentials: "include", headers: { Accept: "application/json" } };

  const el = (id) => document.getElementById(id);
  let pollTimer = null;
  let pnlChart = null;
  let vaultLoaded = false;

  function setConn(ok, msg) {
    const n = el("connStatus");
    if (!n) return;
    n.textContent = msg || "";
    n.classList.toggle("reconnecting", !ok);
  }

  async function safeFetch(url) {
    try {
      const res = await fetch(url, FETCH_OPTS);
      if (!res.ok) throw new Error(res.status + " " + res.statusText);
      return { ok: true, data: await res.json() };
    } catch (e) {
      return { ok: false, error: e };
    }
  }

  function healthDot(status) {
    const s = (status || "").toLowerCase();
    if (s === "healthy") return "ok";
    if (s === "degraded") return "degraded";
    return "unknown";
  }

  function destroyPnlChart() {
    if (pnlChart) {
      try {
        pnlChart.destroy();
      } catch (_) {}
      pnlChart = null;
    }
  }

  function renderPnlChart(points) {
    const canvas = el("pnlChart");
    if (!canvas || typeof Chart === "undefined") return;

    const list = Array.isArray(points) ? points : [];
    const labels = list.map((_, i) => String(i + 1));
    const vals = list.map((p) => {
      if (p && typeof p === "object") {
        if (typeof p.cumulative_pnl === "number") return p.cumulative_pnl;
        if (typeof p.pnl === "number") return p.pnl;
        if (typeof p.y === "number") return p.y;
      }
      return null;
    });
    const data = vals.map((v) => (typeof v === "number" && !Number.isNaN(v) ? v : 0));

    destroyPnlChart();
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    pnlChart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Series",
            data,
            borderColor: "#58a6ff",
            backgroundColor: "rgba(88, 166, 255, 0.12)",
            fill: true,
            tension: 0.2,
            pointRadius: 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: "#8b949e", maxTicksLimit: 8 }, grid: { color: "#30363d" } },
          y: { ticks: { color: "#8b949e" }, grid: { color: "#30363d" } },
        },
      },
    });
  }

  function renderOpenRows(positions) {
    const tbody = el("openTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";
    const rows = Array.isArray(positions) ? positions : [];
    if (!rows.length) {
      const tr = document.createElement("tr");
      tr.innerHTML = '<td colspan="4" class="muted">No open positions</td>';
      tbody.appendChild(tr);
      return;
    }
    for (const p of rows) {
      const tr = document.createElement("tr");
      const sym = p.symbol != null ? String(p.symbol) : "—";
      const qty = p.qty != null ? String(p.qty) : "—";
      const up = p.unrealized_pnl != null ? Number(p.unrealized_pnl).toFixed(2) : "—";
      const sc = p.current_score != null ? String(p.current_score) : "—";
      tr.innerHTML = "<td>" + sym + "</td><td>" + qty + "</td><td>" + up + "</td><td>" + sc + "</td>";
      tbody.appendChild(tr);
    }
  }

  async function pollCommandCenter() {
    let allOk = true;

    const h = await safeFetch("/health");
    if (h.ok && h.data) {
      const st = h.data.status || "unknown";
      const dot = healthDot(st);
      const kpiH = el("kpiHealth");
      if (kpiH) {
        kpiH.innerHTML =
          '<span class="status-dot ' + dot + '"></span>' + st;
      }
      const sub = el("kpiHealthSub");
      if (sub) {
        sub.textContent =
          "Bot " + (h.data.bot_running ? "running" : "stopped") +
          " · Alpaca " + (h.data.alpaca_connected ? "up" : "down");
      }
    } else {
      allOk = false;
    }

    const m = await safeFetch("/metrics");
    if (m.ok && m.data) {
      const sn = m.data.strict_cohort_n;
      const kn = el("kpiStrictN");
      if (kn) kn.textContent = sn != null ? "Strict N=" + String(sn) : "—";
      const dr = m.data.DATA_READY;
      const kd = el("kpiDataReady");
      if (kd) {
        if (dr === true) kd.textContent = "DATA_READY: YES";
        else if (dr === false) kd.textContent = "DATA_READY: NO";
        else kd.textContent = "DATA_READY: unknown";
      }
      const fl = el("kpiFloor");
      if (fl) fl.textContent = m.data.strict_floor_epoch_utc || "—";

      const oc = el("kpiOpenCount");
      if (oc && m.data.open_position_count != null) {
        oc.textContent = String(m.data.open_position_count);
      }
      const dp = el("kpiDayPnl");
      if (dp && m.data.day_pnl_usd != null) {
        dp.textContent = "Day P&L $" + Number(m.data.day_pnl_usd).toFixed(2);
      }

      const pts = m.data.rolling_pnl_last_points;
      if (pts && pts.length) renderPnlChart(pts);
    } else {
      allOk = false;
    }

    const p = await safeFetch("/open_positions?limit=50");
    if (p.ok && p.data) {
      renderOpenRows(p.data.positions);
    } else {
      allOk = false;
    }

    setConn(allOk, allOk ? "" : "Reconnecting…");
  }

  async function loadVault() {
    const btn = el("vaultRefresh");
    const meta = el("vaultMeta");
    const tbody = el("vaultTableBody");
    if (btn) btn.disabled = true;
    try {
      const r = await safeFetch("/closed_trades?limit=50");
      if (!r.ok) throw r.error || new Error("fetch failed");
      const trades = r.data.closed_trades || [];
      if (meta) {
        meta.textContent =
          "(" +
          (r.data.count != null ? r.data.count : trades.length) +
          " shown, total loaded " +
          (r.data.count_total_loaded != null ? r.data.count_total_loaded : "—") +
          ")";
      }
      if (tbody) {
        tbody.innerHTML = "";
        if (!trades.length) {
          const tr = document.createElement("tr");
          tr.innerHTML = '<td colspan="5" class="muted">No rows</td>';
          tbody.appendChild(tr);
        } else {
          for (const t of trades) {
            const tr = document.createElement("tr");
            const ts = (t.timestamp || t.exit_timestamp || "").slice(0, 19);
            const sym = t.symbol != null ? String(t.symbol) : "—";
            const pnl = t.pnl_usd != null ? Number(t.pnl_usd).toFixed(2) : "—";
            const reason = (t.close_reason || "").slice(0, 40);
            const st = t.strict_alpaca_chain != null ? String(t.strict_alpaca_chain) : "—";
            tr.innerHTML =
              "<td>" +
              ts +
              "</td><td>" +
              sym +
              "</td><td>" +
              pnl +
              "</td><td>" +
              reason +
              "</td><td>" +
              st +
              "</td>";
            tbody.appendChild(tr);
          }
        }
      }
      vaultLoaded = true;
      setConn(true, "");
    } catch (e) {
      setConn(false, "Reconnecting…");
      if (tbody) {
        tbody.innerHTML = "";
        const tr = document.createElement("tr");
        tr.innerHTML =
          '<td colspan="5" class="muted">' +
          (e && e.message ? String(e.message) : "Load failed") +
          "</td>";
        tbody.appendChild(tr);
      }
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  function startPoll() {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(function () {
      const cc = el("panel-cc");
      if (cc && cc.classList.contains("active")) {
        try {
          void pollCommandCenter();
        } catch (_) {
          setConn(false, "Reconnecting…");
        }
      }
    }, POLL_MS);
  }

  function activateTab(which) {
    const cc = el("panel-cc");
    const vault = el("panel-vault");
    const tcc = el("tab-cc");
    const tv = el("tab-vault");
    const active = which === "vault";
    if (cc) {
      cc.classList.toggle("active", !active);
      cc.hidden = active;
    }
    if (vault) {
      vault.classList.toggle("active", active);
      vault.hidden = !active;
    }
    if (tcc) {
      tcc.classList.toggle("active", !active);
      tcc.setAttribute("aria-selected", String(!active));
    }
    if (tv) {
      tv.classList.toggle("active", active);
      tv.setAttribute("aria-selected", String(active));
    }
    if (active && !vaultLoaded) void loadVault();
  }

  el("tab-cc").addEventListener("click", function () {
    activateTab("cc");
  });
  el("tab-vault").addEventListener("click", function () {
    activateTab("vault");
  });
  el("vaultRefresh").addEventListener("click", function () {
    void loadVault();
  });

  void pollCommandCenter();
  startPoll();
})();
