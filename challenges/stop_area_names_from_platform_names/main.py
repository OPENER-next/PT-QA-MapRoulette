import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent / "shared"))
from turfpy.measurement import center, bbox, bbox_polygon
import challenge_builder as mrcb

opQuery = """
[out:json][timeout:250];
area(id:3600051477)->.searchArea;
rel["public_transport"="stop_area"][!"name"](area.searchArea)->.stop_areas;
// for each stop area
foreach.stop_areas -> .stop_area {
  // recurse relation fully down (select all ancestors)
  // required to construct the full geometry for relations that contain other relations
  // and to get members of type relation (single > only returns ways and nodes)
  .stop_area >>;
  nwr._["public_transport"="platform"];

  if (u(t["name"]) != "< multiple values found >" && u(t["name"]) != "") {
      make StopArea
      name=u(t["name"]),
      // get stop are relation id
      ::id=stop_area.u(id()),
      // group geometries into one
      ::geom=hull(gcat(geom()));

      out geom tags;
  }
}
"""

op = mrcb.Overpass()
resultElements = op.queryElementsAsGeoJSON(opQuery)

challenge = mrcb.Challenge()

for element in resultElements:
    if element["geometry"]["type"] == "Polygon":
        geometry=element["geometry"]
    elif element["geometry"]["type"] == "LineString":
        geometry=bbox_polygon(bbox(element["geometry"])).geometry
    else:
        geometry=center(element["geometry"]).geometry

    mainFeature = mrcb.GeoFeature.withId(
        osmType="relation",
        osmId=element["properties"]["@id"],
        geometry=geometry,
        properties={})
    suggestedName = element["properties"]["name"]
    cooperativeWork = mrcb.TagFix(
        osmType="relation",
        osmId=element["properties"]["@id"],
        tags={"name": suggestedName})
    task = mrcb.Task(
        mainFeature=mainFeature,
        additionalFeatures=[],
        cooperativeWork=cooperativeWork)
    challenge.addTask(task)

challenge.saveToFile("stop_area_names_from_platform_names.json")
