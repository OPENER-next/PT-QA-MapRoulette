import json
import urllib.parse
import requests

# Use this function to determine if a task needs to be created for a given element
# use this function for filtering things that overpass cannot filter, maybe by using a function from a different file that you specifically implemented for this task
# if your overpass query already returns all elements that need to be fixed, make this function return True
def needsTask(e):
    return True


TASKS = []

response = requests.get('ENTER_URL_OF_DIZY_EXPORT_HERE')
dizydata = response.text.split('\n')
# remove the last line, which is empty
dizydata.pop()
# iterate over all lines of data
for line in dizydata:
    # remove the first character of the line, which is a control character
    line = line[1:]
    # parse the line as json
    data = json.loads(line)
    # Get the necessary data from the json
    osmfullid = data["features"][0]["properties"]["@id"]
    ## Hack while the MR fix is not deployed - skip this task if the osmid contains relation
    if "relation" in osmfullid:
        continue
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
    TASKS.append(data)

# Now, dump the task to a geojson file

with open('tasks.json', 'w', encoding="UTF-8") as f:
    for task in TASKS:
        f.write('\x1E')
        f.write(json.dumps(task, ensure_ascii=False))
        f.write('\n')

