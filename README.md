# PT-QA-MapRoulette
Public transport quality assurance callenges for MapRoulette

## Current challenges

- `add-platforms-to-stop_areas` (WIP) - Creates cooperative tasks to add platforms without stop_area-Relations to a nearby relation or create a relation and add all platforms to it
- `dhid-zuordnung-converter` - Takes a URL to a json-File that presents a regular MR challenge for adding ref:IFOPT to OSM and converts it into a TagFix-Challenge json-File
- `large-stop_area-bbox` (WIP) - Checks the bbox size of all stop_area relations in a certain area and creates tasks to check on those that surpass a certain threhhold value
- `stop_area-names-from-platform-names` - Creates a TagFix-Challenge json-File that proposes to add a name=-Tag to stop_area-Relations where all platforms have the same name
