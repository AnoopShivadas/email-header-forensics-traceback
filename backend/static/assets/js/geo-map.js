window.addEventListener("load", async () => {
  const svg = document.getElementById("geoMap");
  const tableBody = document.getElementById("geoTableBody");
  const replayBtn = document.getElementById("replayRoute");
  if (!svg) return;

  const projection = window.__EMAIL_MAP_PROJECTION__;
  const isMobile = window.innerWidth <= 768;
  const svgWidth = svg.clientWidth;
  const svgHeight = isMobile ? 250 : 500;

  // Apply height properly
  svg.setAttribute("height", svgHeight);

  // Apply projection correctly for BOTH views
  projection
    .translate([svgWidth / 2, svgHeight / 2])
    .scale(isMobile ? svgWidth / 4.2 : svgWidth / 6);

  let routeLayer = document.getElementById("routeLayer");
  if (!routeLayer) {
    routeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    routeLayer.id = "routeLayer";
    svg.appendChild(routeLayer);
  }

  // --------------------------------------------------
  // TOOLTIP
  // --------------------------------------------------
  const tooltip = document.createElement("div");
  tooltip.className = "geo-tooltip";
  document.body.appendChild(tooltip);

  // Preserve first 2 colors
  const baseColors = ["#22c55e", "#3b82f6"];

  // Extra colors for 3+ hops
  const extraColors = ["#f97316", "#a855f7", "#ef4444", "#06b6d4", "#eab308"];

  const params = new URLSearchParams(window.location.search);
  const analysisId = params.get("analysis_id");
  const apiUrl = analysisId
    ? `/api/geolocation/${analysisId}`
    : `/api/geolocation/latest`;

  const res = await fetch(apiUrl);
  if (!res.ok) return;
  const data = await res.json();
  const hops = data.hops || [];

  // --------------------------------------------------
  // TABLE (UNCHANGED)
  // --------------------------------------------------
  if (tableBody) {
    tableBody.innerHTML = "";
    hops.forEach((h, i) => {
      tableBody.innerHTML += `
        <tr>
          <td>${h.stage || `Hop ${i + 1}`}</td>
          <td>${h.ip}</td>
          <td>${h.city}</td>
          <td>${h.country}</td>
          <td>${h.org}</td>
          <td>${h.timestamp || "Auto-generated"}</td>
        </tr>
      `;
    });
  }

  // --------------------------------------------------
  // PROJECT POINTS (FIXED – NO HOP LOSS)
  // --------------------------------------------------
  const points = hops.map((h, i) => {

    if (h.latitude == null || h.longitude == null) {
      return { inactive: true };
    }

    const p = projection([h.longitude, h.latitude]);
    if (!p) {
      return { inactive: true };
    }

    return {
      x: p[0],
      y: p[1],
      color:
        i < 2
          ? baseColors[i]
          : extraColors[(i - 2) % extraColors.length],
      label: h.stage || `Hop ${i + 1}`,
      ip: h.ip,
      city: h.city,
      country: h.country,
      org: h.org,
      inactive: false
    };
  });

  // Filter only drawable points for animation logic
  const activePoints = points.filter(p => !p.inactive);
  if (!activePoints.length) return;

  // --------------------------------------------------
  // DOT WITH TOOLTIP
  // --------------------------------------------------
  function drawDot(p, isLast) {
    const dot = document.createElementNS(svg.namespaceURI, "circle");
    dot.setAttribute("cx", p.x);
    dot.setAttribute("cy", p.y);
    dot.setAttribute("r", isLast ? 7 : 5);
    dot.setAttribute("fill", p.color);
    dot.classList.add("pulse-dot");
    routeLayer.appendChild(dot);

    dot.addEventListener("mouseenter", () => {
      tooltip.innerHTML = `
        <strong>${p.label}</strong><br>
        IP: ${p.ip}<br>
        ${p.city}, ${p.country}<br>
        ${p.org}
      `;
      tooltip.style.opacity = "1";
    });

    dot.addEventListener("mousemove", e => {
      tooltip.style.left = e.clientX + 12 + "px";
      tooltip.style.top = e.clientY + 12 + "px";
    });

    dot.addEventListener("mouseleave", () => {
      tooltip.style.opacity = "0";
    });
  }

  // --------------------------------------------------
  // SMART LINE ANIMATION
  // --------------------------------------------------
  function drawSmoothDashedLine(from, to, color, duration = 3000) {
    return new Promise(resolve => {
      const line = document.createElementNS(svg.namespaceURI, "line");

      line.setAttribute("x1", from.x);
      line.setAttribute("y1", from.y);
      line.setAttribute("x2", to.x);
      line.setAttribute("y2", to.y);
      line.setAttribute("stroke", color);
      line.setAttribute("stroke-width", "2");
      line.setAttribute("stroke-linecap", "round");
      line.setAttribute("stroke-dasharray", "6 6");

      const length = Math.hypot(to.x - from.x, to.y - from.y);
      line.style.strokeDashoffset = length;
      line.style.strokeDasharray = `${length} ${length}`;

      routeLayer.appendChild(line);
      line.getBoundingClientRect();

      line.style.transition =
        `stroke-dashoffset ${duration}ms cubic-bezier(0.4, 0.0, 0.2, 1)`;
      line.style.strokeDashoffset = "0";

      setTimeout(resolve, duration);
    });
  }

  // --------------------------------------------------
  // SMART REPLAY ENGINE (NO INDEX SHIFT BUG)
  // --------------------------------------------------
  async function replayRoute() {
    routeLayer.innerHTML = "";

    const hopCount = activePoints.length;
    const dotDelay = hopCount <= 2 ? 700 : 300;
    const lineSpeed = hopCount <= 2 ? 3000 : 1200;

    drawDot(activePoints[0], hopCount === 1);
    await wait(dotDelay);

    for (let i = 1; i < activePoints.length; i++) {
      await drawSmoothDashedLine(
        activePoints[i - 1],
        activePoints[i],
        activePoints[i].color,
        lineSpeed
      );

      drawDot(activePoints[i], i === activePoints.length - 1);
      await wait(dotDelay);
    }
  }

  function wait(ms) {
    return new Promise(r => setTimeout(r, ms));
  }

  // Auto-play once
  replayRoute();

  // --------------------------------------------------
  // REPLAY BUTTON
  // --------------------------------------------------
  replayBtn?.addEventListener("click", async () => {
    if (replayBtn.disabled) return;
    replayBtn.disabled = true;

    await replayRoute();

    replayBtn.disabled = false;
  });
});