import os, sys, json, requests, copy

class MRChallengeBuilder:
    # Functionality:
    # - Get data from an overpass query as JSON
    def __init__(self):
        self.tasks = []
        self.overpass_url = "http://overpass-api.de/api/interpreter"
        self.overpass_data = None
        self.cooperativeWorkBase = {
            "meta": {
                "version": 2,
                "type": 1
            },
            "operations": []
        }

    def get_overpass_elements_json(self, overpass_query):
        response = requests.get(self.overpass_url, params={'data': overpass_query})
        if response.status_code != 200:
            return False
        self.overpass_data = response.json()["elements"]
        return True

    def create_element_centers(self):
        # Force every element in overpass data to have a lat/lon value
        # This provides us with _some_ coordinates we can use to put a marker in about the right position
        if self.overpass_data is None or len(self.overpass_data) == 0:
            return False
        for element in self.overpass_data:
            if 'lat' in element:
                element['lat'] = element['lat'] # That's a bit redundant, but it's here for clarity
                element['lon'] = element['lon']
            elif 'center' in element:
                element['lat'] = element['center']['lat']
                element['lon'] = element['center']['lon']
            elif 'bounds' in element:
                element['lat'] = (element['bounds']['minlat'] + element['bounds']['maxlat']) / 2
                element['lon'] = (element['bounds']['minlon'] + element['bounds']['maxlon']) / 2
            else:
                print("No coordinates found for element")
                raise ValueError("No handalable coordinates found for element")

    def create_task(self, taskgeometry, osmtype, osmid, additionalgeometry = [], cooperativeWork = False):
        # first, check if the taskgeometry is a point or a line
        # taskbeometry is either a dict of lat and lon or a list of dicts of lat and lon OR it is a list of tweo floats, then its a point, and if its a list of lists of two floats, then its a line
        # if its a point, the format "geometry": {"type": "Point", "coordinates": [13.6414144, 51.08160959923558]} is used
        # if its a line, the format "geometry": {"type": "LineString", "coordinates": [[13.6414144, 51.08160959923558], [13.6414144, 51.08160959923558]]} is used

        taskgeometrytype = None
        # Reformat the geometry in the format for geojson, so either a list of two floats or a list of lists of two floats
        if isinstance(taskgeometry, dict):
            taskgeometrytype = "Point"
            taskgeometry = [taskgeometry['lon'], taskgeometry['lat']]
        elif isinstance(taskgeometry[0], dict):
            taskgeometrytype = "Point"
            taskgeometry = [taskgeometry[0]['lon'], taskgeometry[0]['lat']]
        elif isinstance(taskgeometry[0], list):
            taskgeometrytype = "LineString"
            taskgeometry = [[point['lon'], point['lat']] for point in taskgeometry]
        elif isinstance(taskgeometry[0], float) and len(taskgeometry) == 2:
            taskgeometrytype = "Point"
            # Taskgeometry is already in the right format
        else:
            print(taskgeometry)
            raise ValueError("Taskgeometry is not in a handalable format")

        # Create the feature for the task (there may be more features in this task, but the "task feature" is the one that contains the osm id)
        
        taskFeature = {
            "type": "Feature",
            "geometry": {
                "type": taskgeometrytype,
                "coordinates": taskgeometry
            },
            "properties": {
                "@id": f"{osmtype}/{osmid}"
            }
        }

        cooperativeWorkDict = None
        if cooperativeWork:
            cooperativeWorkDict = copy.deepcopy(self.cooperativeWorkBase)

        # For every element of the list additionalgeometry, create a feature and add it to the task
        # we'll implement this later
        for geometry in additionalgeometry:
            pass

        allTaskFeatures = [taskFeature]
        # return the task, as we might want to modify it before adding it to the tasks list
        if cooperativeWork:
            return {
                "type": "FeatureCollection",
                "features": allTaskFeatures,
                "cooperativeWork": cooperativeWorkDict
            }
        else:
            return {
                "type": "FeatureCollection",
                "features": allTaskFeatures
            }

    def add_task(self, task):
        self.tasks.append(task)

    def set_edit_operation_for_task(self, taskDict, combinedOSMid, keysToDelete = [], tagsToSet = {}):
        # taskDict - the task dictionary that we got when we ran create_task
        # combinedOSMid - the osm element in the format "type/id" that we want to modify
        # tagsToDelete - a list of keys that we want to delete from the element (e.g. ["name", "operator"])
        # tagsToSet - a dictionary of key-value pairs that we want to set on the element (e.g. {"name": "Berlin Hauptbahnhof", "operator": "Deutsche Bahn"})
        # -------------------------------
        # This creates the operations list that will be added to the cooperativeWork section of the task and returns the new taskDict
        # The operations list can only be at most 2 elements long, since all setTags operations are combined into one operation and all deleteTags operations are combined into one operation
        # example: "operations": [{"operationType": "modifyElement", "data": {"id": "way/343089181", "operations": [{"operation": "setTags", "data": {"ref:IFOPT": "de:14612:342:1:1"}}]}}]}}
        # Check if we have tagsToSet
        NestedOperations = [] # the secondary operations list that will be added to the operations list
        if len(tagsToSet) > 0:
            NestedOperations.append({
                "operation": "setTags",
                "data": tagsToSet
            })
        # Check if we have keysToDelete
        if len(keysToDelete) > 0:
            NestedOperations.append({
                "operation": "unsetTags",
                "data": keysToDelete
            })
        # Create the top operations list
        TopOperationsList = [{
            "operationType": "modifyElement",
            "data": {
                "id": combinedOSMid,
                "operations": NestedOperations
            }
        }]
        # Take the task dict, set the operations list in it to our TopOperationsList and return the modified task dict
        taskDict["cooperativeWork"]["operations"] = TopOperationsList
        return taskDict

    def set_main_feature_properties_for_task(self, taskDict, propertiesDict):
        # taskDict - the task dictionary that we got when we ran create_task
        # propertiesDict - a dictionary of key-value pairs that we want to set on the main feature of the task (the one that contains the osm id) - used for styling elements
        # -------------------------------
        # This expands the properties of the main feature of the task and returns the new taskDict (keep properties that are already there)        
        for key, value in propertiesDict.items():
            taskDict["features"][0]["properties"][key] = value
        return taskDict

    def set_additional_feature_properties_for_task(self, taskDict, featureIndex, propertiesDict):
        pass


    def save_tasks_to_file(self, filename="tasks.json"):
        with open(filename, 'w', encoding="UTF-8") as f:
            for task in self.tasks:
                f.write('\x1E')
                json.dump(task, f, ensure_ascii=False)
                f.write('\n')



        