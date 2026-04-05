/* ==================================================
   GLOBAL THEME APPLY (EARLY LOAD)
================================================== */
(function applyThemeEarly() {
    const theme = localStorage.getItem("theme");
    if (theme === "dark") {
        document.documentElement.classList.add("dark-theme");
        document.body.classList.add("dark-theme");
    }
})();


document.addEventListener("DOMContentLoaded", () => {
    initSidebar();
    initAnalyzePage();
    initThemeToggle();
    initSettingsToggles();
    initResultsAnimation();
    initGeolocationAnimation();
});


/* ==================================================
   SIDEBAR ACTIVE STATE
================================================== */
function initSidebar() {
    const currentPath = window.location.pathname.replace(/\/$/, "");
    document.querySelectorAll(".nav-item").forEach(item => {
        const href = item.getAttribute("href");
        if (href === currentPath) item.classList.add("active");
    });
}


/* ==================================================
   ANALYZE PAGE (REAL BACKEND CONNECTED)
================================================== */
function initAnalyzePage() {
    const analyzeBtn = document.getElementById("analyzeBtn");
    const clearBtn = document.getElementById("clearBtn");
    const sampleBtn = document.getElementById("sampleBtn");
    const emailHeader = document.getElementById("emailHeader");

    const riskScoreEl = document.getElementById("riskScore");
    const verdictEl = document.getElementById("verdict");
    const hopsEl = document.getElementById("hops");
    const statusBadge = document.getElementById("statusBadge");

    if (!analyzeBtn || !emailHeader) return;

    analyzeBtn.addEventListener("click", async () => {
        const headerText = emailHeader.value.trim();
        if (!headerText) {
            showModernPopup(
                "Missing Email Headers",
                "Please paste full email headers before running forensic analysis."
            );
            return;
        }

        // UI lock
        analyzeBtn.disabled = true;
        clearBtn && (clearBtn.disabled = true);
        sampleBtn && (sampleBtn.disabled = true);
        emailHeader.disabled = true;

        statusBadge.textContent = "Analyzing…";
        statusBadge.className = "badge badge-warning";
        analyzeBtn.textContent = "🔍 Analyzing…";

        try {
            const response = await fetch("/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ header_text: headerText })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "Analysis failed");

            // Update preview widgets (REAL DATA)
            riskScoreEl.textContent = data.risk_score;
            verdictEl.textContent = data.verdict;
            hopsEl.textContent = data.findings?.hop_count ?? "—";

            statusBadge.textContent = "Completed";
            statusBadge.className = "badge badge-success";
            analyzeBtn.textContent = "✔ Analyzed";

            // Show email notification if enabled
            if (data.notification === true) {
                showNotificationToast();
            }

            // Move to results page
            setTimeout(() => {
                if (data.analysis_id === "temp") {
                    window.location.href = "/results";
                } else {
                    window.location.href = `/results?analysis_id=${data.analysis_id}`;
                }
            }, 900);


        } catch (err) {
            console.error(err);
            alert("Analysis failed. Please try again.");

            statusBadge.textContent = "Failed";
            statusBadge.className = "badge badge-danger";
            analyzeBtn.textContent = "Analyze";

            analyzeBtn.disabled = false;
            clearBtn && (clearBtn.disabled = false);
            sampleBtn && (sampleBtn.disabled = false);
            emailHeader.disabled = false;
        }
    });
    clearBtn && clearBtn.addEventListener("click", () => {
        emailHeader.value = "";
        emailHeader.focus();
    });
}

/* ==================================================
   THEME TOGGLE (SETTINGS)
================================================== */
function initThemeToggle() {
    const buttons = document.querySelectorAll(".theme-btn");
    if (!buttons.length) return;

    const root = document.documentElement;
    const savedTheme = localStorage.getItem("theme") || "light";

    root.classList.remove("dark-theme");
    if (savedTheme === "dark") root.classList.add("dark-theme");

    buttons.forEach(btn => {
        btn.classList.toggle("active", btn.dataset.theme === savedTheme);

        btn.addEventListener("click", (e) => {
            e.preventDefault();
            const selectedTheme = btn.dataset.theme;

            buttons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            root.classList.remove("dark-theme");
            if (selectedTheme === "dark") root.classList.add("dark-theme");

            localStorage.setItem("theme", selectedTheme);
        });
    });
}


/* ==================================================
   SETTINGS TOGGLES (PLACEHOLDER)
================================================== */
function initSettingsToggles() {
    document.querySelectorAll(".toggle-switch input")
        .forEach(toggle => {
            toggle.onchange = () => {
                console.log("Setting changed:", toggle.checked);
            };
        });
}


/* ==================================================
   RESULTS PAGE ANIMATION (TEMP STATIC)
   → Will be connected to backend next phase
================================================== */
function initResultsAnimation() {
    const scoreEl = document.getElementById("riskScore");
    const labelEl = document.getElementById("riskLabel");
    const verdictEl = document.getElementById("verdictBadge");
    const progressEl = document.getElementById("riskProgress");

    if (!scoreEl || !labelEl || !verdictEl || !progressEl) return;

    const finalScore = parseInt(scoreEl.textContent) || 62;
    let current = 0;

    const CIRCUMFERENCE = 502;
    progressEl.style.strokeDasharray = CIRCUMFERENCE;
    progressEl.style.strokeDashoffset = CIRCUMFERENCE;

    const interval = setInterval(() => {
        current++;
        scoreEl.textContent = current;
        progressEl.style.strokeDashoffset =
            CIRCUMFERENCE - (CIRCUMFERENCE * current / 100);

        if (current >= finalScore) {
            clearInterval(interval);
            labelEl.textContent = finalScore >= 70 ? "Threat" :
                                  finalScore >= 40 ? "Suspicious" : "Safe";
            verdictEl.style.opacity = 1;
        }
    }, 20);
}


/* ==================================================
   GEOLOCATION PAGE ANIMATION
================================================== */
function initGeolocationAnimation() {
    const timelineItems = document.querySelectorAll(".timeline-item");
    if (!timelineItems.length) return;

    timelineItems.forEach((item, i) => {
        setTimeout(() => item.classList.add("reveal"), i * 400);
    });

    document.querySelectorAll("tbody tr").forEach((row, i) => {
        setTimeout(() => row.classList.add("reveal"), 1200 + i * 200);
    });
}
/* ==================================================
   RESULTS PAGE – LOAD ANALYSIS BY ID (FIX)
================================================== */

document.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    const analysisId = params.get("analysis_id");
    if (!analysisId) return;

    fetch(`/api/analysis/${analysisId}`)
        .then(res => res.json())
        .then(renderResultsFromApi)
        .catch(err => console.error("Failed to load analysis", err));
});

