import os, sys, json
from dataclasses import dataclass, field
from typing import List, Dict
import requests

@dataclass
class Geometry:
    # This is an abstraction of a GeoJSON Geometry
    # A geometry is a dict with a type and coordinates
    # The type is a string and the coordinates are a list of lists of numbers
    def __init__(self, type, coordinates):
        self.type = type
        self.coordinates = coordinates

    # A method that will take an overpass result element and extract the geometry from it depending on what kind of data it is
    # The type of the geometry can be given in the arguments, but will default be inferred from the coordinates
    # This element can be a lot of different things...
    @classmethod
    def fromOverpassElement(cls, element, GeomType = None):
        if GeomType == None:
            if 'lat' in element:
                GeomType = "Point"
            elif 'center' in element:
                GeomType = "Point"
            elif 'bounds' in element:
                if GeomType == None:
                    GeomType = "Polygon"
            elif 'geometry' in element:
                if element['geometry']['type'] == 'Point':
                    GeomType = "Point"
                elif element['geometry']['type'] == 'LineString':
                    GeomType = "LineString"
                elif element['geometry']['type'] == 'Polygon':
                    GeomType = "Polygon"
            else:
                raise ValueError("No handalable coordinates found for element")
        

        if GeomType == "Point":
            if 'geometry' in element:
                return cls(GeomType, element['geometry']['coordinates'])
            if 'center' in element:
                return cls(GeomType, [element['center']['lon'], element['center']['lat']])
            else:
                return cls(GeomType, [element['lon'], element['lat']])
        elif 'bounds' in element:
            # The geometry that needs to be initialized changes depending on if the user specifically requested a certain format
            # A LineString is a list of lists of 2 numbers
            # A Polygon is a list with one element: a list of lists of 2 numbers
            if GeomType == "LineString":
                return cls(GeomType, [
                    [element['bounds']['minlon'], element['bounds']['minlat']],
                    [element['bounds']['minlon'], element['bounds']['maxlat']],
                    [element['bounds']['maxlon'], element['bounds']['maxlat']],
                    [element['bounds']['maxlon'], element['bounds']['minlat']],
                    [element['bounds']['minlon'], element['bounds']['minlat']]
                ])
            elif GeomType == "Polygon":
                return cls(GeomType, [
                    [[element['bounds']['minlon'], element['bounds']['minlat']],
                    [element['bounds']['minlon'], element['bounds']['maxlat']],
                    [element['bounds']['maxlon'], element['bounds']['maxlat']],
                    [element['bounds']['maxlon'], element['bounds']['minlat']],
                    [element['bounds']['minlon'], element['bounds']['minlat']]]
                ])
        elif GeomType == "LineString":
            return cls(GeomType, [[point['lon'], point['lat']] for point in element['geometry']])
        elif GeomType == "Polygon":
            return cls(GeomType, [[[point['lon'], point['lat']] for point in element['geometry']]])
        
    def toGeoJSON(self):
        return {
            "type": self.type,
            "coordinates": self.coordinates
        }

    def convertPolygonToClosedString(self):
        if self.type != "Polygon":
            raise ValueError("This function only works for Polygons")
        self.type = "LineString"
        self.coordinates = self.coordinates[0]

    def convertClosedStringToPolygon(self):
        if self.type != "LineString":
            raise ValueError("This function only works for LineStrings")
        self.type = "Polygon"
        self.coordinates = [self.coordinates]

    def getCenterPoint(self):
        if self.type == "Point":
            return self.coordinates
        elif self.type == "LineString":
            # Create a center point as an average of all points
            lat = 0
            lon = 0
            for point in self.coordinates:
                lat += point[1]
                lon += point[0]
            return [lon / len(self.coordinates), lat / len(self.coordinates)]
        elif self.type == "Polygon":
            # Create a center point as an average of all points
            lat = 0
            lon = 0
            for point in self.coordinates[0]:
                lat += point[1]
                lon += point[0]
            return [lon / len(self.coordinates[0]), lat / len(self.coordinates[0])]

@dataclass
class GeoFeature:
    # This is an abstraction of a GeoJSON Feature
    # A geo feature is a feature that has a geometry and properties
    # The geometry is a dict with a type and coordinates
    # The properties is a dict with key-value pairs
    def __init__(self, geometry, properties = {}):
        self.geometry = geometry
        self.properties = properties
        # infer the type of the geometry (Point, LineString, Polygon) from the coordinates
        # if its just a list of 2 numbers, its a Point
        # if its a list of lists of 2 numbers, its a LineString
        # if its a list of lists of 2 numbers where start and end are the same, its a Polygon
        if not isinstance(geometry, Geometry):
            raise ValueError("geometry must be an instance of the Geometry class, got " + str(type(geometry)) + " instead")


    @classmethod
    def withId(cls, osmType, osmId, geometry, properties):
        print(osmType, osmId, geometry, properties)
        properties["@id"] = str(osmType) + "/" + str(osmId)
        return cls(geometry, properties)

    def toGeoJSON(self):
        return {
            "type": "Feature",
            "geometry": self.geometry.toGeoJSON(),
            "properties": self.properties
        }

    def convertPolygonToClosedString(self):
        if self.geometryType != "Polygon":
            raise ValueError("This function only works for Polygons")
        self.geometryType = "LineString"
        self.geometry = self.geometry[0]

    def convertClosedStringToPolygon(self):
        if self.geometryType != "LineString":
            raise ValueError("This function only works for LineStrings")
        self.geometryType = "Polygon"
        self.geometry = [self.geometry]

