import os, sys, json
from dataclasses import dataclass, field
from typing import List, Dict
import requests
import geojson
from turfpy.measurement import distance, bbox, centroid



@dataclass
class GeoFeature:
    def __init__(self, geometry, properties={}):
        self.geometry = geometry
        self.properties = properties
        if not isinstance(geometry, geojson.geometry.Geometry):
            raise ValueError("geometry must be an instance of the geoJSON Geometry class, got " + str(type(geometry)) + " instead")

    @classmethod
    def withId(cls, osmType, osmId, geometry, properties):
        properties["@id"] = f"{osmType}/{osmId}"
        # Fix polygons beeing not a 3-dimensional array
        if geometry["type"] == "Polygon" and len(geometry["coordinates"]) != 1:
            geometry["coordinates"] = [geometry["coordinates"]]
        return cls(geometry, properties)

    def toGeoJSON(self):
        return geojson.Feature(geometry=self.geometry, properties=self.properties)

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

    def queryElementsRaw(self, overpass_query):
        response = requests.get(self.overpass_url, params={'data': overpass_query})
        if response.status_code != 200:
            raise ValueError("Invalid return data")
        return response.json()["elements"]

    def queryElementsAsGeoJSON(self, overpass_query, forceGeomType=None):
        rawElements = self.queryElementsRaw(overpass_query)
        geometriesAndProperties = [(self.geoJSONGeometryFromOverpassElement(element, forceGeomType)) for element in rawElements]
        return [geojson.Feature(geometry=g, properties=p) for g,p in geometriesAndProperties]

    def geoJSONGeometryFromOverpassElement(self, element, forceGeomType=None):
        # returns a geojson depending on element; either Point(), LineString() or Polygon()
        # frist, asses the geometry type we want to give back based on the element if ForceGeomType is None
        if "tags" not in element:
            element["tags"] = {}
        element["tags"]["@type"] = element["type"]
        element["tags"]["@id"] = element["id"]
        thisElementProperties = element["tags"]
        if forceGeomType is None:
            if 'lat' in element or 'center' in element:
                geomType = "Point"
            elif 'bounds' in element:
                geomType = "Polygon"
            elif 'geometry' in element:
                if element['geometry']['type'] in ["Point", "LineString", "Polygon"]:
                    geomType = element['geometry']['type']
                else:
                    raise ValueError("No handalable coordinates found for element")
            else:
                raise ValueError("No handalable coordinates found for element")
        else:
            geomType = forceGeomType
        # now, create the geojson object
        if geomType == "Point":
            if 'geometry' in element:
                thisElementGeometry = geojson.Point(element['geometry']['coordinates'])
            elif 'center' in element:
                thisElementGeometry = geojson.Point([element['center']['lon'], element['center']['lat']])
            else:
                thisElementGeometry = geojson.Point([element['lon'], element['lat']])
        elif geomType == "LineString":
            thisElementGeometry = geojson.LineString([[point['lon'], point['lat']] for point in element['geometry']])
        elif geomType == "Polygon":
            if 'bounds' in element:
                print("bounds im Element")
                thisElementGeometry=geojson.Polygon([
                    [[element['bounds']['minlon'], element['bounds']['minlat']],
                    [element['bounds']['minlon'], element['bounds']['maxlat']],
                    [element['bounds']['maxlon'], element['bounds']['maxlat']],
                    [element['bounds']['maxlon'], element['bounds']['minlat']],
                    [element['bounds']['minlon'], element['bounds']['minlat']]]
                ])
            if 'coordinates' in element['geometry']:
                print("element: " + str(element))
                if len(element['geometry']['coordinates']) == 1:
                    print("Elementgeometrie length 1")
                    thisElementGeometry = geojson.Polygon([element['geometry']['coordinates']])
                print("Elementgeometrie length > 1")
                print("Übergebene geometrie: " + str([element['geometry']['coordinates']]))
                thisElementGeometry = geojson.Polygon([element['geometry']['coordinates']])
            else:
                print("Dictionarys mit lon und lat")
                thisElementGeometry=geojson.Polygon([[[point['lon'], point['lat']] for point in element['geometry']]])
        return (thisElementGeometry, thisElementProperties)