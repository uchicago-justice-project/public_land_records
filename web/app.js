Promise.all([d3.json("data.json")])
  .then(ready)
  .catch((err) => {
    console.log(err);
  });

function ready(res) {
  let raw = res[0];
  console.log(raw);

  let mapWidth = 600;
  let mapHeight = 550;
  let minYear = 1820;
  let maxYear = 1880;
  let currentYear = minYear;

  let yearTitle = d3.select("#year");

  yearTitle.text(currentYear);

  let features = {};
  for (let key in raw.objects) {
    features[key] = topojson.feature(raw, raw.objects[key]);
  }

  let projs = {};
  for (let key in features) {
    projs[key] = d3
      .geoTransverseMercator()
      .rotate([88 + 20 / 60, -36 - 40 / 60])
      .fitSize([mapWidth, mapHeight], features[key]);
  }

  let paths = {};
  for (let key in projs) {
    paths[key] = d3.geoPath().projection(projs[key]);
  }

  let mapSvg = d3.select("body").select("#map");
  mapSvg.attr("viewBox", `0 0 ${mapWidth} ${mapHeight}`);

  let color = d3
    .scaleSequential(d3.interpolateMagma)
    .domain([minYear, maxYear]);
  let getColor = (d) => color(d.properties.YEAR);

  mapSvg
    .append("g")
    .selectAll(".section")
    .data(features.chicago_sections.features)
    .join("path")
    .attr("d", paths.chicago_sections)
    .attr("class", "section")
    .style("fill", "none")
    .style("stroke", "black")
    .style("stroke-width", "0.25")
    .style("pointer-events", "none");

  mapSvg
    .append("g")
    .selectAll(".purchase")
    .data(features.chicago_purchases.features)
    .join("path")
    .attr("d", paths.chicago_purchases)
    .attr("class", "purchase")
    .style("fill", getColor)
    .style("stroke", "black")
    .style("opacity", "0")
    .style("stroke-width", "0.25");

  mapSvg
    .append("g")
    .selectAll(".city")
    .data(features.city_limits.features)
    .join("path")
    .attr("d", paths.city_limits)
    .attr("class", "city")
    .attr("id", (d) => {
      return `limit-${d.properties.YEAR}`;
    })
    .style("fill", "none")
    .style("stroke", "yellow")
    .style("stroke-width", "2")
    .style("opacity", 0)
    .style("pointer-events", "none");

  //   mapSvg
  //     .append("g")
  //     .selectAll(".village")
  //     .data(features.chicago_indigenous_villages.features)
  //     .join("path")
  //     .attr("d", paths.chicago_purchases)
  //     .attr("class", "village")
  //     .style("fill", "none")
  //     .style("stroke", "orange")
  //     .style("stroke-width", "2")
  //     .style("pointer-events", "none");

  //   mapSvg
  //     .append("g")
  //     .selectAll(".settlement")
  //     .data(features.settlements.features)
  //     .join("path")
  //     .attr("d", paths.settlements)
  //     .attr("class", "settlement")
  //     .style("fill", "none")
  //     .style("stroke", "lightgreen")
  //     .style("stroke-width", "2")
  //     .style("pointer-events", "none");

  let popup = mapSvg
    .append("g")
    .attr("class", "mouse-over-popup")
    .style("display", "none");

  popup
    .append("rect")
    .attr("x", 0)
    .attr("y", 0)
    .attr("width", 240)
    .attr("height", 40)
    .style("fill", "white");

  popup
    .append("text")
    .attr("class", "purchaser")
    .attr("x", 5)
    .attr("y", 15)
    .style("font-size", 12);
  popup
    .append("text")
    .attr("class", "location")
    .attr("x", 5)
    .attr("y", 30)
    .style("font-size", 12);

  const purchases_geo = d3.selectAll(".purchase");
  const city_geo = d3.selectAll(".city");

  purchases_geo
    .on("mouseover", (event, d) => {
      popup
        .attr(
          "transform",
          `translate(${paths.chicago_purchases.centroid(d)[0] - 60},${
            paths.chicago_purchases.centroid(d)[1] + 10
          })`
        )
        .style("display", "block");

      popup
        .select(".purchaser")
        .text(`Purchaser: ${d.properties["Cleaned Name"]}`);

      popup
        .select(".location")
        .text(`Location ${d.properties["Township"]}-${d.properties["Range"]}`);
    })
    .on("mouseout", (event, d) => {
      popup.style("display", "none");
    });

  function update(year) {
    currentYear = year;
    if (year == maxYear) {
      yearTitle.text("All");
      purchases_geo.style("opacity", "1");
    } else {
      yearTitle.text(currentYear);
      purchases_geo
        .filter((d) => d.properties.YEAR > year)
        .style("opacity", "0");
      purchases_geo
        .filter((d) => d.properties.YEAR <= year)
        .style("opacity", "1");
    }

    city_geo.filter((d) => d.properties.YEAR <= year).style("opacity", "1");
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
    const playAction = setInterval(() => {
      if (currentYear == maxYear) {
        clearInterval(playAction);
      }
      currentYear = currentYear + 1;
      slider.value(currentYear);
    }, 300);

    d3.select("#pause").on("click", () => {
      clearInterval(playAction);
    });
  }

  d3.select("#play").on("click", play);
}
