# PT-QA-MapRoulette
Public transport quality assurance callenges for MapRoulette

## Current challenges

- `large-stop_area-bbox` - Checks the bbox size of all stop_area relations in a certain area and creates tasks to check on those that surpass a certain threhhold value
- `stop_area-names-from-platform-names` - Creates a TagFix-Challenge json-File that proposes to add a name=-Tag to stop_area-Relations where all platforms have the same name
