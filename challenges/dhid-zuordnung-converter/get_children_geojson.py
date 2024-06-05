import requests
import json
import xmltodict


def get_children_geojson(osm_id):
    url = f"https://api.openstreetmap.org/api/0.6/relation/{osm_id}/full"
    response = requests.get(url)
    data = response.content.decode("utf-8")
    geojson = {"type": "FeatureCollection", "features": []}

    # Parse the XML response and extract node and way children
    # Convert them to GeoJSON features and add them to the feature collection
    # You may need to install the `xmltodict` library for this to work
    """
    Example dictionary:
    {'osm': {'@version': '0.6', '@generator': 'CGImap 0.9.2 (3405214 spike-07.openstreetmap.org)', '@copyright': 'OpenStreetMap and contributors', '@attribution': 'http://www.openstreetmap.org/copyright', '@license': 'http://opendatacommons.org/licenses/odbl/1-0/', 'node': [{'@id': '4372055037', '@visible': 'true', '@version': '2', '@changeset': '49946866', 
    '@timestamp': '2017-06-30T15:31:51Z', '@user': 'SvenQ', '@uid': '559480', '@lat': '50.8156477', '@lon': '12.9236379'}, {'@id': '4372055038', '@visible': 'true', '@version': '2', 
    '@changeset': '49946866', '@timestamp': '2017-06-30T15:31:51Z', '@user': 'SvenQ', '@uid': '559480', '@lat': '50.8158259', '@lon': '12.9236603'}, {'@id': '4944211173', '@visible': 'true', '@version': '5', '@changeset': '60018252', '@timestamp': '2018-06-20T17:59:40Z', '@user': 'SvenQ', '@uid': '559480', '@lat': '50.8157424', '@lon': '12.9235447', 'tag': [{'@k': 'bus', '@v': 'yes'}, {'@k': 'highway', '@v': 'bus_stop'}, {'@k': 'name', '@v': 'Fraunhoferstraße Süd'}, {'@k': 'public_transport', '@v': 'stop_position'}, {'@k': 'ref_name', '@v': 'Fraunhoferstr.Süd, Chemnitz'}]}, {'@id': '4944211174', '@visible': 'true', '@version': '4', '@changeset': '60018252', '@timestamp': '2018-06-20T17:59:40Z', '@user': 'SvenQ', '@uid': '559480', '@lat': '50.8166563', '@lon': '12.9235711', 'tag': [{'@k': 'bus', '@v': 'yes'}, {'@k': 'highway', '@v': 'bus_stop'}, {'@k': 'name', '@v': 'Fraunhoferstraße Süd'}, {'@k': 'public_transport', '@v': 'stop_position'}, {'@k': 'ref_name', '@v': 'Fraunhoferstr.Süd, Chemnitz'}]}, {'@id': '4944211175', '@visible': 'true', '@version': '1', 
    '@changeset': '49946866', '@timestamp': '2017-06-30T15:31:50Z', '@user': 'SvenQ', '@uid': '559480', '@lat': '50.8167424', '@lon': '12.9234389'}, {'@id': '4944211176', '@visible': 'true', '@version': '1', '@changeset': '49946866', '@timestamp': '2017-06-30T15:31:50Z', '@user': 'SvenQ', '@uid': '559480', '@lat': '50.8165630', '@lon': '12.9234460'}], 'way': [{'@id': '439562400', '@visible': 'true', '@version': '6', '@changeset': '132940447', '@timestamp': '2023-02-23T19:25:01Z', '@user': 'wielandb-paid', '@uid': '18116609', 'nd': [{'@ref': '4372055037'}, {'@ref': '4372055038'}], 'tag': [{'@k': 'bench', '@v': 'no'}, {'@k': 'bin', '@v': 'yes'}, {'@k': 'highway', '@v': 'platform'}, {'@k': 'lit', '@v': 'yes'}, {'@k': 'public_transport', '@v': 'platform'}, {'@k': 'ref', '@v': 'Fraunhoferstraße Süd'}, {'@k': 'ref:IFOPT', '@v': 'de:14511:30350:0:BN'}, {'@k': 'shelter', '@v': 'yes'}, {'@k': 'tactile_paving', '@v': 'yes'}, {'@k': 'wheelchair', '@v': 'yes'}]}, {'@id': '504244349', '@visible': 'true', '@version': '5', '@changeset': '132940447', '@timestamp': '2023-02-23T19:25:01Z', '@user': 'wielandb-paid', '@uid': '18116609', 'nd': [{'@ref': '4944211175'}, {'@ref': '4944211176'}], 'tag': [{'@k': 'bench', '@v': 'no'}, {'@k': 'bin', '@v': 'yes'}, {'@k': 'check_date:shelter', '@v': '2023-01-05'}, {'@k': 'highway', '@v': 'platform'}, {'@k': 'lit', '@v': 'yes'}, {'@k': 'public_transport', '@v': 'platform'}, {'@k': 'ref', '@v': 'Fraunhoferstraße Süd'}, {'@k': 'ref:IFOPT', '@v': 'de:14511:30350:0:BS'}, {'@k': 'shelter', '@v': 'no'}, {'@k': 'tactile_paving', '@v': 'yes'}, {'@k': 'wheelchair', '@v': 'yes'}]}], 'relation': {'@id': '7366007', '@visible': 'true', '@version': '4', '@changeset': '132940447', '@timestamp': '2023-02-23T19:25:01Z', '@user': 'wielandb-paid', '@uid': '18116609', 'member': [{'@type': 'node', '@ref': '4944211173', '@role': 'stop'}, {'@type': 'way', '@ref': '439562400', '@role': 'platform'}, {'@type': 'node', '@ref': '4944211174', '@role': 'stop'}, {'@type': 'way', '@ref': '504244349', '@role': 'platform'}], 'tag': [{'@k': 'fare_zone', '@v': '13'}, {'@k': 'name', '@v': 'Fraunhoferstraße Süd'}, {'@k': 'network', '@v': 'Verkehrsverbund Mittelsachsen'}, {'@k': 'operator', '@v': 'Chemnitzer Verkehrs-AG'}, {'@k': 'public_transport', '@v': 'stop_area'}, {'@k': 'ref:IFOPT', '@v': 'de:14511:30350'}, {'@k': 'ref_name', '@v': 'Fraunhoferstr.Süd, Chemnitz'}, {'@k': 'type', '@v': 'public_transport'}]}}}
    So the elements "node" and "way" can either be a list of dictionarys or just one dictionary object.
    
    """

    xml_data = xmltodict.parse(data)
    print(xml_data)
    for element in xml_data["osm"]["node"]:
        # Add the node as a feature, but only if is not part of any way (<nd ref="{nodeId}"/> does not exist in the whole XML)
        if "<nd ref=\"" + element["@id"] + "\"/>" in data: # Der dreckige Hack funktioniert mal wieder, aber so wie mans eigentlich machen soll nicht :/
            continue
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(element["@lon"]), float(element["@lat"])]
            },
            "properties": {
                "id": element["@id"],
                "type": "node"
            }
        }
        geojson["features"].append(feature)
    # For ways, we need to fetch the way from the osm api to get the coordinates of the nodes that make up the way
    for element in xml_data["osm"]["way"]:
        way_id = element["@id"]
        way_url = f"https://api.openstreetmap.org/api/0.6/way/{way_id}/full"
        way_response = requests.get(way_url)
        way_data = way_response.content.decode("utf-8")
        way_xml_data = xmltodict.parse(way_data)
        nodes = way_xml_data["osm"]["way"]["nd"]
        coordinates = []
        for node in nodes:
            node_id = node["@ref"]
            node_url = f"https://api.openstreetmap.org/api/0.6/node/{node_id}"
            node_response = requests.get(node_url)
            node_data = node_response.content.decode("utf-8")
            node_xml_data = xmltodict.parse(node_data)
            coordinates.append([float(node_xml_data["osm"]["node"]["@lon"]), float(node_xml_data["osm"]["node"]["@lat"])])
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            },
            "properties": {
                "id": way_id,
                "type": "way"
            }
        }
        geojson["features"].append(feature)
    return geojson

# Example usage
osm_id = 7366007
geojson = get_children_geojson(osm_id)
print(json.dumps(geojson, indent=2))
