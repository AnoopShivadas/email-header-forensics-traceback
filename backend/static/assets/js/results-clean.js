document.addEventListener("DOMContentLoaded", async () => {
  const params = new URLSearchParams(window.location.search);
  let analysisId = params.get("analysis_id");

  /* =====================================================
     SESSION SAFETY FIX
     ===================================================== */

  const navigationType = performance.getEntriesByType("navigation")[0]?.type;

  // If user landed directly (not via history click),
  // clear stale stored analysis
  if (!analysisId && navigationType === "navigate") {
    sessionStorage.removeItem("last_analysis_id");
  }

  // Preserve only if explicitly passed via query
  if (analysisId && analysisId !== "undefined") {
    sessionStorage.setItem("last_analysis_id", analysisId);
  } else {
    analysisId = sessionStorage.getItem("last_analysis_id");
  }

  let data = null;

  try {
    if (analysisId && analysisId !== "undefined") {
      const res = await fetch(`/api/analysis/${analysisId}`);
      if (!res.ok) {
        clearUI();
        return;
      }
      data = await res.json();
    } else {
      const res = await fetch("/api/latest-result");
      if (!res.ok) {
        clearUI();
        return;
      }

      data = await res.json();

      // ✅ NEW: Handle backend empty state properly
      if (data.empty) {
        clearUI();
        return;
      }

      // Fetch full analysis if partial
      if (!data.findings && data.id) {
        const fullRes = await fetch(`/api/analysis/${data.id}`);
        if (fullRes.ok) {
          data = await fullRes.json();
        }
      }
    }

    if (!data) {
      clearUI();
      return;
    }

    /* ===============================
       HEADER INFO
    ================================ */
    fromVal.textContent = data.from || "—";
    toVal.textContent = data.to || "—";
    subjectVal.textContent = data.subject || "—";
    dateVal.textContent = data.date || "—";
    hopCount.textContent = data.hop_count ?? "—";

    /* ===============================
       AUTH
    ================================ */
    resetAuth("spfBadge");
    resetAuth("dkimBadge");
    resetAuth("dmarcBadge");

    setAuth("spfBadge", normalizeAuth(data.spf));
    setAuth("dkimBadge", normalizeAuth(data.dkim));
    setAuth("dmarcBadge", normalizeAuth(data.dmarc));

    /* ===============================
       SCORE
    ================================ */
    resetScore();
    animateScore(data.risk_score, data.verdict, data.summary);

    /* ===============================
       RISK BREAKDOWN
    ================================ */
    renderRiskBreakdown(data.findings || []);

  } catch (err) {
    console.error("Results load failed:", err);
    clearUI();
  }
});

/* =====================================================
   CLEAR UI (NEW FUNCTION)
   ===================================================== */

function clearUI() {
  sessionStorage.removeItem("last_analysis_id");

  fromVal.textContent = "—";
  toVal.textContent = "—";
  subjectVal.textContent = "—";
  dateVal.textContent = "—";
  hopCount.textContent = "—";

  resetAuth("spfBadge");
  resetAuth("dkimBadge");
  resetAuth("dmarcBadge");

  resetScore();

  const verdictText = document.getElementById("verdictText");
  const verdictSummary = document.getElementById("verdictSummary");

  if (verdictText) verdictText.textContent = "No Analysis Performed";
  if (verdictSummary) verdictSummary.textContent =
    "Run an email header analysis to view risk insights.";

  const list = document.getElementById("riskFactors");
  if (list) {
    list.innerHTML =
      "<li style='opacity:0.6;'>No analysis data available.</li>";
  }
}

/* ===============================
   AUTH HELPERS
================================ */
function normalizeAuth(val) {
  if (val === true) return true;
  if (typeof val === "string") {
    return val.toLowerCase() === "pass";
  }
  return false;
}

function resetAuth(id) {
  const el = document.getElementById(id);
  if (!el) return;

  el.classList.remove("pass", "fail");
  el.textContent = el.textContent.replace(" ✓", "").replace(" ✕", "");
}

function setAuth(id, ok) {
  const el = document.getElementById(id);
  if (!el) return;

  el.classList.add(ok ? "pass" : "fail");
  el.textContent += ok ? " ✓" : " ✕";
}

/* ===============================
   SCORE
================================ */
function resetScore() {
  riskScore.textContent = "0";
  riskProgress.style.strokeDashoffset = 502;
}

function animateScore(final, verdict, summary) {
  let s = 0;
  const circle = riskProgress;
  const verdictText = document.getElementById("verdictText");
  const verdictSummary = document.getElementById("verdictSummary");

  const i = setInterval(() => {
    s++;
    riskScore.textContent = s;
    circle.style.strokeDashoffset = 502 - (502 * s / 100);

    if (s >= final) {
      clearInterval(i);
      verdictText.textContent = verdict;
      verdictSummary.textContent = summary;
    }
  }, 12);
}

/* ===============================
   RISK BREAKDOWN
================================ */
function renderRiskBreakdown(findings) {
  const list = document.getElementById("riskFactors");
  list.innerHTML = "";

  if (!findings.length) {
    list.innerHTML =
      "<li>No significant risk factors detected.</li>";
    return;
  }

  findings.forEach((f, index) => {
    const li = document.createElement("li");

    const label = document.createElement("span");
    label.textContent = f.rule;

    const bar = document.createElement("div");
    bar.className = "bar";

    const fill = document.createElement("div");
    fill.className = "fill";

    if (f.impact < 0) fill.style.background = "#22c55e";
    else if (f.impact > 0) fill.style.background = "#f59e0b";
    else fill.style.background = "#94a3b8";

    const width = Math.min(Math.abs(f.impact) * 3, 100);
    setTimeout(() => {
      fill.style.width = width + "%";
    }, 100 + index * 120);

    bar.appendChild(fill);

    const score = document.createElement("small");
    score.textContent = f.impact > 0 ? `+${f.impact}` : f.impact;

    li.appendChild(label);
    li.appendChild(bar);
    li.appendChild(score);

    list.appendChild(li);
  });
}