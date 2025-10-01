# OSM2GPKG
To convert osm files to gpkg for easy processing, only using needed earth features.
This is based on information from openstreetmap.org
Visit the website for more information

## Installation
### pip install osmnx geopandas shapely pyproj matplotlib pandas
install any other library that pops up as error


## Required Files
You need to download two files which are the OSM coastline products.
- Land polygons: global polygons for all land (continents + islands) https://osmdata.openstreetmap.de/data/land-polygons.html
    Extract the file and place the path to 'land_polygons.shp' in 'LAND_SHP' in osm2gpkg.py
- Water polygons (optional): global polygons for oceans/seas https://osmdata.openstreetmap.de/data/water-polygons.html
    Extract the file and place the path to 'water_polygons.shp' in 'WATER_SHP' in osm2gpkg.py
(Both are hosted at OSM’s official data mirror: osmdata.openstreetmap.de.)

## Mapped Area 
Go to the area you would like to convert to gpkg at https://www.openstreetmap.org/export
You can manually select an area, but bear it in mind that OSM has limited nodes, so you cannot select a large area with so many features. You may need to zoom in for that.

The export button pops up as soon as you can download the features. Download the map and put the path reference to OSM_XML in osm2gpkg.py
There are more features than included in this project, but the current features implemented are:
- coastline
- water
- roads 
- waterways

## Running
Run the osm2gpkg.py file and that generates the gpkg file in file/basemap.gpkg and a figure of the mapped area in figures/map_fit.png

## Reading GPKG 
Run readgpkg.py to read the same file in file/basemap.gpkg and plot it without having to iterate through the land and water polygons anymore. This can be a layer on which you can build your project that requires plotting on earth geographical features.
You can read from the gpkg file in different format, as we have saved from the converter file. Options are:
- frame_wgs84
- frame_3857 
- frame_utm