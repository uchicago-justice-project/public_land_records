Promise.all([
  d3.json("cook_county_border.json"),
  d3.json("cook_county_with_geometries.json"),
])
  .then(ready)
  .catch((err) => {
    console.log(err);
  });

function ready(res) {
  let borderRaw = res[0];
  let purchasesRaw = res[1];
  let mapWidth = 600;
  let mapHeight = 550;
  let minYear = 1820;
  let maxYear = 1880;

  let border = topojson.feature(
    borderRaw,
    borderRaw.objects.Cook_County_Border
  );
  let purchases = topojson.feature(
    purchasesRaw,
    purchasesRaw.objects.cook_county_with_geometries4
  );

  let mapSvg = d3.select("body").select("#map");
  mapSvg.attr("viewBox", `0 0 ${mapWidth} ${mapHeight}`);

  let borderProj = d3
    .geoTransverseMercator()
    .rotate([88 + 20 / 60, -36 - 40 / 60])
    .fitSize([mapWidth, mapHeight], border);

  let purchasesProj = d3
    .geoTransverseMercator()
    .rotate([88 + 20 / 60, -36 - 40 / 60])
    .fitSize([mapWidth, mapHeight], purchases);

  let pathBorder = d3.geoPath().projection(borderProj);
  let pathPurchases = d3.geoPath().projection(purchasesProj);

  let color = d3
    .scaleSequential(d3.interpolateMagma)
    .domain([minYear, maxYear]);
  let getColor = (d) => color(d.properties.YEAR);

  mapSvg
    .append("g")
    .selectAll(".border")
    .data(border.features)
    .join("path")
    .attr("d", pathBorder)
    .style("fill", "none")
    .style("stroke", "black")
    .style("stroke-width", "0.25")
    .style("pointer-events", "none");

  mapSvg
    .append("g")
    .selectAll(".purchase")
    .data(purchases.features)
    .join("path")
    .attr("d", pathPurchases)
    .attr("class", "purchase")
    .style("fill", getColor)
    .style("stroke", "black")
    .style("opacity", "0")
    .style("stroke-width", "0.25")
    .style("pointer-events", "none");

  const purchases_geo = d3.selectAll(".purchase");

  function update(year) {
    if (year == maxYear) {
      purchases_geo.style("opacity", "1");
    } else {
      purchases_geo
        .filter((d) => d.properties.YEAR > year)
        .style("opacity", "0");
      purchases_geo
        .filter((d) => d.properties.YEAR <= year)
        .style("opacity", "1");
    }
  }

  let slider = d3
    .sliderHorizontal()
    .min(minYear)
    .max(maxYear)
    .step(1)
    .width(400)
    .displayValue(true)
    .tickFormat(d3.format(""))
    .displayFormat(d3.format(""))
    .on("onchange", update);

  d3.select("#slider")
    .attr("viewBox", `0 0 ${500} ${100}`)
    .append("g")
    .attr("transform", "translate(30,30)")
    .call(slider);

  function play() {
    let currentYear = slider.value();

    const playAction = setInterval(() => {
      if (currentYear == maxYear) {
        clearInterval(playAction);
      }
      currentYear = currentYear + 1;
      slider.value(currentYear);
    }, 300);
  }

  d3.select("#play").on("click", play);
}
