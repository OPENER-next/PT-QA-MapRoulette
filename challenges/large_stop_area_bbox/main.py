import sys, math
sys.path.append('../../include')
import challenge_builder as mrcb

## Functions specific to this challenge

def get_distance_from_coordinates(lat1, lon1, lat2, lon2):
    R = 6371000  # Radius of the Earth in meters
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

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
    lon_diff = get_distance_from_coordinates(e['bounds']['minlat'], e['bounds']['minlon'], e['bounds']['minlat'], e['bounds']['maxlon'])
    # Calculate the length of the latitude difference of the bbox
    lat_diff = get_distance_from_coordinates(e['bounds']['minlat'], e['bounds']['minlon'], e['bounds']['maxlat'], e['bounds']['minlon'])
    # If either the longitude or the latitude difference is longer than 100 meters, return the name of the element
    print(lon_diff, lat_diff)
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
        bboxGeometry = mrcb.getElementGeometry(element)
        print(bboxGeometry)
        mainFeature = mrcb.GeoFeature.withId(
            osmType="relation", 
            osmId=element["id"],
            geometry=bboxGeometry, 
            properties={})
        mainFeature.convertPolygonToClosedString()
        t = mrcb.Task(
            mainFeature=mainFeature, 
            additionalFeatures=[], 
            cooperativeWork=None)
        challenge.addTask(t)

challenge.saveToFile("large_stop_area_bbox.json")

    