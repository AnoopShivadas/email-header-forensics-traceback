document.addEventListener("DOMContentLoaded", () => {
  const openBtn = document.getElementById("openExport");
  const backdrop = document.getElementById("exportBackdrop");
  const closeBtn = document.getElementById("closeExport");

  if (!openBtn || !backdrop) return;

  openBtn.onclick = () => backdrop.classList.add("active");
  closeBtn.onclick = () => backdrop.classList.remove("active");

  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) backdrop.classList.remove("active");
  });

  // ===============================
  // EXPORT HANDLERS (CSV / JSON / PDF)
  // ===============================
  document.querySelectorAll(".export-option").forEach(btn => {
    btn.addEventListener("click", () => {
      const format = btn.dataset.format;
      const params = new URLSearchParams(window.location.search);
      const analysisId = params.get("analysis_id");

      if (!analysisId) {
        alert("No analysis found to export.");
        return;
      }

      // Backend already supports all formats
      window.location.href =
            `/export/analysis/${analysisId}/${format}`;

      backdrop.classList.remove("active");
    });
  });
});
