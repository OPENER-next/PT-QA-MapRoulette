import json
import urllib.parse
import requests

# Use this function to determine if a task needs to be created for a given element
# use this function for filtering things that overpass cannot filter, maybe by using a function from a different file that you specifically implemented for this task
# if your overpass query already returns all elements that need to be fixed, make this function return True
def needsTask(e):
    return True
## Helper functions

# For some currently unknown reason, sometimes special characters are mangled in the data
# we pass every string through that function to correct the problem if it appears
def correct_mangled_characters(input_string):
    mangled_to_correct = {
        'Ã¼': 'ü',
        'Ã¶': 'ö',
        'Ã¤': 'ä',
        'ÃŸ': 'ß',
        'Ã ': 'à',
        'Ã¡': 'á',
        'Ã¢': 'â',
        'Ã£': 'ã',
        'Ã©': 'é',
        'Ã¨': 'è',
        'Ãª': 'ê',
        'Ã«': 'ë',
        'Ã®': 'î',
        'Ã¯': 'ï',
        'Ã´': 'ô',
        'Ãµ': 'õ',
        'Ã¹': 'ù',
        'Ãº': 'ú',
        'Ã»': 'û',
        'Ã½': 'ý',
        'Ã¿': 'ÿ',
        'Ã–': 'Ö',
        'Ãœ': 'Ü',
        'Ã„': 'Ä',
        '채': 'ä',
        'Ã¶': 'ö'
    }
    corrected_string = input_string
    for mangled, correct in mangled_to_correct.items():
        corrected_string = re.sub(mangled, correct, corrected_string)
    return corrected_string

TASKS = []

# Get the Data that we want to work with from the Overpass API
# The script will assume (a.k.a. make sure that):
# - the data is in JSON format
# - out center is used, that for every way and relation a center is provided
overpass_query = """
[out:json][timeout:25];
area(id:3600051477)->.searchArea;
relation["public_transport"="stop_area"][!"name"](area.searchArea);
out ids center;
"""

# URL encode the query and get the Data from the overpass API
overpass_url = "http://overpass-api.de/api/interpreter"
response = requests.get(overpass_url, params={'data': overpass_query})
data = response.json()

# Iterate over the data
for element in data['elements']:
    # Do anything that needs to be done to the data in a algorithmic way here
    if value := needsTask(element):
        # Get lon and lat
        # if the element is a node, it has a 'lat' and 'lon' key
        # if the element is a way or a relation, it has a 'center' key with a 'lat' and 'lon' key
        print(element)
        if 'lat' in element:
            element['lat'] = element['lat']
            element['lon'] = element['lon']
        else:
            element['lat'] = element['center']['lat']
            element['lon'] = element['center']['lon']
        # Create a Task for the element
        task = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [element['lon'], element['lat']]
                    },
                    "properties": {
                        "@id": f"{element['type']}/{element['id']}", # You should provide at least one marker element that 
                        "latitude": element['lat'],                 # the user can see when they open the task
                        "longitude": element['lon'],
                        #"name": element.get('tags', {}).get('name', 'Unnamed')
                    }
                }
            ],
            "cooperativeWork": {
                "meta": {
                    "version": 2,
                    "type": 1
                },
                "operations": [
                    {
                        "operationType": "modifyElement",
                        "data": {
                            "id": f"{element['type']}/{element['id']}",
                            "operations": [                                 # This is the section where the actual work is done
                                {                                           # Read the Maproutte documentation for more information
                                    "operation": "setTags",                 # Make sure to modify this section to fit your needs
                                    "data": {
                                        "name": value
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
        TASKS.append(task)

# Now, dump the task to a geojson file

with open('tasks.json', 'w', encoding="UTF-8") as f:
    for task in TASKS:
        f.write('\x1E')
        json.dump(task, f, ensure_ascii=False)
        f.write('\n')

