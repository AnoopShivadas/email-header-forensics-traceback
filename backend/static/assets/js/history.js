let currentPage = 1;
let totalPages = 1;

document.addEventListener("DOMContentLoaded", () => {
    loadHistoryStats();
    loadHistoryTable();

    document.getElementById("applyFilters")?.addEventListener("click", () => {
        currentPage = 1;
        loadHistoryTable(true);
    });

    document.getElementById("prevPage")?.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            loadHistoryTable(true);
        }
    });

    document.getElementById("nextPage")?.addEventListener("click", () => {
        if (currentPage < totalPages) {
            currentPage++;
            loadHistoryTable(true);
        }
    });
});


/* ===============================
   STATS
================================ */
async function loadHistoryStats() {
    try {
        const res = await fetch("/api/history/stats");
        const data = await res.json();

        document.getElementById("stat-total").textContent = data.total ?? 0;
        document.getElementById("stat-safe").textContent = data.safe ?? 0;
        document.getElementById("stat-suspicious").textContent = data.suspicious ?? 0;
        document.getElementById("stat-threat").textContent = data.threat ?? 0;

    } catch (err) {
        console.error("Failed to load history stats", err);
    }
}


/* ===============================
   HISTORY TABLE + PAGINATION
================================ */
async function loadHistoryTable(useFilters = false) {
    const tbody = document.getElementById("history-table-body");
    if (!tbody) return;

    tbody.innerHTML = "";

    let url = `/api/history?page=${currentPage}&page_size=5`;

    if (useFilters) {
        const risk = document.getElementById("filter-risk")?.value;
        const days = document.getElementById("filter-time")?.value;

        if (risk) url += `&risk=${encodeURIComponent(risk)}`;
        if (days) url += `&days=${encodeURIComponent(days)}`;
    }

    try {
        const res = await fetch(url);
        const data = await res.json();

        totalPages = data.total_pages || 1;
        document.getElementById("currentPage").textContent = currentPage;

        updatePaginationButtons();

        if (!data.items.length) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align:center; opacity:0.6">
                        No analysis history found
                    </td>
                </tr>`;
            return;
        }

        data.items.forEach(row => {
            const riskClass =
                row.risk_score >= 70 ? "high" :
                row.risk_score >= 40 ? "medium" : "low";

            const badgeClass =
                row.verdict === "Threat" ? "badge-danger" :
                row.verdict === "Suspicious" ? "badge-warning" :
                "badge-success";

            const tr = document.createElement("tr");
            tr.style.cursor = "pointer";

            tr.innerHTML = `
                <td>${row.date}</td>
                <td>${row.sender}</td>
                <td>${row.subject}</td>
                <td><span class="risk ${riskClass}">${row.risk_score}</span></td>
                <td><span class="badge ${badgeClass}">${row.verdict}</span></td>
                <td class="actions">
                    <span class="action-view">👁️</span>
                    <span class="action-download">📥</span>
                </td>
            `;

            tr.addEventListener("click", () => {
                window.location.href = `/results?analysis_id=${row.id}`;
            });

            tr.querySelector(".action-download").addEventListener("click", (e) => {
                e.stopPropagation();
                downloadSingleAnalysis(row.id);
            });

            tbody.appendChild(tr);
        });

    } catch (err) {
        console.error("Failed to load history table", err);
    }
}


function updatePaginationButtons() {
    const prev = document.getElementById("prevPage");
    const next = document.getElementById("nextPage");

    if (!prev || !next) return;

    prev.disabled = currentPage <= 1;
    next.disabled = currentPage >= totalPages;
}
/* ===============================
   STAT COUNT-UP ANIMATION
================================ */
function animateStats() {
    document.querySelectorAll(".history-stats .stat-box strong").forEach(el => {
        const target = parseInt(el.textContent, 10);
        if (isNaN(target)) return;

        let current = 0;
        const step = Math.max(1, Math.floor(target / 30));

        const interval = setInterval(() => {
            current += step;
            if (current >= target) {
                el.textContent = target;
                clearInterval(interval);
            } else {
                el.textContent = current;
            }
        }, 20);
    });
}

/* Hook into existing stats loader safely */
const __loadStats = loadHistoryStats;
loadHistoryStats = async function () {
    await __loadStats();
    animateStats();
};
// ===============================
// CUSTOM RISK DROPDOWN
// ===============================

document.addEventListener("DOMContentLoaded", () => {

    const dropdown = document.getElementById("riskDropdown");
    if (!dropdown) return;

    const selected = dropdown.querySelector(".dropdown-selected");
    const options = dropdown.querySelectorAll(".dropdown-options div");
    const hiddenInput = document.getElementById("filter-risk");

    selected.addEventListener("click", () => {
        dropdown.classList.toggle("open");
    });

    options.forEach(option => {
        option.addEventListener("click", () => {
            selected.textContent = option.textContent;
            hiddenInput.value = option.dataset.value;
            dropdown.classList.remove("open");
        });
    });

    document.addEventListener("click", (e) => {
        if (!dropdown.contains(e.target)) {
            dropdown.classList.remove("open");
        }
    });

});
// ===============================
// CUSTOM TIME DROPDOWN
// ===============================

document.addEventListener("DOMContentLoaded", () => {

    const dropdown = document.getElementById("timeDropdown");
    if (!dropdown) return;

    const selected = dropdown.querySelector(".dropdown-selected");
    const options = dropdown.querySelectorAll(".dropdown-options div");
    const hiddenInput = document.getElementById("filter-time");

    selected.addEventListener("click", () => {
        dropdown.classList.toggle("open");
    });

    options.forEach(option => {
        option.addEventListener("click", () => {
            selected.textContent = option.textContent;
            hiddenInput.value = option.dataset.value;
            dropdown.classList.remove("open");
        });
    });

    document.addEventListener("click", (e) => {
        if (!dropdown.contains(e.target)) {
            dropdown.classList.remove("open");
        }
    });

});