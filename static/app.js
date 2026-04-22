(function () {
  "use strict";

  /** Command Center poll interval (ms); balance broker load vs chart freshness. */
  const POLL_MS = 30000;
  const FETCH_OPTS = { credentials: "include", headers: { Accept: "application/json" } };

  const el = (id) => document.getElementById(id);
  let pollTimer = null;
  let pnlChart = null;
  /** @type {any} */
  let dailyTradesChart = null;
  let lastDailyTradesSig = "";
  let vaultLoaded = false;
  /** @type {{ t: number, equity: number, src?: string }[]} */
  let equityTrail = [];
  let lastChartSig = "";
  /** Reference starting equity for chart anchor (USD). */
  var EQUITY_BASELINE_USD = 10000;

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

  function destroyDailyTradesChart() {
    if (dailyTradesChart) {
      try {
        dailyTradesChart.destroy();
      } catch (_) {}
      dailyTradesChart = null;
    }
  }

  /**
   * @param {{ label?: string, date?: string, trade_count?: number }[]} series
   */
  function renderDailyTradesChart(series) {
    const canvas = el("dailyTradesChart");
    if (!canvas || typeof Chart === "undefined") return;
    if (!Array.isArray(series) || series.length === 0) {
      destroyDailyTradesChart();
      lastDailyTradesSig = "";
      return;
    }
    const labels = series.map(function (x) {
      return x.label || x.date || "";
    });
    const vals = series.map(function (x) {
      return Number(x.trade_count) || 0;
    });
    var mx = 0;
    for (var vi = 0; vi < vals.length; vi++) {
      if (vals[vi] > mx) mx = vals[vi];
    }
    var ySuggestedMax = mx === 0 ? 4 : Math.ceil(mx * 1.15);
    const sig = labels.join("\u0001") + "|" + vals.join(",") + "|" + ySuggestedMax;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    if (dailyTradesChart && sig === lastDailyTradesSig) {
      dailyTradesChart.data.labels = labels;
      dailyTradesChart.data.datasets[0].data = vals;
      if (dailyTradesChart.options.scales && dailyTradesChart.options.scales.y) {
        dailyTradesChart.options.scales.y.suggestedMax = ySuggestedMax;
      }
      dailyTradesChart.update("none");
      return;
    }
    lastDailyTradesSig = sig;
    destroyDailyTradesChart();

    try {
      dailyTradesChart = new Chart(ctx, {
        type: "bar",
        data: {
          labels: labels,
          datasets: [
            {
              data: vals,
              backgroundColor: "rgba(88, 166, 255, 0.72)",
              borderColor: "#58a6ff",
              borderWidth: 1,
              borderRadius: 2,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: false,
          plugins: {
            legend: { display: false },
            tooltip: { enabled: false },
          },
          scales: {
            x: {
              ticks: {
                color: "#8b949e",
                maxRotation: 55,
                minRotation: 45,
                autoSkip: true,
                maxTicksLimit: 16,
                font: { size: 9 },
              },
              grid: { display: false },
            },
            y: {
              beginAtZero: true,
              suggestedMax: ySuggestedMax,
              ticks: { color: "#8b949e", precision: 0, stepSize: mx === 0 ? 1 : undefined },
              grid: { display: false },
            },
          },
        },
      });
    } catch (err) {
      console.error("[dashboard] daily trades chart", err);
      destroyDailyTradesChart();
    }
  }

  async function loadDailyTradeVolume() {
    const note = el("dailyTradeNote");
    try {
      const r = await safeFetch("/api/dashboard/daily_trade_volume?days=30");
      if (!r.ok) {
        if (note) {
          note.textContent =
            r.error && r.error.message ? String(r.error.message) : "Could not load trades-per-day (check auth).";
        }
        destroyDailyTradesChart();
        return;
      }
      const d = r.data;
      if (!d || d.ok === false) {
        if (note) note.textContent = d && d.error ? String(d.error) : "Trades-per-day unavailable.";
        destroyDailyTradesChart();
        return;
      }
      const sn = d.scan_note ? String(d.scan_note) : "";
      const tz = d.timezone ? " · " + d.timezone : "";
      const todayHint =
        d.calendar_today_label && d.calendar_today_trade_count != null
          ? " · Today: " + d.calendar_today_label + " → " + String(d.calendar_today_trade_count)
          : "";
      if (note) note.textContent = (sn || "Daily closed-trade counts from exit_attribution.jsonl tail") + tz + todayHint;
      var series = d.series || [];
      requestAnimationFrame(function () {
        try {
          renderDailyTradesChart(series);
        } catch (e) {
          console.error("[dashboard] render daily trades", e);
        }
      });
    } catch (e) {
      console.error("[dashboard] loadDailyTradeVolume", e);
      if (note) note.textContent = "Trades-per-day load error.";
      destroyDailyTradesChart();
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

  function shadowEquityFromRollingPoint(p) {
    if (!p || typeof p !== "object") return null;
    if (p.equity_shadow != null && !Number.isNaN(Number(p.equity_shadow))) return Number(p.equity_shadow);
    if (p.shadow_equity != null && !Number.isNaN(Number(p.shadow_equity))) return Number(p.shadow_equity);
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
      var sh = shadowEquityFromRollingPoint(p);
      var found = -1;
      for (var j = 0; j < equityTrail.length; j++) {
        if (Math.abs(equityTrail[j].t - t) < 500) {
          found = j;
          break;
        }
      }
      if (found >= 0) {
        var ex = equityTrail[found];
        var merged = { t: t, equity: eq, src: "rolling_file" };
        if (sh != null) merged.shadow = sh;
        else if (ex.shadow != null) merged.shadow = ex.shadow;
        equityTrail[found] = merged;
      } else {
        var row = { t: t, equity: eq, src: "rolling_file" };
        if (sh != null) row.shadow = sh;
        equityTrail.push(row);
      }
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

  async function refreshRollingPnl5d() {
    try {
      var r = await safeFetch("/api/rolling_pnl_5d");
      if (!r.ok || !r.data) return;
      var pts = r.data.points;
      if (!Array.isArray(pts)) return;
      var sv = r.data.shadow_value;
      if (Array.isArray(sv) && sv.length === pts.length) {
        for (var k = 0; k < pts.length; k++) {
          var sVal = sv[k];
          if (sVal == null) continue;
          if (Number.isNaN(Number(sVal))) continue;
          var p = pts[k];
          if (!p || typeof p !== "object") continue;
          if (p.equity_shadow == null) pts[k] = Object.assign({}, p, { equity_shadow: Number(sVal) });
        }
      }
      mergeSamplesFromRollingJson(pts);
    } catch (_) {}
  }

  /** True when timestamp falls on NYSE regular session (Mon–Fri, 09:30–16:00 America/New_York). */
  function isNYSERegularSession(tsMs) {
    var d = new Date(tsMs);
    var wk = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", weekday: "short" }).format(d);
    if (wk === "Sat" || wk === "Sun") return false;
    var parts = new Intl.DateTimeFormat("en-US", {
      timeZone: "America/New_York",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).formatToParts(d);
    var hh = -1;
    var mm = 0;
    for (var i = 0; i < parts.length; i++) {
      var p = parts[i];
      if (p.type === "hour") hh = parseInt(p.value, 10);
      if (p.type === "minute") mm = parseInt(p.value, 10) || 0;
    }
    if (hh < 0 || Number.isNaN(hh)) return false;
    var mins = hh * 60 + mm;
    return mins >= 9 * 60 + 30 && mins < 16 * 60;
  }

  /**
   * Drop overnight/weekend points so the X-axis is sequential RTH-only (stitched sessions).
   * Always keeps the final sample (live broker total) even outside RTH.
   * @param {{ t: number, equity: number, src?: string }[]} sortedAsc
   */
  function filterEquitySeriesRthStitch(sortedAsc) {
    if (!sortedAsc || sortedAsc.length === 0) return [];
    var last = sortedAsc[sortedAsc.length - 1];
    var out = [];
    for (var i = 0; i < sortedAsc.length; i++) {
      var pt = sortedAsc[i];
      if (isNYSERegularSession(pt.t)) out.push(pt);
    }
    if (out.length === 0) return sortedAsc.slice();
    if (last && !isNYSERegularSession(last.t)) {
      if (!out.length || out[out.length - 1].t !== last.t) out.push(last);
    }
    return out;
  }

  function equityChartRthOnlyEnabled() {
    var c = el("equityRthOnly");
    return !c || c.checked;
  }

  function equityChartShowRunPnl() {
    var c = el("equityShowRunPnl");
    return !c || c.checked;
  }

  function equityChartShowShadow() {
    var c = el("equityShowShadow");
    return !c || c.checked;
  }

  function formatEtAxisLabel(tsMs) {
    try {
      return new Intl.DateTimeFormat("en-US", {
        timeZone: "America/New_York",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      }).format(new Date(tsMs));
    } catch (_) {
      return String(tsMs);
    }
  }

  /** Min/max Y for equity chart: strict data range + small padding (no synthetic anchors). */
  function yDomainFromVals(vals) {
    var mn = Infinity;
    var mx = -Infinity;
    for (var i = 0; i < vals.length; i++) {
      var v = Number(vals[i]);
      if (!Number.isFinite(v)) continue;
      mn = Math.min(mn, v);
      mx = Math.max(mx, v);
    }
    if (!Number.isFinite(mn) || !Number.isFinite(mx)) {
      return { min: undefined, max: undefined };
    }
    if (mn === mx) {
      var padFlat = Math.max(Math.abs(mn) * 0.001, 1);
      return { min: mn - padFlat, max: mx + padFlat };
    }
    var span = mx - mn;
    var pad = span * 0.001;
    return { min: mn - pad, max: mx + pad };
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
            var o = { t: x.t, equity: x.equity, src: x.src || "session" };
            if (typeof x.shadow === "number" && !Number.isNaN(x.shadow)) o.shadow = x.shadow;
            return o;
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

    var rawSeries = equityTrail.slice().sort(function (a, b) {
      return a.t - b.t;
    });
    if (rawSeries.length === 0) {
      destroyPnlChart();
      lastChartSig = "";
      return;
    }

    var rthOn = equityChartRthOnlyEnabled();
    var series = rthOn ? filterEquitySeriesRthStitch(rawSeries) : rawSeries;
    if (series.length === 0) series = rawSeries;

    var showRun = equityChartShowRunPnl();
    var baseline = Number(EQUITY_BASELINE_USD);
    if (Number.isNaN(baseline)) baseline = 10000;

    var n = series.length;
    var tickEvery = Math.max(1, Math.ceil(n / 14));
    var prevDayEt = "";
    /** @type {string[]} */
    var labels = [];
    for (var idx = 0; idx < n; idx++) {
      var pt = series[idx];
      var dayEt = "";
      try {
        dayEt = new Intl.DateTimeFormat("en-CA", {
          timeZone: "America/New_York",
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
        }).format(new Date(pt.t));
      } catch (_) {
        dayEt = "";
      }
      var showTick = idx === 0 || idx === n - 1 || dayEt !== prevDayEt || idx % tickEvery === 0;
      prevDayEt = dayEt || prevDayEt;
      labels.push(showTick ? formatEtAxisLabel(pt.t) : "");
    }

    var vals = series.map(function (pt) {
      return pt.equity;
    });
    var pnlVals = vals.map(function (v) {
      return v - baseline;
    });
    var showSh = equityChartShowShadow();
    var shadowVals = series.map(function (pt) {
      if (typeof pt.shadow === "number" && !Number.isNaN(pt.shadow)) return pt.shadow;
      return null;
    });
    var hasShadowData = false;
    for (var si = 0; si < shadowVals.length; si++) {
      if (shadowVals[si] != null && Number.isFinite(shadowVals[si])) {
        hasShadowData = true;
        break;
      }
    }

    if (vals.length === 1) {
      labels = [labels[0] || formatEtAxisLabel(series[0].t), "now"];
      vals = [vals[0], vals[0]];
      pnlVals = [pnlVals[0], pnlVals[0]];
      if (shadowVals[0] != null) {
        shadowVals = [shadowVals[0], shadowVals[0]];
      } else {
        shadowVals = [null, null];
      }
    }

    var anchorRef = vals[0];
    var lastEq = vals[vals.length - 1];
    var yBoundVals = vals.slice();
    if (showSh) {
      for (var bj = 0; bj < shadowVals.length; bj++) {
        if (shadowVals[bj] != null && Number.isFinite(shadowVals[bj])) yBoundVals.push(shadowVals[bj]);
      }
    }
    var yBounds = yDomainFromVals(yBoundVals);
    var yPnlBounds = yDomainFromVals(pnlVals);
    var above = lastEq >= anchorRef;
    var lineMain = above ? "#39d353" : "#ff6b6b";
    var fillTop = above ? "rgba(57, 211, 83, 0.24)" : "rgba(255, 107, 107, 0.2)";
    var fillBot = "rgba(13, 17, 23, 0)";
    var sig =
      (rthOn ? "R1" : "R0") +
      (showRun ? "P1" : "P0") +
      (showSh ? "S1" : "S0") +
      "\u0001" +
      labels.join("\u0001") +
      "|" +
      vals.join(",") +
      "|" +
      pnlVals.join(",") +
      "|" +
      (shadowVals.map(function (x) { return x == null ? "" : x; }).join(",") + "");

    var ctx2 = canvas.getContext("2d");
    if (!ctx2) return;

    var gradientFill = fillTop;
    try {
      var ch = canvas.parentElement ? canvas.parentElement.clientHeight : 0;
      var g = ctx2.createLinearGradient(0, 0, 0, ch || canvas.clientHeight || 220);
      g.addColorStop(0, fillTop);
      g.addColorStop(1, fillBot);
      gradientFill = g;
    } catch (_) {}

    if (pnlChart && sig === lastChartSig) {
      pnlChart.data.labels = labels;
      pnlChart.data.datasets[0].data = vals;
      pnlChart.data.datasets[0].borderColor = lineMain;
      pnlChart.data.datasets[0].backgroundColor = gradientFill;
      if (pnlChart.data.datasets[1]) {
        pnlChart.data.datasets[1].data = pnlVals;
        pnlChart.data.datasets[1].hidden = !showRun;
      }
      if (pnlChart.data.datasets[2]) {
        pnlChart.data.datasets[2].data = shadowVals;
        pnlChart.data.datasets[2].hidden = !showSh || !hasShadowData;
      }
      if (pnlChart.options.scales && pnlChart.options.scales.y) {
        pnlChart.options.scales.y.min = yBounds.min;
        pnlChart.options.scales.y.max = yBounds.max;
      }
      if (pnlChart.options.scales && pnlChart.options.scales.y1) {
        pnlChart.options.scales.y1.display = showRun;
        if (showRun) {
          pnlChart.options.scales.y1.min = yPnlBounds.min;
          pnlChart.options.scales.y1.max = yPnlBounds.max;
        }
      }
      if (pnlChart.options.plugins && pnlChart.options.plugins.legend) {
        pnlChart.options.plugins.legend.display = showRun || (showSh && hasShadowData);
      }
      pnlChart.update("none");
      return;
    }
    lastChartSig = sig;

    var legendOn = showRun || (showSh && hasShadowData);
    var shadowOn = showSh && hasShadowData;
    var shadowDashed = [5, 5];
    var shadowColor = "#FFD700";

    destroyPnlChart();
    try {
      pnlChart = new Chart(ctx2, {
        type: "line",
        data: {
          labels: labels,
          datasets: [
            {
              label: "Actual equity (live)",
              data: vals,
              yAxisID: "y",
              borderColor: lineMain,
              backgroundColor: gradientFill,
              fill: true,
              tension: 0.25,
              pointRadius: 0,
              borderWidth: 2,
            },
            {
              label: "Running PnL vs baseline",
              data: pnlVals,
              yAxisID: "y1",
              borderColor: "#58a6ff",
              backgroundColor: "transparent",
              fill: false,
              tension: 0.25,
              pointRadius: 0,
              borderWidth: 1.75,
              borderDash: [5, 4],
              hidden: !showRun,
            },
            {
              label: "Shadow equity (no-chop sim)",
              data: shadowVals,
              yAxisID: "y",
              borderColor: shadowColor,
              backgroundColor: "transparent",
              fill: false,
              tension: 0.25,
              pointRadius: 0,
              borderWidth: 2.25,
              borderDash: shadowDashed,
              hidden: !shadowOn,
              spanGaps: true,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: false,
          interaction: { intersect: false, mode: "index" },
          plugins: {
            legend: {
              display: legendOn,
              position: "top",
              labels: { color: "#8b949e", boxWidth: 10, font: { size: 10 } },
            },
            tooltip: {
              callbacks: {
                title: function (items) {
                  var ix = items && items[0] ? items[0].dataIndex : 0;
                  var row = series[ix];
                  if (!row) return "";
                  try {
                    return new Date(row.t).toISOString();
                  } catch (_) {
                    return "";
                  }
                },
                label: function (ctx) {
                  var ix = ctx.dataIndex;
                  var row = series[ix];
                  var tsEt = row ? formatEtAxisLabel(row.t) : "";
                  var tag = tsEt ? " · " + tsEt + " ET" : "";
                  if (ctx.datasetIndex === 0 || ctx.datasetIndex === 2) {
                    return null;
                  }
                  if (ctx.datasetIndex === 1) {
                    var pv = ctx.parsed.y;
                    return "Running PnL " + formatMoney(pv) + " vs " + formatMoney(baseline) + tag;
                  }
                  return "";
                },
                footer: function (tooltipItems) {
                  if (!tooltipItems || !tooltipItems.length) return [];
                  var ix = tooltipItems[0].dataIndex;
                  var row = series[ix];
                  if (!row) return [];
                  var tsEt = formatEtAxisLabel(row.t) + " ET";
                  var act = "Actual equity (live): " + formatMoney(row.equity) + (row.t ? " · " + tsEt : "");
                  if (!showSh) {
                    return [act];
                  }
                  var sh =
                    row.shadow != null && !Number.isNaN(Number(row.shadow))
                      ? "Shadow equity (no-chop sim): " + formatMoney(row.shadow) + (row.t ? " · " + tsEt : "")
                      : "Shadow equity (no-chop sim): n/a";
                  return [act, sh];
                },
              },
            },
          },
          scales: {
            x: {
              type: "category",
              offset: false,
              ticks: { color: "#8b949e", maxRotation: 0, autoSkip: true, maxTicksLimit: 12 },
              grid: { color: "#30363d" },
            },
            y: {
              position: "left",
              min: yBounds.min,
              max: yBounds.max,
              ticks: {
                color: "#8b949e",
                callback: function (v) {
                  return formatMoney(v);
                },
              },
              grid: { color: "#30363d" },
            },
            y1: {
              display: showRun,
              position: "right",
              min: yPnlBounds.min,
              max: yPnlBounds.max,
              grid: { drawOnChartArea: false },
              ticks: {
                color: "#79b8ff",
                callback: function (v) {
                  return formatMoney(v);
                },
              },
            },
          },
        },
      });
    } catch (err) {
      console.error("[dashboard] equity chart", err);
      destroyPnlChart();
    }
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
      if (m.data.equity_baseline_usd != null && !Number.isNaN(Number(m.data.equity_baseline_usd))) {
        EQUITY_BASELINE_USD = Number(m.data.equity_baseline_usd);
      }
      const ke = el("kpiEpoch");
      const target = m.data.ml_epoch_target != null ? Number(m.data.ml_epoch_target) : 250;
      if (ke) {
        const n = m.data.ml_epoch_n;
        if (n != null && n !== "" && !Number.isNaN(Number(n))) {
          ke.textContent = "Epoch: N = " + String(n) + " / " + String(target);
        } else if (m.data.ml_epoch_csv_missing) {
          ke.textContent = "Epoch: N = — / " + target + " (no cohort CSV)";
        } else if (m.data.ml_epoch_error) {
          ke.textContent = "Epoch: N = — / " + target;
          ke.title = String(m.data.ml_epoch_error);
        } else {
          ke.textContent = "Epoch: N = — / " + target;
          ke.title = "";
        }
      }
      const bh = el("equityBaselineHint");
      if (bh && m.data.equity_baseline_usd != null) {
        bh.textContent = formatMoney(m.data.equity_baseline_usd);
      }
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

    await refreshRollingPnl5d();

    const p = await safeFetch("/open_positions?limit=50");
    if (p.ok && p.data) {
      renderOpenRows(p.data.positions);
      if (p.data.total_value != null && p.data.total_value !== "") {
        appendLivePortfolioEquity(p.data.total_value);
      }
    } else {
      allOk = false;
    }

    persistTrailSession();

    await loadDailyTradeVolume();

    requestAnimationFrame(function () {
      try {
        renderEquityChart();
      } catch (err) {
        console.error("[dashboard] paint equity", err);
      }
    });

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

  (function bindEquityChartToggles() {
    function bump() {
      lastChartSig = "";
      requestAnimationFrame(function () {
        try {
          renderEquityChart();
        } catch (_) {}
      });
    }
    var rth = el("equityRthOnly");
    var run = el("equityShowRunPnl");
    var shw = el("equityShowShadow");
    if (rth) rth.addEventListener("change", bump);
    if (run) run.addEventListener("change", bump);
    if (shw) shw.addEventListener("change", bump);
  })();

  hydrateTrailFromSession();
  void pollCommandCenter();
  startPoll();
})();
