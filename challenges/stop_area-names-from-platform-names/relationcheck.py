import osmium

import requests

platform_names = set()

def fetch_relation_data(relation_id):
    result = requests.get(f"https://overpass-api.de/api/interpreter?data=relation%28" + str(relation_id) + "%29%3B%28._%3B%3E%3B%29%3Bout%3B")
    if result.status_code != 200:
        raise Exception("Failed to fetch relation data")
    return result.text

class RelationHandler(osmium.SimpleHandler):
    global platform_names
    def __init__(self, relation_id):
        super(RelationHandler, self).__init__()
        self.relation_id = relation_id
        self.platforms = []

    def way(self, w):
        print("Way", w.id, w.tags)
        if 'public_transport' in w.tags and w.tags['public_transport'] == 'platform' and 'name' in w.tags:
            print("Found platform", w.tags['name'])
            platform_names.add(w.tags['name'])
        elif 'highway' in w.tags and w.tags['highway'] == 'bus_stop' and 'name' in w.tags:
            platform_names.add(w.tags['name'])

    def node(self, n):
        print("Node", n.id, n.tags)
        if 'public_transport' in n.tags and n.tags['public_transport'] == 'platform' and 'name' in n.tags:
            platform_names.add(n.tags['name'])
        elif 'highway' in n.tags and n.tags['highway'] == 'bus_stop' and 'name' in n.tags:
            print("Found bus stop", n.tags['name'])
            platform_names.add(n.tags['name'])

def check_platform_names(relation_id, file_path):
    global platform_names
    handler = RelationHandler(relation_id)
    handler.apply_file(file_path)
    print(platform_names)
    if len(platform_names) == 0:
        platform_names = set()
        return None
    elif len(platform_names) == 1:
        return platform_names.pop()
    else:
        platform_names = set()
        return False


def check_relation_for_consistent_platform_names(rid):
    # Example usage:
    relation_id = rid
    # Get the relation sata and save it to data.osm
    data = fetch_relation_data(relation_id)
    with open("data.osm", "w", encoding="UTF-8") as f:
        f.write(data)
    result = check_platform_names(relation_id, "data.osm")
    if result is None:
        print("Ergebnis: Keine Platform hatte einen Namen, wir können nichts tun")
    elif result is False:
        print("Ergebnis: Die Platformen hatten unterschiedliche Namen")
    else:
        print("Ergebnis: Die Platformen hatten den gleichen Namen: " + result)
    if result is None:
        return False
    return result