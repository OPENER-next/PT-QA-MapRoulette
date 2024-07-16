import os, sys, json
from dataclasses import dataclass, field
from typing import List, Dict
import requests
import geojson
from turfpy.measurement import distance, bbox, centroid

@dataclass
class Geometry:
    def __init__(self, type, coordinates):
        self.type = type
        self.coordinates = coordinates

    @classmethod
    def fromOverpassElement(cls, element, GeomType=None):
        if GeomType is None:
            if 'lat' in element or 'center' in element:
                GeomType = "Point"
            elif 'bounds' in element:
                GeomType = "Polygon"
            elif 'geometry' in element:
                GeomType = element['geometry']['type']
            else:
                raise ValueError("No handalable coordinates found for element")

        if GeomType == "Point":
            if 'geometry' in element:
                return cls(GeomType, element['geometry']['coordinates'])
            elif 'center' in element:
                return cls(GeomType, [element['center']['lon'], element['center']['lat']])
            else:
                return cls(GeomType, [element['lon'], element['lat']])
        elif GeomType == "LineString":
            return cls(GeomType, [[point['lon'], point['lat']] for point in element['geometry']])
        elif GeomType == "Polygon":
            if 'bounds' in element:
                return cls(GeomType, [
                    [[element['bounds']['minlon'], element['bounds']['minlat']],
                     [element['bounds']['minlon'], element['bounds']['maxlat']],
                     [element['bounds']['maxlon'], element['bounds']['maxlat']],
                     [element['bounds']['maxlon'], element['bounds']['minlat']],
                     [element['bounds']['minlon'], element['bounds']['minlat']]]
                ])
            else:
                return cls(GeomType, [[[point['lon'], point['lat']] for point in element['geometry']]])

    def toGeoJSON(self):
        if self.type == "Point":
            return geojson.Point(self.coordinates)
        elif self.type == "LineString":
            return geojson.LineString(self.coordinates)
        elif self.type == "Polygon":
            return geojson.Polygon(self.coordinates)

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
        else:
            geojson_obj = self.toGeoJSON()
            center = centroid(geojson_obj)
            return center['geometry']['coordinates']

@dataclass
class GeoFeature:
    def __init__(self, geometry, properties={}):
        self.geometry = geometry
        self.properties = properties
        if not isinstance(geometry, Geometry):
            raise ValueError("geometry must be an instance of the Geometry class, got " + str(type(geometry)) + " instead")

    @classmethod
    def withId(cls, osmType, osmId, geometry, properties):
        properties["@id"] = f"{osmType}/{osmId}"
        return cls(geometry, properties)

    def toGeoJSON(self):
        return geojson.Feature(geometry=self.geometry.toGeoJSON(), properties=self.properties)

@dataclass
class TagFix():
    def __init__(self, osmType, osmId, tags):
        self.osmType = osmType
        self.osmId = osmId
        self.tagsToDelete = [key for key, value in tags.items() if value is None]
        self.tagsToSet = {key: value for key, value in tags.items() if value is not None}
        if not isinstance(self.tagsToDelete, list):
            raise ValueError("tagsToDelete must be a list, e.g. ['tag1', 'tag2']")
        if not isinstance(self.tagsToSet, dict):
            raise ValueError("tagsToSet must be a dict e.g. {'tag1': 'value1', 'tag2': 'value2'}")
        
    def toGeoJSON(self):
        return {"meta": {"version": 2, "type": 1}, 
                "operations": [
                    {"operationType": "modifyElement", 
                     "data": {
                         "id": f"{self.osmType}/{self.osmId}",  
                         "operations": [
                             {"operation": "setTags", "data": self.tagsToSet},
                             {"operation": "unsetTags", "data": self.tagsToDelete}
                         ]
                     }
                    }
                ]
                }

@dataclass
class Task:
    def __init__(self, mainFeature, additionalFeatures=[], cooperativeWork=None):
        self.mainFeature = mainFeature
        self.additionalFeatures = additionalFeatures
        self.cooperativeWork = cooperativeWork

    def toGeoJSON(self):
        features = [self.mainFeature.toGeoJSON()] + [f.toGeoJSON() for f in self.additionalFeatures]
        return geojson.FeatureCollection(features, **({"cooperativeWork": self.cooperativeWork.toGeoJSON()} if self.cooperativeWork else {}))

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
    def __init__(self, overpass_url="https://overpass-api.de/api/interpreter"):
        self.overpass_url = overpass_url

    def queryElements(self, overpass_query):
        response = requests.get(self.overpass_url, params={'data': overpass_query})
        if response.status_code != 200:
            raise ValueError("Invalid return data")
        return response.json()["elements"]