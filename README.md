# PT-QA-MapRoulette
Public transport quality assurance callenges for MapRoulette

## Current challenges

- `large-stop_area-bbox` - Checks the bbox size of all stop_area relations in a certain area and creates tasks to check on those that surpass a certain threshold value
- `stop_area-names-from-platform-names` - Creates a TagFix-Challenge json-File that proposes to add a name=-Tag to stop_area-Relations where all platforms have the same name

## How to use the output of the scripts / this repository

A GitHub Action executes the scripts and creates a release with the output files. You can download the files from the [releases page](https://github.com/wielandb/PT-QA-MapRoulette/releases).

[![Release with JSON Artifacts](https://github.com/wielandb/PT-QA-MapRoulette/actions/workflows/release.yml/badge.svg)](https://github.com/wielandb/PT-QA-MapRoulette/actions/workflows/release.yml)

For usage with MapRoulette, it is recommended that you use the static url that will always point to the latest release.
Theese URLs are currently:
- https://github.com/wielandb/PT-QA-MapRoulette/releases/latest/download/large_stop_area_bbox.json
- https://github.com/wielandb/PT-QA-MapRoulette/releases/latest/download/stop_area_names_from_platform_names.json