function renderResultsFromApi(data) {
    // Score
    const scoreEl = document.getElementById("riskScore");
    if (scoreEl) scoreEl.textContent = data.risk_score;

    // Verdict
    const verdictEl = document.getElementById("verdictBadge");
    if (verdictEl) verdictEl.textContent = data.verdict;

    // Risk label
    const labelEl = document.getElementById("riskLabel");
    if (labelEl) {
        labelEl.textContent =
            data.risk_score >= 70 ? "Threat" :
            data.risk_score >= 40 ? "Suspicious" : "Safe";
    }

    // Auth badges
    setAuthBadge("spf", data.spf);
    setAuthBadge("dkim", data.dkim);
    setAuthBadge("dmarc", data.dmarc);

    // Risk Breakdown (🔥 THIS WAS THE BUG)
    renderRiskBreakdown(data.findings);

    // Header intelligence
    setText("fromValue", data.from);
    setText("toValue", data.to);
    setText("subjectValue", data.subject);
    setText("dateValue", data.date);
}

/* ---------------- HELPERS ---------------- */

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value || "—";
}

function setAuthBadge(type, passed) {
    const el = document.getElementById(type + "Badge");
    if (!el) return;
    el.className = passed ? "badge badge-success" : "badge badge-danger";
}

function renderRiskBreakdown(findings = []) {
    const container = document.getElementById("riskBreakdownBody");
    if (!container) return;

    container.innerHTML = "";

    if (!findings.length) {
        container.innerHTML = "<p>No significant risk factors detected.</p>";
        return;
    }

    findings.forEach(f => {
        const row = document.createElement("div");
        row.className = "risk-row";
        row.innerHTML = `
            <span>${f.label}</span>
            <div class="bar">
                <div class="fill ${f.score > 0 ? "warning" : "safe"}"
                     style="width:${Math.min(Math.abs(f.score) * 4, 100)}%">
                </div>
            </div>
            <span>${f.score > 0 ? "+" : ""}${f.score}</span>
        `;
        container.appendChild(row);
    });
}
/* ==================================================
   MANUAL LOGIN (DEMO AUTH – GUIDE APPROVED)
================================================== */
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("manualLoginForm");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const email = form.querySelector('input[type="text"]').value.trim();
        const password = form.querySelector('input[type="password"]').value.trim();

        if (!email || !password) {
            alert("Please enter email and password.");
            return;
        }

        try {
            const res = await fetch("/auth/manual", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email })
            });

            if (!res.ok) throw new Error("Login failed");

            window.location.href = "/dashboard";
        } catch (err) {
            alert("Manual login failed.");
        }
    });
});
/* ==================================================
   MANUAL LOGIN – UX POLISH (SAFE)
================================================== */
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("manualLoginForm");
    if (!form) return;

    const emailInput = document.getElementById("emailInput");
    const passwordInput = document.getElementById("passwordInput");
    const errorEl = document.getElementById("loginError");
    const btn = document.getElementById("loginBtn");
    const avatar = document.getElementById("avatarPreview");
    const toggle = document.getElementById("togglePassword");

    // Avatar initials
    emailInput.addEventListener("input", () => {
        const val = emailInput.value.split("@")[0];
        avatar.textContent = val ? val[0].toUpperCase() : "A";
    });

    // Show / Hide password
    toggle.onclick = () => {
        passwordInput.type =
            passwordInput.type === "password" ? "text" : "password";
    };

    // Manual login submit
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        errorEl.textContent = "";

        const email = emailInput.value.trim();
        const password = passwordInput.value.trim();

        if (!email || !password) {
            errorEl.textContent = "Email and password are required.";
            return;
        }

        btn.textContent = "Signing in…";
        btn.disabled = true;

        try {
            const res = await fetch("/auth/manual", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email })
            });

            if (!res.ok) throw new Error();

            window.location.href = "/dashboard";
        } catch {
            errorEl.textContent = "Login failed. Please try again.";
            btn.textContent = "Sign In";
            btn.disabled = false;
        }
    });
});
/* ==================================================
   DASHBOARD GREETING
================================================== */
document.addEventListener("DOMContentLoaded", () => {
    const greetingEl = document.getElementById("dashboardGreeting");
    if (!greetingEl || !window.__USER__) return;

    let name = window.__USER__.name;

    // Manual login fallback → email prefix
    if (!name && window.__USER__.email) {
        name = window.__USER__.email.split("@")[0];
    }

    if (name) {
        greetingEl.textContent = `Welcome, ${name}`;
    }
});
/* ==================================================
   FORGOT PASSWORD (DEMO FLOW)
================================================== */
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("forgotPasswordForm");
    if (!form) return;

    form.addEventListener("submit", (e) => {
        e.preventDefault();

        const email = form.querySelector("input").value.trim();
        if (!email) return;

        alert(
            "If this email exists, password reset instructions have been sent.\n\n(Demo mode – no email sent)"
        );

        setTimeout(() => {
            window.location.href = "/login";
        }, 1200);
    });
});

