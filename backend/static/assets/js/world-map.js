(async function () {
    const width = 1000;
    const height = 500;

    const svg = d3.select("#geoMap");
    if (svg.empty()) {
        console.error("geoMap SVG not found");
        return;
    }

    // Projection (this makes the map look real)
    const projection = d3.geoNaturalEarth1()
        .scale(170)
        .translate([width / 2, height / 2]);

    // 🔴 EXPOSE PROJECTION (FIX)
    window.__EMAIL_MAP_PROJECTION__ = projection;

    const path = d3.geoPath().projection(projection);

    // Group for countries
    const mapLayer = svg.insert("g", ":first-child")
        .attr("id", "mapLayer");

    try {
        const world = await d3.json(
            "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json"
        );

        const countries = topojson.feature(
            world,
            world.objects.countries
        ).features;

        mapLayer.selectAll("path")
            .data(countries)
            .enter()
            .append("path")
            .attr("d", path)
            .attr("fill", "#e5e7eb")
            .attr("stroke", "#cbd5e1")
            .attr("stroke-width", 0.5);

        console.log("World map rendered");

    } catch (err) {
        console.error("Failed to load world map", err);
    }
})();
