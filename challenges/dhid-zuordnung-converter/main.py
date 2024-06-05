import json
import urllib.parse
import requests
# Imports that are specific to this challenge
import get_elements_around as gea

# Use this function to determine if a task needs to be created for a given element
# use this function for filtering things that overpass cannot filter, maybe by using a function from a different file that you specifically implemented for this task
# if your overpass query already returns all elements that need to be fixed, make this function return True
def needsTask(e):
    return True


TASKS = []

response = requests.get('ENTER_URL_HERE')
dizydata = response.text.split('\n')
# remove the last line, which is empty
dizydata.pop()
# For testing purposes, only use the first 100 lines of data
#dizydata = dizydata[:531]
# iterate over all lines of data
for line in dizydata:
    # remove the first character of the line, which is a control character
    line = line[1:]
    # parse the line as json
    data = json.loads(line)
    # Get the necessary data from the json
    osmfullid = data["features"][0]["properties"]["@id"]
    ## Hack while the MR fix is not deployed - skip this task if the osmid contains relation
    dhid = data["features"][0]["properties"]["zhv-dhid"]
    # Modify the json to include the cooperative work
    data["cooperativeWork"] = {
                "meta": {
                    "version": 2,
                    "type": 1
                },
                "operations": [
                    {
                        "operationType": "modifyElement",
                        "data": {
                            "id": osmfullid,
                            "operations": [                                 # This is the section where the actual work is done
                                {                                           # Read the Maproutte documentation for more information
                                    "operation": "setTags",                 # Make sure to modify this section to fit your needs
                                    "data": {
                                        "ref:IFOPT": dhid
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
    # Expand the features section to include geometry in the area
    # get the lon and lat of the element, for a node its easy, but for a way, we just take the first node as a source of lon and lat
    # check if ... [coordinates][0] is a float, if yes, then it is a node, if not, then it is a way
    if isinstance(data["features"][0]["geometry"]["coordinates"][0], float):
        lon = data["features"][0]["geometry"]["coordinates"][0]
        lat = data["features"][0]["geometry"]["coordinates"][1]
    else:
        lon = data["features"][0]["geometry"]["coordinates"][0][0]
        lat = data["features"][0]["geometry"]["coordinates"][0][1]
    nearby_platform_features = gea.get_elements_around((lat, lon), {"public_transport": "platform", "highway": "bus_stop", "railway": "platform"}, 0.001)
    for feature in nearby_platform_features:
        # If the feature is a node, check if there is any other node with the same coordinates (when coordinates are truncated to 4 decimal places)
        # Only add the feature if there is NOT another node with the same coordinates
        if feature["geometry"]["type"] == "Point":
            # iterate over all features in the list, and if a feature is a point, check if it has the same coordinates (truncated to 4 decimal places)
            # if it does, then skip this feature
            skip = False
            for f in data["features"]:
                if f["geometry"]["type"] == "Point":
                    if round(f["geometry"]["coordinates"][0], 4) == round(feature["geometry"]["coordinates"][0], 4) and round(f["geometry"]["coordinates"][1], 4) == round(feature["geometry"]["coordinates"][1], 4):
                        skip = True
                        break
            if skip:
                continue
        data["features"].append(feature)
    TASKS.append(data)
    # Now, dump the task to a geojson file
    with open('tasks.json', 'w', encoding="UTF-8") as f:
        for task in TASKS:
            f.write('\x1E')
            f.write(json.dumps(task, ensure_ascii=False))
            f.write('\n')

