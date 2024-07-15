import sys, math
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent / "shared"))
import challenge_builder as mrcb
from geopy import distance

## Functions specific to this challenge

# Use this function to determine if a task needs to be created for a given element
# use this function for filtering things that overpass cannot filter, maybe by using a function from a different file that you specifically implemented for this task
# if your overpass query already returns all elements that need to be fixed, make this function return True
def needsTask(e):
    # Every element looks like this:
    # {"type": "relation", "id": 4751, "bounds": {"minlat": 51.4922560, "minlon": 7.4171198, "maxlat": 51.4923844, "maxlon": 7.4176189 }},
    # An element needs a task if either the vertical or the horizontal bbox edge is longer than a predefinded value in meters
    max_distance = 1000
    # Calculate the length of the longitude difference of the bbox
    e['bounds'] = {}
    e['bounds']['minlat'] = e['geometry']['coordinates'][0][1]
    e['bounds']['minlon'] = e['geometry']['coordinates'][0][0]
    e['bounds']['maxlat'] = e['geometry']['coordinates'][2][1]
    e['bounds']['maxlon'] = e['geometry']['coordinates'][2][0]
    # Calculate the length of the longitude difference of the bbox
    lon_diff = distance.distance((e['bounds']['minlat'], e['bounds']['minlon']), (e['bounds']['minlat'], e['bounds']['maxlon'])).m
    # Calculate the length of the latitude difference of the bbox
    lat_diff = distance.distance((e['bounds']['minlat'], e['bounds']['minlon']), (e['bounds']['maxlat'], e['bounds']['minlon'])).m
    # If either the longitude or the latitude difference is longer than 1000 meters, return the name of the element
    if lon_diff > max_distance or lat_diff > max_distance:
        return True



opQuery = """
[out:json][timeout:250];
area(id:3600051477)->.searchArea;
relation["public_transport"="stop_area"](area.searchArea);
foreach {
  >> -> .ancestors;
  make myCustomElement
    ::id=min(id()),
    ::geom=ancestors.gcat(geom());
  out bb;
}
"""

op = mrcb.Overpass()
resultElements = op.getElementsFromQuery(opQuery)

challenge = mrcb.Challenge()

for element in resultElements:
    if needsTask(element):
        geomCls = mrcb.Geometry.fromOverpassElement(element)
        mainFeature = mrcb.GeoFeature.withId(
            osmType="relation", 
            osmId=element["id"],
            geometry=geomCls, 
            properties={})
        t = mrcb.Task(
            mainFeature=mainFeature)
        challenge.addTask(t)

challenge.saveToFile("large_stop_area_bbox.json")

    