import requests
import xmltodict    
import json
from time import sleep
def get_elements_around(coordinates, keyvaluepairs, radius):
    base_url = "https://api.openstreetmap.org/api/0.6/map"
    lat, lon = coordinates
    # Keyvaluepairs is a dictionary with the key being the key and the value being the value like this: {"public_transport": "platform", "highway": "platform"}
    # Construct the query parameters
    params = {
        "bbox": f"{lon - radius},{lat - radius},{lon + radius},{lat + radius}"
    }

    # Send the GET request to the API
    success = False
    while not success:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            success = True
        else:
            print("An error occurred while fetching data from the API")
            print(response.text)
            print("Retrying in 60 seconds...")
            sleep(60)
            
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the XML response
        data = xmltodict.parse(response.content)

        # Extract the elements that match the given key and value
        geojson = {"type": "FeatureCollection", "features": []}
        # If node is a list, then it is a list of nodes, if it is a dictionary, then it is a single node. Convert it to a list if it is a dictionary
        if isinstance(data["osm"]["node"], dict):
            data["osm"]["node"] = [data["osm"]["node"]]
        for element in data["osm"]["node"]:         
            print(element)   
            # Add the node as a feature, but only if is not part of any way (<nd ref="{nodeId}"/> does not exist in the whole XML)
            #if "<nd ref=\"" + element["@id"] + "\"/>" in data: # Der dreckige Hack funktioniert mal wieder, aber so wie mans eigentlich machen soll nicht :/
            #    continue
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(element["@lon"]), float(element["@lat"])]
                },
                "properties": {
                    "marker-color": "#555555"
                }
            }
            # Append it, but only if
            # check if the element has at least one of the key value pairs
            has_key_and_value = False
            if "tag" in element:
                tags = element["tag"]
                if not isinstance(tags, list):
                    tags = [tags]
                for tag in tags:
                    for key, value in keyvaluepairs.items():
                        if tag["@k"] == key and tag["@v"] == value:
                            has_key_and_value = True
                            break
            print(element["tag"] if "tag" in element else "No tags")
            print(has_key_and_value)
            if has_key_and_value:
                geojson["features"].append(feature)
        # We do not need to fetch the ways from the API, as the API already returns the ways (and their nodes) in the data we received
        if isinstance(data["osm"]["way"], dict):
            data["osm"]["way"] = [data["osm"]["way"]]
        for element in data["osm"]["way"]:
            # Check if the way has the given key and value
            print(element)
            way_id = element["@id"]
            nodes = element["nd"]
            coordinates = []
            for node in nodes:
                node_id = node["@ref"]
                for node_element in data["osm"]["node"]:
                    if node_element["@id"] == node_id:
                        coordinates.append([float(node_element["@lon"]), float(node_element["@lat"])])
                        break
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coordinates
                },
                "properties": {
                    "marker-color": "#555555",
                    "fill":"#555555",
                    "stroke-width":"3",
                    "fill-opacity":0.6,
                    "stroke": "#555555"
                }
            }
            # Append it, but only if it has the given key and value
            # check if the element has at least one of the key value pairs
            has_key_and_value = False
            if "tag" in element:
                tags = element["tag"]
                if not isinstance(tags, list):
                    tags = [tags]
                for tag in tags:
                    for key, value in keyvaluepairs.items():
                        if tag["@k"] == key and tag["@v"] == value:
                            has_key_and_value = True
                            break
            print(element["tag"] if "tag" in element else "No tags")
            print(has_key_and_value)
            if has_key_and_value:
                geojson["features"].append(feature)
                 
        return geojson["features"]  

    else:
        # If the request was not successful, print an error message
        print("An error occurred while fetching data from the API")
        print(response.text)
