(function () {
  "use strict";

  const POLL_MS = 60000;
  const FETCH_OPTS = { credentials: "include", headers: { Accept: "application/json" } };

  const el = (id) => document.getElementById(id);
  let pollTimer = null;
  let pnlChart = null;
  let vaultLoaded = false;
  /** @type {{ t: number, equity: number, src?: string }[]} */
  let equityTrail = [];
  let rollingHistoryFetched = false;
  let lastChartSig = "";

  const moneyFmt = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  function formatMoney(n) {
    if (n === null || n === undefined || n === "") return "—";
    const x = Number(n);
    if (Number.isNaN(x)) return "—";
    return moneyFmt.format(x);
  }

  function formatPct(n) {
    if (n === null || n === undefined || n === "") return "—";
    const x = Number(n);
    if (Number.isNaN(x)) return "—";
    const s = x.toFixed(2) + "%";
    return s;
  }

  function pnlClass(n) {
    const x = Number(n);
    if (Number.isNaN(x) || x === 0) return "pnl-flat";
    return x > 0 ? "pnl-pos" : "pnl-neg";
  }

  function spanMoney(n) {
    const c = pnlClass(n);
    const v = formatMoney(n);
    return '<span class="' + c + '">' + v + "</span>";
  }

  function spanPct(n) {
    const c = pnlClass(n);
    const v = formatPct(n);
    return '<span class="' + c + '">' + v + "</span>";
  }

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

  function equityFromRollingPoint(p) {
    if (!p || typeof p !== "object") return null;
    var keys = [
      "equity",
      "portfolio_value",
      "account_equity",
      "total_value",
      "net_liquidation",
      "cumulative_pnl",
      "pnl",
      "y",
    ];
    for (var i = 0; i < keys.length; i++) {
      var k = keys[i];
      if (typeof p[k] === "number" && !Number.isNaN(p[k])) return p[k];
      if (p[k] != null && p[k] !== "" && !Number.isNaN(Number(p[k]))) return Number(p[k]);
    }
    return null;
  }

  function mergeSamplesFromRollingJson(points) {
    if (!Array.isArray(points)) return;
    for (var i = 0; i < points.length; i++) {
      var p = points[i];
      var eq = equityFromRollingPoint(p);
      if (eq === null) continue;
      var tsRaw = p.ts || p.timestamp || "";
      var t = tsRaw ? Date.parse(tsRaw) : NaN;
      if (Number.isNaN(t)) continue;
      var found = -1;
      for (var j = 0; j < equityTrail.length; j++) {
        if (Math.abs(equityTrail[j].t - t) < 500) {
          found = j;
          break;
        }
      }
      if (found >= 0) equityTrail[found] = { t: t, equity: eq, src: "rolling_file" };
      else equityTrail.push({ t: t, equity: eq, src: "rolling_file" });
    }
    equityTrail.sort(function (a, b) {
      return a.t - b.t;
    });
    while (equityTrail.length > 4000) equityTrail.shift();
  }

  function appendLivePortfolioEquity(totalValue) {
    var y = Number(totalValue);
    if (Number.isNaN(y)) return;
    var t = Date.now();
    var last = equityTrail[equityTrail.length - 1];
    if (last && last.src === "live_poll" && t - last.t < 3500 && last.equity === y) return;
    equityTrail.push({ t: t, equity: y, src: "live_poll" });
    while (equityTrail.length > 4000) equityTrail.shift();
  }

  async function ensureRollingHistoryOnce() {
    if (rollingHistoryFetched) return;
    rollingHistoryFetched = true;
    try {
      var r = await safeFetch("/api/rolling_pnl_5d");
      if (r.ok && r.data && Array.isArray(r.data.points)) mergeSamplesFromRollingJson(r.data.points);
    } catch (_) {}
  }

  function hydrateTrailFromSession() {
    try {
      var raw = sessionStorage.getItem("equityTrailV1");
      if (!raw) return;
      var arr = JSON.parse(raw);
      if (Array.isArray(arr) && arr.length) {
        equityTrail = arr
          .filter(function (x) {
            return x && typeof x.t === "number" && typeof x.equity === "number";
          })
          .map(function (x) {
            return { t: x.t, equity: x.equity, src: x.src || "session" };
          });
      }
    } catch (_) {}
  }

  function persistTrailSession() {
    try {
      var tail = equityTrail.slice(-800);
      sessionStorage.setItem("equityTrailV1", JSON.stringify(tail));
    } catch (_) {}
  }

  function topNumericKeys(obj, maxN) {
    if (!obj || typeof obj !== "object" || Array.isArray(obj)) return [];
    const scored = [];
    for (const [k, v] of Object.entries(obj)) {
      if (v === null || v === undefined) continue;
      if (typeof v === "number" && !Number.isNaN(v)) {
        scored.push({ k, v, mag: Math.abs(v) });
      }
    }
    scored.sort((a, b) => b.mag - a.mag);
    return scored.slice(0, maxN);
  }

  function chipsFromParts(parts, maxChips) {
    const out = [];
    const lim = maxChips || 4;
    for (let i = 0; i < parts.length && out.length < lim; i++) {
      const t = String(parts[i] || "").trim();
      if (t.length > 64) out.push(t.slice(0, 61) + "…");
      else if (t) out.push(t);
    }
    return out;
  }

  function parseContextDisplay(str) {
    const s = String(str || "").trim();
    if (!s || s === "—") return [];
    const chunks = s.split(";").map(function (x) {
      return x.trim();
    });
    const scored = chunks
      .map(function (c) {
        const m = c.match(/=([-+]?[0-9]*\.?[0-9]+)\s*$/);
        const mag = m ? Math.abs(parseFloat(m[1], 10)) : c.length * 0.01;
        return { c: c, mag: mag };
      })
      .sort(function (a, b) {
        return b.mag - a.mag;
      });
    return scored.map(function (x) {
      return x.c;
    });
  }

  function entrySignalsHtml(p) {
    const chips = [];
    const uw = p.entry_uw;
    const sig = p.signals;
    const intel = p.passive_uw_harvest;
    const v2 = p.v2;
    if (uw && typeof uw === "object") {
      topNumericKeys(uw, 4).forEach(function (x) {
        chips.push(x.k + "=" + String(x.v));
      });
    }
    if (chips.length < 4 && sig && typeof sig === "object") {
      topNumericKeys(sig, 4).forEach(function (x) {
        chips.push(x.k + "=" + String(x.v));
      });
    }
    if (chips.length < 4 && intel && typeof intel === "object") {
      topNumericKeys(intel, 3).forEach(function (x) {
        chips.push("harvest:" + x.k + "=" + String(x.v));
      });
    }
    if (chips.length < 4 && v2 && typeof v2 === "object" && v2.components && typeof v2.components === "object") {
      topNumericKeys(v2.components, 4).forEach(function (x) {
        chips.push(x.k + "=" + String(x.v));
      });
    }
    const fallback = parseContextDisplay(p.entry_context_display).concat(
      parseContextDisplay(p.entry_reason_display)
    );
    const merged = chips.length ? chips : fallback;
    const uniq = [];
    const seen = {};
    for (let i = 0; i < merged.length; i++) {
      const k = merged[i];
      if (!k || seen[k]) continue;
      seen[k] = 1;
      uniq.push(k);
    }
    const list = chipsFromParts(uniq, 5);
    if (!list.length) {
      return '<span class="muted row-hint">No structured signals</span>';
    }
    let h = '<div class="signal-chips">';
    for (let j = 0; j < list.length; j++) {
      h += '<span class="chip" title="' + escapeAttr(list[j]) + '">' + escapeHtml(list[j]) + "</span>";
    }
    h += "</div>";
    return h;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function escapeAttr(s) {
    return escapeHtml(s).replace(/'/g, "&#39;");
  }

  function compositeClass(cur, entry) {
    const c = Number(cur);
    const e = Number(entry);
    if (Number.isNaN(c)) return "composite-score mid";
    if (!Number.isNaN(e) && e > 0) {
      const r = c / e;
      if (r >= 0.75) return "composite-score";
      if (r >= 0.45) return "composite-score mid";
      return "composite-score weak";
    }
    if (c >= 3) return "composite-score";
    if (c >= 1.5) return "composite-score mid";
    return "composite-score weak";
  }

  function compositeLabel(p) {
    const cur = p.current_score;
    if (cur !== null && cur !== undefined && !Number.isNaN(Number(cur))) {
      return Number(cur).toFixed(2);
    }
    return "—";
  }

  function renderEquityChart() {
    var canvas = el("pnlChart");
    if (!canvas || typeof Chart === "undefined") return;

    var series = equityTrail.slice().sort(function (a, b) {
      return a.t - b.t;
    });
    if (series.length === 0) {
      destroyPnlChart();
      lastChartSig = "";
      return;
    }

    var anchor = series[0].equity;
    var lastEq = series[series.length - 1].equity;
    /** @type {string[]} */
    var labels = series.map(function (pt, idx) {
      try {
        var d = new Date(pt.t);
        if (idx === 0 || idx === series.length - 1 || idx % Math.ceil(series.length / 12 || 1) === 0) {
          return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
        }
        return "";
      } catch (_) {
        return String(idx + 1);
      }
    });
    var vals = series.map(function (pt) {
      return pt.equity;
    });

    if (vals.length === 1) {
      labels = [labels[0] || "start", "now"];
      vals = [vals[0], vals[0]];
    }

    var above = lastEq >= anchor;
    var lineMain = above ? "#39d353" : "#ff6b6b";
    var fillTop = above ? "rgba(57, 211, 83, 0.24)" : "rgba(255, 107, 107, 0.2)";
    var fillBot = "rgba(13, 17, 23, 0)";
    var sig = labels.join("\u0001") + "|" + vals.join(",");

    var ctx2 = canvas.getContext("2d");
    if (!ctx2) return;

    var gradientFill = fillTop;
    try {
      var g = ctx2.createLinearGradient(0, 0, 0, canvas.clientHeight || 220);
      g.addColorStop(0, fillTop);
      g.addColorStop(1, fillBot);
      gradientFill = g;
    } catch (_) {}

    if (pnlChart && sig === lastChartSig) {
      pnlChart.data.labels = labels;
      pnlChart.data.datasets[0].data = vals;
      pnlChart.data.datasets[0].borderColor = lineMain;
      pnlChart.data.datasets[0].backgroundColor = gradientFill;
      pnlChart.update("none");
      return;
    }
    lastChartSig = sig;

    destroyPnlChart();
    pnlChart = new Chart(ctx2, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Equity (USD)",
            data: vals,
            borderColor: lineMain,
            backgroundColor: gradientFill,
            fill: true,
            tension: 0.25,
            pointRadius: 0,
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: "index" },
        elements: {
          line: {
            segment: {
              borderColor: function (seg) {
                var y0 = seg.p0.parsed.y;
                var y1 = seg.p1.parsed.y;
                var m0 = y0 >= anchor;
                var m1 = y1 >= anchor;
                if (m0 && m1) return "#39d353";
                if (!m0 && !m1) return "#ff6b6b";
                return "#d29922";
              },
            },
          },
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                var v = ctx.parsed.y;
                var vsAnchor = v >= anchor ? "≥ anchor" : "< anchor";
                return formatMoney(v) + " (" + vsAnchor + ")";
              },
            },
          },
        },
        scales: {
          x: { ticks: { color: "#8b949e", maxRotation: 0, autoSkip: true, maxTicksLimit: 10 }, grid: { color: "#30363d" } },
          y: {
            ticks: {
              color: "#8b949e",
              callback: function (v) {
                return formatMoney(v);
              },
            },
            grid: { color: "#30363d" },
          },
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
      tr.innerHTML = '<td colspan="8" class="muted">No open positions</td>';
      tbody.appendChild(tr);
      return;
    }
    for (let i = 0; i < rows.length; i++) {
      const p = rows[i];
      const tr = document.createElement("tr");
      tr.className = "data-row";
      const sym = p.symbol != null ? String(p.symbol) : "—";
      const qty = p.qty != null ? String(p.qty) : "—";
      var outlayRaw =
        p.total_outlay != null && p.total_outlay !== ""
          ? p.total_outlay
          : p.qty != null && p.avg_entry_price != null
            ? Number(p.qty) * Number(p.avg_entry_price)
            : null;
      const outlay = formatMoney(outlayRaw);
      const up = p.unrealized_pnl;
      const pct = p.unrealized_pnl_pct;
      const comp = compositeLabel(p);
      const cc = compositeClass(p.current_score, p.entry_score);
      const entrySc = p.entry_score != null && !Number.isNaN(Number(p.entry_score)) ? Number(p.entry_score).toFixed(2) : "—";
      const entryScClass = pnlClass(p.entry_score);
      tr.innerHTML =
        "<td>" +
        escapeHtml(sym) +
        "</td><td>" +
        escapeHtml(qty) +
        "</td><td>" +
        escapeHtml(outlay) +
        "</td><td>" +
        spanMoney(up) +
        "</td><td>" +
        spanPct(pct) +
        "</td><td>" +
        entrySignalsHtml(p) +
        '</td><td><span class="' +
        cc +
        '">' +
        escapeHtml(comp) +
        '</span></td><td><span class="' +
        entryScClass +
        '">' +
        escapeHtml(entrySc) +
        "</span></td>";
      tbody.appendChild(tr);
    }
  }

  function openTradeModal(trade) {
    const backdrop = el("tradeDetailModal");
    const pre = el("tradeDetailPre");
    const title = el("tradeDetailTitle");
    if (!backdrop || !pre) return;
    const sym = trade && trade.symbol ? String(trade.symbol) : "Trade";
    if (title) title.textContent = sym + " · payload";
    pre.textContent = JSON.stringify(trade, null, 2);
    backdrop.hidden = false;
    backdrop.classList.add("open");
    document.body.style.overflow = "hidden";
  }

  function closeTradeModal() {
    const backdrop = el("tradeDetailModal");
    if (!backdrop) return;
    backdrop.classList.remove("open");
    backdrop.hidden = true;
    document.body.style.overflow = "";
  }

  async function pollCommandCenter() {
    let allOk = true;

    const h = await safeFetch("/health");
    if (h.ok && h.data) {
      const st = h.data.status || "unknown";
      const dot = healthDot(st);
      const kpiH = el("kpiHealth");
      if (kpiH) {
        kpiH.innerHTML = '<span class="status-dot ' + dot + '"></span>' + escapeHtml(st);
      }
      const sub = el("kpiHealthSub");
      if (sub) {
        sub.textContent =
          "Bot " +
          (h.data.bot_running ? "running" : "stopped") +
          " · Alpaca " +
          (h.data.alpaca_connected ? "up" : "down");
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
        const v = m.data.day_pnl_usd;
        dp.className = pnlClass(v);
        dp.textContent = formatMoney(v);
      }

      var pts = m.data.rolling_pnl_last_points;
      if (pts && pts.length) mergeSamplesFromRollingJson(pts);
    } else {
      allOk = false;
    }

    await ensureRollingHistoryOnce();

    const p = await safeFetch("/open_positions?limit=50");
    if (p.ok && p.data) {
      renderOpenRows(p.data.positions);
      if (p.data.total_value != null && p.data.total_value !== "") {
        appendLivePortfolioEquity(p.data.total_value);
      }
    } else {
      allOk = false;
    }

    renderEquityChart();
    persistTrailSession();

    setConn(allOk, allOk ? "" : "Reconnecting…");
  }

  function exitReasonCell(t) {
    const raw = t.close_reason || t.exit_reason || "";
    return escapeHtml(String(raw).slice(0, 56));
  }

  function entrySignalsClosedHtml(t) {
    const parts = [];
    if (t.entry_reason_display) parts.push(String(t.entry_reason_display));
    if (t.entry_reason && String(t.entry_reason) !== String(t.entry_reason_display)) {
      parts.push(String(t.entry_reason).slice(0, 120));
    }
    const intel = t.intelligence_trace;
    const harv = t.passive_uw_harvest;
    if (intel && typeof intel === "object") {
      topNumericKeys(intel, 3).forEach(function (x) {
        parts.push("trace:" + x.k + "=" + String(x.v));
      });
    }
    if (harv && typeof harv === "object") {
      topNumericKeys(harv, 3).forEach(function (x) {
        parts.push("harvest:" + x.k + "=" + String(x.v));
      });
    }
    const list = chipsFromParts(parts, 5);
    if (!list.length) return '<span class="muted row-hint">—</span>';
    let h = '<div class="signal-chips">';
    for (let j = 0; j < list.length; j++) {
      h += '<span class="chip" title="' + escapeAttr(list[j]) + '">' + escapeHtml(list[j]) + "</span>";
    }
    h += "</div>";
    return h;
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
          tr.innerHTML = '<td colspan="7" class="muted">No rows</td>';
          tbody.appendChild(tr);
        } else {
          for (let i = 0; i < trades.length; i++) {
            const t = trades[i];
            const tr = document.createElement("tr");
            tr.className = "data-row";
            const ts = (t.timestamp || t.exit_timestamp || "").slice(0, 19);
            const sym = t.symbol != null ? String(t.symbol) : "—";
            const pnl = t.pnl_usd;
            const st = t.strict_alpaca_chain != null ? String(t.strict_alpaca_chain) : "—";
            tr.innerHTML =
              "<td>" +
              escapeHtml(ts) +
              "</td><td>" +
              escapeHtml(sym) +
              "</td><td>" +
              spanMoney(pnl) +
              "</td><td>" +
              exitReasonCell(t) +
              "</td><td>" +
              entrySignalsClosedHtml(t) +
              '</td><td class="row-hint">' +
              escapeHtml(st) +
              '</td><td><span class="muted row-hint">Details</span></td>';
            tr.addEventListener("click", function () {
              openTradeModal(t);
            });
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
          '<td colspan="7" class="muted">' +
          escapeHtml(e && e.message ? String(e.message) : "Load failed") +
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

  const modal = el("tradeDetailModal");
  const modalClose = el("tradeDetailClose");
  if (modalClose) modalClose.addEventListener("click", closeTradeModal);
  if (modal) {
    modal.addEventListener("click", function (ev) {
      if (ev.target === modal) closeTradeModal();
    });
  }
  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") closeTradeModal();
  });

  hydrateTrailFromSession();
  void pollCommandCenter();
  startPoll();
})();
