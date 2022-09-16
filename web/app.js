Promise.all([d3.json("Streets.json"), d3.json("cook_county.json")])
  .then(ready)
  .catch((err) => {
    console.log(err);
  });

function ready(res) {
  let streetsRaw = res[0];
  let tractsRaw = res[1];
  let mapWidth = 600;
  let mapHeight = 550;

  let streets = topojson.feature(streetsRaw, streetsRaw.objects.Streets);
  let tracts = topojson.feature(
    tractsRaw,
    tractsRaw.objects.cook_county_with_geometries
  );

  let mapSvg = d3.select("body").select("#map");
  mapSvg.attr("viewBox", `0 0 ${mapWidth} ${mapHeight}`);

  console.log(tracts);

  let streetsProj = d3.geoAlbersUsa().fitSize([mapWidth, mapHeight], streets);
  let tractsProj = d3.geoAlbersUsa().fitSize([mapWidth, mapHeight], tracts);

  let pathStreets = d3.geoPath().projection(streetsProj);
  let pathTracts = d3.geoPath().projection(tractsProj);

  mapSvg
    .append("g")
    .selectAll(".streets")
    .data(streets.features)
    .join("path")
    .attr("d", pathStreets)
    .style("fill", "none")
    .style("stroke", "black")
    .style("stroke-width", "0.25")
    .style("pointer-events", "none");

  //   mapSvg
  //     .append("g")
  //     .selectAll(".tracts")
  //     .data(tracts.features)
  //     .join("path")
  //     .attr("d", pathTracts)
  //     .style("fill", "blue")
  //     .style("opacity", "0.25")
  //     .style("stroke", "black")
  //     .style("stroke-width", "0.25")
  //     .style("pointer-events", "none");
}
