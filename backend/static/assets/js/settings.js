/* =========================================
   SETTINGS PAGE SCRIPT (FIXED VERSION)
========================================= */

document.addEventListener("DOMContentLoaded", () => {

    // =========================
    // LOAD SETTINGS
    // =========================
    loadSettings();

    async function loadSettings() {
        try {
            const res = await fetch("/api/settings");
            if (!res.ok) return;

            const data = await res.json();

            const autoSave = document.getElementById("autoSaveToggle");
            const emailNotify = document.getElementById("emailNotifyToggle");
            const exportFormat = document.getElementById("exportFormat");

            if (autoSave) autoSave.checked = data.auto_save;
            if (emailNotify) emailNotify.checked = data.email_notifications;
            if (exportFormat) exportFormat.value = data.export_format;

        } catch (err) {
            console.error("Failed to load settings");
        }
    }

    // =========================
    // UPDATE SETTINGS
    // =========================
    async function updateSetting(payload) {
        try {
            await fetch("/api/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
        } catch (err) {
            console.error("Failed to update setting");
        }
    }

    // =========================
    // TOGGLES
    // =========================
    document.addEventListener("change", (e) => {
        if (e.target.id === "autoSaveToggle") {
            updateSetting({ auto_save: e.target.checked });
        }

        if (e.target.id === "emailNotifyToggle") {
            updateSetting({ email_notifications: e.target.checked });
        }

        if (e.target.id === "exportFormat") {
            updateSetting({ export_format: e.target.value });
        }
    });

    // =========================
    // CLEAR HISTORY FIX (MAIN PART)
    // =========================
    const clearBtn = document.getElementById("clearHistoryBtn");
    const modal = document.getElementById("confirmModal");
    const cancelBtn = document.getElementById("cancelClearBtn");
    const confirmBtn = document.getElementById("confirmClearBtn");

    console.log("Clear Button:", clearBtn); // DEBUG

    if (clearBtn && modal) {
        clearBtn.addEventListener("click", () => {
            console.log("Clear Clicked"); // DEBUG
            modal.classList.remove("hidden");
        });
    }

    if (cancelBtn && modal) {
        cancelBtn.addEventListener("click", () => {
            modal.classList.add("hidden");
        });
    }

    if (confirmBtn) {
        confirmBtn.addEventListener("click", async () => {
            try {
                const res = await fetch("/api/history/clear", {
                    method: "POST"
                });

                if (res.ok) {
                    alert("History cleared successfully");
                    location.reload();
                } else {
                    alert("Failed to clear history");
                }

            } catch (err) {
                console.error("Failed to clear history", err);
            }
        });
    }

    // =========================
    // LAST LOGIN TIME
    // =========================
    const el = document.getElementById("lastLoginTime");
    if (el) {
        const raw = el.dataset.utc;
        if (raw) {
            const cleaned = raw.replace(" (UTC)", "");
            const parsed = new Date(cleaned + " UTC");

            if (!isNaN(parsed)) {
                const localTime = parsed.toLocaleString(undefined, {
                    year: "numeric",
                    month: "short",
                    day: "2-digit",
                    hour: "2-digit",
                    minute: "2-digit",
                    hour12: true
                });

                el.textContent = `${localTime} (Local)`;
            }
        }
    }

    // =========================
    // THEME SWITCH
    // =========================
    document.addEventListener("click", (e) => {
        if (!e.target.classList.contains("theme-btn")) return;

        const theme = e.target.dataset.theme;

        document.documentElement.classList.toggle(
            "dark-theme",
            theme === "dark"
        );

        document.body.classList.toggle(
            "dark-theme",
            theme === "dark"
        );
    });

});