/* ==================================================
   EMAIL NOTIFICATION TOAST
================================================== */
function showNotificationToast() {
    const toast = document.createElement("div");
    toast.className = "notification-toast";
    toast.innerHTML = `
        📩 Analysis Report Sent<br>
        <small>A notification has been delivered to your registered email.</small>
    `;

    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add("show"), 100);

    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
/* ==================================================
   MODERN UI POPUP (REPLACES alert)
================================================== */
function showModernPopup(title, message) {

    const overlay = document.createElement("div");
    overlay.className = "popup-overlay";

    const popup = document.createElement("div");
    popup.className = "modern-popup";

    popup.innerHTML = `
        <div class="popup-header">
            <h3>${title}</h3>
        </div>
        <div class="popup-body">
            <p>${message}</p>
        </div>
        <div class="popup-footer">
            <button class="popup-btn">OK</button>
        </div>
    `;

    overlay.appendChild(popup);
    document.body.appendChild(overlay);

    setTimeout(() => overlay.classList.add("show"), 10);

    popup.querySelector(".popup-btn").onclick = () => {
        overlay.classList.remove("show");
        setTimeout(() => overlay.remove(), 300);
    };
}
// ===============================
// SAMPLE BUTTON LOGIC (RANDOM – FINAL)
// ===============================
document.addEventListener("DOMContentLoaded", () => {
  const sampleBtn = document.getElementById("sampleBtn");
  const headerInput = document.getElementById("emailHeader");

  if (!sampleBtn || !headerInput || !EMAIL_SAMPLES.length) return;

  sampleBtn.addEventListener("click", () => {

    let randomIndex;

    // Prevent same sample twice in a row
    do {
      randomIndex = Math.floor(Math.random() * EMAIL_SAMPLES.length);
    } while (randomIndex === window.__lastSampleIndex);

    window.__lastSampleIndex = randomIndex;

    headerInput.value = EMAIL_SAMPLES[randomIndex].header;
  });
});


/* =========================================
   CLEAN SIDEBAR + PREVIEW CONTROL
========================================= */

document.addEventListener("DOMContentLoaded", () => {

    // SIDEBAR TOGGLE
    const toggle = document.getElementById("menuToggle");
    const sidebar = document.querySelector(".sidebar");

    if (toggle && sidebar) {
        toggle.addEventListener("click", (e) => {
            e.stopPropagation();
            sidebar.classList.toggle("active");
        });

        // Click outside closes sidebar
        document.addEventListener("click", (e) => {
            if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
                sidebar.classList.remove("active");
            }
        });
    }

    // PREVIEW DROPDOWN (FIXED)
    document.querySelectorAll(".preview-toggle").forEach(toggle => {
        toggle.addEventListener("click", () => {
            const parent = toggle.closest(".command-preview");
            parent.classList.toggle("collapsed");
        });
    });

});
/* =========================================
   LANDING SCROLL ANIMATION
========================================= */

const revealElements = document.querySelectorAll(
  ".platform-card, .stat-card, .value-card"
);

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = 1;
      entry.target.style.transform = "translateY(0)";
    }
  });
}, { threshold: 0.1 });

revealElements.forEach(el => {
  el.style.opacity = 0;
  el.style.transform = "translateY(20px)";
  el.style.transition = "all 0.5s ease";
  observer.observe(el);
});