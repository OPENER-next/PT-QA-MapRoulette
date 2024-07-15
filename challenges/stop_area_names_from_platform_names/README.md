# Add names to stop_areas by platform names

This script gets all stop_areas without names from the overpass API. In the query, a virtual OSM object is constructed with a "combined name" of all platforms of this stop_area. If they are different, the `name=`-tag of this new object will read `< multiple values found >`, and it will not be considered. If they are all the name, this name is written to the `name=`-tag and suggested to be added as the name for the whole stop_area.

## Maproulette Challenge Description

```
In dieser Challenge bearbeitest du Haltestellenrelationen, die keinen Namen haben. Alle Steige in dieser Relation (oder zumindest alle, die einen Namen haben), haben den gleichen Namen. Deswegen ist mit hoher Wahrscheinlichkeit davon auszugehen, dass die Haltestelle als ganzes auch so heißt. Wenn der Name sinnvoll erscheint, drücke auf "Yes", um ihn der Haltestellenrelation hinzuzufügen.

```



## Maproulette Task Instruction

```
Das ist der Mittelpunkt einer Haltestellenrelation. Sie hat selber noch keinen Namen. Alle Steige in dieser Relation (oder zumindest alle, die einen Namen haben), haben den gleichen Namen. Deswegen ist mit hoher Wahrscheinlichkeit davon auszugehen, dass die Haltestelle als ganzes auch so heißt. Wenn der Name sinnvoll erscheint, drücke auf "Yes", um ihn der Haltestellenrelation hinzuzufügen.

```

