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
        # fix or raise errors for common geometry problems
        if not isinstance(geometry, geojson.geometry.Geometry):
            raise ValueError("geometry must be an instance of the geoJSON Geometry class, got " + str(type(geometry)) + " instead")
        if geometry.type == "Point" and len(geometry.coordinates) != 2:
            geometry.coordinates = centroid(geometry).coordinates
        if geometry.type == "LineString" and len(geometry.coordinates) < 2:
            raise ValueError("LineString must have at least 2 points")
        if geometry.type == "Polygon" and len(geometry.coordinates) != 1:
            geometry.coordinates = [geometry.coordinates]
        if geometry.type == "Polygon" and len(geometry.coordinates[0]) < 4:
            raise ValueError("Polygon must have at least 4 points")

    @classmethod
    def withId(cls, osmType, osmId, geometry, properties):
        properties["@id"] = f"{osmType}/{osmId}"
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

    def queryElementsAsGeoJSON(self, overpass_query):
        rawElements = self.queryElementsRaw(overpass_query)
        featureList = list(map(lambda element: geojson.Feature(
            geometry=self.geoJSONGeometryFromOverpassElement(element),
            properties=self.geoJSONPropertiesFromOverpassElement(element)
        ), rawElements))
        return featureList


    def geoJSONPropertiesFromOverpassElement(self, element):
        tags = element.get('tags', {})
        tags["@type"] = element["type"]
        tags["@id"] = element["id"]
        return tags;

    def geoJSONGeometryFromOverpassElement(self, element):
        # returns a geojson depending on element; either Point(), LineString() or Polygon()
        if 'lat' in element or 'center' in element:
            geomType = "Point"
        elif 'geometry' in element:
            if element['geometry']['type'] in ["Point", "LineString", "Polygon"]:
                geomType = element['geometry']['type']
            else:
                raise ValueError("No handalable coordinates found for element")
        else:
            raise ValueError("No handalable coordinates found for element")

        # now, create the geojson object
        if geomType == "Point":
            if 'geometry' in element:
                return geojson.Point(element['geometry']['coordinates'])
            elif 'center' in element:
                return geojson.Point([element['center']['lon'], element['center']['lat']])
            else:
                return geojson.Point([element['lon'], element['lat']])
        elif geomType == "LineString":
            if 'coordinates' in element['geometry']:
                return geojson.LineString(element['geometry']['coordinates'])
            else:
                return geojson.LineString([[point['lon'], point['lat']] for point in element['geometry']])
        elif geomType == "Polygon":
            if 'coordinates' in element['geometry']:
                if len(element['geometry']['coordinates']) == 1:
                    return geojson.Polygon(element['geometry']['coordinates'])
                else:
                    return geojson.Polygon([element['geometry']['coordinates']])
            else:
                return geojson.Polygon([[[point['lon'], point['lat']] for point in element['geometry']]])
        raise ValueError("No handalable coordinates found for element")
