import sys
sys.path.append('../../include')
import MRFactory as mrf

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
      
      out center tags;
  }
}
"""

op = mrf.Overpass()
resultElements = op.getElementsFromQuery(opQuery)

challenge = mrf.Challenge()

for element in resultElements:
	centerPoint = mrf.getElementCenterPoint(element)
	mainFeature = mrf.MainGeoFeature(
		geometry=centerPoint, 
		properties={}, 
		osmType="relation", 
		osmId=element["id"])
	suggestedName = element["tags"]["name"]
	cooperativeWork = mrf.TagFix(
		osmType="relation", 
		osmId=element["id"], 
		tags={"name": suggestedName})
	t = mrf.Task(
		mainFeature=mainFeature, 
		additionalFeatures=[], 
		cooperativeWork=cooperativeWork)
	challenge.addTask(t)

challenge.saveToFile("stop_area_names_from_platform_names.json")