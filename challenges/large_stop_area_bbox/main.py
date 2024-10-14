import sys, math
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent / "shared"))
import challenge_builder as mrcb
from turfpy.measurement import distance
from geojson import Point

## Functions specific to this challenge

opQuery = """
[out:json][timeout:250];
area(id:3600051477)->.searchArea;
relation["public_transport"="stop_area"](area.searchArea);
foreach {
  >> -> .ancestors;
  make myCustomElement
    ::id=min(id()),
    ::geom=hull(ancestors.gcat(geom()));
  out bb;
}
"""

# Use this function to determine if a task needs to be created for a given element
# use this function for filtering things that overpass cannot filter, maybe by using a function from a different file that you specifically implemented for this task
# if your overpass query already returns all elements that need to be fixed, make this function return True
def needsTask(e):
    # An element needs a task if either the vertical or the horizontal bbox edge is longer than a predefined value in meters
    max_distance = 1000
    bbox = e['geometry']['coordinates'][0]
    point1 = Point((bbox[0][0], bbox[0][1]))
    point2 = Point((bbox[1][0], bbox[1][1]))
    point3 = Point((bbox[2][0], bbox[2][1]))
    # Calculate the length of the longitude/latitude difference of the bbox
    lon_diff = distance(point1, point3) * 1000  # Convert kilometers to meters
    lat_diff = distance(point1, point2) * 1000  # Convert kilometers to meters
    # If either the longitude or the latitude difference is longer than 1000 meters, return True
    if lon_diff > max_distance or lat_diff > max_distance:
        return True

op = mrcb.Overpass()
resultElements = op.queryElementsAsGeoJSON(opQuery)

challenge = mrcb.Challenge()

for element in resultElements:
    if needsTask(element):
        mainFeature = mrcb.GeoFeature.withId(
            osmType="relation",
            osmId=element["properties"]["@id"],
            geometry=element["geometry"],
            properties={})
        task = mrcb.Task(
            mainFeature=mainFeature)
        challenge.addTask(task)

challenge.saveToFile("large_stop_area_bbox.json")