@dataclass
class TagFix():
    def __init__(self, osmType, osmId, tags):
        # give tags to set and to delete in this format: {"name": "suggested name", "wrongtag": null}
        self.osmType = osmType
        self.osmId = osmId
        self.tagsToDelete = [key for key, value in tags.items() if value == None]
        self.tagsToSet = {key: value for key, value in tags.items() if value != None}
        if not isinstance(self.tagsToDelete, list):
            raise ValueError("tagsToDelete must be a list, e.g. ['tag1', 'tag2']")
        if not isinstance(self.tagsToSet, dict):
            raise ValueError("tagsToSet must be a dict e.g. {'tag1': 'value1', 'tag2': 'value2'}")
        
    def toGeoJSON(self):
        return {"meta": 
            {"version": 2, "type": 1}, 
            "operations": [
                {"operationType": "modifyElement", 
                "data": {
                    "id": str(self.osmType) + "/" + str(self.osmId),  
                    "operations": [
                        {
                            "operation": "setTags", 
                            "data": self.tagsToSet
                        },
                        {
                            "operation": "unsetTags",
                            "data": self.tagsToDelete
                        }
                    ]
                }}]}

@dataclass
class Task:
    def __init__(self, mainFeature, additionalFeatures = [], cooperativeWork = None):
        self.mainFeature = mainFeature
        self.additionalFeatures = additionalFeatures
        self.cooperativeWork = cooperativeWork

    def toGeoJSON(self):
        # the features are the main feature and the additional features as one list
        features = [
            self.mainFeature.toGeoJSON(),
            *map(lambda f: f.toGeoJSON(), self.additionalFeatures)
            ]
        return {
            "type": "FeatureCollection",
            "features": features,
            **({"cooperativeWork": self.cooperativeWork.toGeoJSON()} if self.cooperativeWork != None else {})
        }

@dataclass
class Challenge:
    def __init__(self):
        self.tasks = []

    def addTask(self, task):
        self.tasks.append(task)

    def saveToFile(self, filename):
        with open(filename, 'w', encoding="UTF-8") as f:
            for task in self.tasks:
                f.write('\x1E')
                json.dump(task.toGeoJSON(), f, ensure_ascii=False)
                f.write('\n')

class Overpass:
    def __init__(self, overpass_url = "https://overpass-api.de/api/interpreter"):
        self.overpass_url = overpass_url

    def getElementsFromQuery(self, overpass_query):
        response = requests.get(self.overpass_url, params={'data': overpass_query})
        if response.status_code != 200:
            raise ValueError("Invalid return data")
        resultElements = response.json()["elements"]
        return resultElements


def createElementCenterPoint(element):
    # This function forces the element to have a lat and lon key
    # so that, regardless of the type of geometry of the element, the script can use lat/lon
    if 'lat' in element:
        element['lat'] = element['lat'] # That's a bit redundant, but it's here for clarity
        element['lon'] = element['lon']
    elif 'center' in element:
        element['lat'] = element['center']['lat']
        element['lon'] = element['center']['lon']
    elif 'bounds' in element:
        element['lat'] = (element['bounds']['minlat'] + element['bounds']['maxlat']) / 2
        element['lon'] = (element['bounds']['minlon'] + element['bounds']['maxlon']) / 2
    elif 'geometry' in element:
        if element['geometry']['type'] == 'Point':
            element['lat'] = element['geometry']['coordinates'][1]
            element['lon'] = element['geometry']['coordinates'][0]
        elif element['geometry']['type'] == 'LineString':
            # Create a center point as an average of all points
            lat = 0
            lon = 0
            for point in element['geometry']['coordinates']:
                lat += point[1]
                lon += point[0]
            element['lat'] = lat / len(element['geometry']['coordinates'])
            element['lon'] = lon / len(element['geometry']['coordinates'])
        elif element['geometry']['type'] == 'Polygon':
            # Create a center point as an average of all points
            lat = 0
            lon = 0
            for point in element['geometry']['coordinates']:
                lat += point[1]
                lon += point[0]
            element['lat'] = lat / len(element['geometry']['coordinates'])
            element['lon'] = lon / len(element['geometry']['coordinates'])
    else:
        print(element)
        raise ValueError("No handalable coordinates found for element")
    return element

def createGeometryFromElement(element):
    # "geometry" needs to check before "bounds", because when you output geom, bbox will also be given back
    # if there is "bounds" in element, construct a polygon with 4 points that represents the bbox
    if "lat" in element:
        # list of 2 floats for a dict that has lat lon as keys
        element["simpleGeometry"] = [element["lon"], element["lat"]]
    elif "geometry" in element and "coordinates" in element["geometry"]:
        # list of lists of 2 floats for a dict that has lat lon as keys
        element["simpleGeometry"] = element["geometry"]["coordinates"]
    elif "geometry" in element:
        # list of lists of 2 floats for a dict that has lat lon as keys
        element["simpleGeometry"] = [[point["lon"], point["lat"]] for point in element["geometry"]]
    elif "bounds" in element:
        element["simpleGeometry"] = [
            [element["bounds"]["minlon"], element["bounds"]["minlat"]],
            [element["bounds"]["minlon"], element["bounds"]["maxlat"]],
            [element["bounds"]["maxlon"], element["bounds"]["maxlat"]],
            [element["bounds"]["maxlon"], element["bounds"]["minlat"]],
            [element["bounds"]["minlon"], element["bounds"]["minlat"]]
        ]	
    else:
        print(element)
        raise ValueError("No handalable geometry found for element")
    return element

def getElementCenterPoint(element):
    newElement = createElementCenterPoint(element)
    return [newElement["lon"], newElement["lat"]]

def getElementGeometry(element):
    newElement = createGeometryFromElement(element)
    return newElement["simpleGeometry"]