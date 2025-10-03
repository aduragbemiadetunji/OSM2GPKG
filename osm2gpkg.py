# pip install osmnx geopandas shapely pyproj matplotlib pandas
import os, xml.etree.ElementTree as ET
import geopandas as gpd, pandas as pd, osmnx as ox
from shapely.ops import unary_union
from shapely.geometry import box
import matplotlib.pyplot as plt

OSM_XML   = "osmFiles/Helsingborg_Helsingor.osm"  # change this path to your new AOI .osm
LAND_SHP  = r"osmFiles/land-polygons-complete-4326/land-polygons-complete-4326/land_polygons.shp"
WATER_SHP = r"osmFiles/water-polygons-split-4326/water-polygons-split-4326/water_polygons.shp"  # optional

#directory to save the gpkg file
OUT_GPKG = "files/basemap.gpkg"

# --- (1) HARD-RESET THE OUTPUT GPKG ---
if os.path.exists(OUT_GPKG):
    os.remove(OUT_GPKG)

# Bounds from OSM → frame (WGS84)
b = ET.parse(OSM_XML).getroot().find("bounds")
minx, miny, maxx, maxy = map(float, (b.get("minlon"), b.get("minlat"), b.get("maxlon"), b.get("maxlat")))
frame_wgs84 = gpd.GeoDataFrame(geometry=[box(minx, miny, maxx, maxy)], crs="EPSG:4326")

# Land/Ocean mask
land = gpd.clip(gpd.read_file(LAND_SHP), frame_wgs84)
try:
    ocean = gpd.clip(gpd.read_file(WATER_SHP), frame_wgs84)
except Exception:
    land_u = unary_union(land.geometry) if not land.empty else None
    ocean = gpd.GeoDataFrame(
        geometry=[frame_wgs84.geometry.iloc[0].difference(land_u)] if land_u else [frame_wgs84.geometry.iloc[0]],
        crs="EPSG:4326"
    )

# Helper to pull OSM features
def feats(tags):
    try:
        g = ox.features_from_xml(OSM_XML, tags=tags)
    except Exception:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    if g is None or getattr(g, "empty", True):
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    if g.crs is None:
        g.set_crs("EPSG:4326", inplace=True)
    return g

#You can add more layers, read OpenStreetMap.org for more documentation
coast      = feats({"natural":"coastline"})
water_nat  = feats({"natural":"water"})
water_tag  = feats({"water":True})
water = (
    gpd.GeoDataFrame(
        pd.concat(
            [df[df.geometry.geom_type.isin(["Polygon","MultiPolygon"])]
             for df in (water_nat, water_tag) if not df.empty],
            ignore_index=True
        ),
        crs="EPSG:4326"
    )
    if (not water_nat.empty or not water_tag.empty)
    else gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
)
waterways  = feats({"waterway":True})
roads      = feats({"highway":True})

################################### More Features #######################

beaches = feats({"natural": ["beach", "sand", "dune"]})
wetlands = feats({"natural": "wetland"})  # then filter by wetland=tidalflat/saltmarsh in attributes
tidalflats = feats({"natural": "tidalflat"})  # if present

lock_gates = feats({"waterway": "lock_gate"})
weirs      = feats({"waterway": "weir"})
sluices    = feats({"waterway": "sluice"})
dams_mm    = feats({"man_made": "dam"})  # dams are usually man_made=dam

docks = feats({"waterway": "dock"})

harbours = feats({"harbour": True}) #Harbours
marinas = feats({"leisure": "marina"}) #Marinas

ferry_terms  = feats({"amenity": "ferry_terminal"}) #Ferry terminals
ferry_routes = feats({"route": "ferry"}) #ferry routes

marine_structures = feats({"man_made": ["pier", "breakwater", "groyne", "seawall", "jetty"]})#marine structures
slipways = feats({"leisure": "slipway"})#slipways
lighthouses = feats({"man_made": "lighthouse"})#lighthouses

#Aids to Navigation
seamarks_all = feats({"seamark:type": True})
buoys = feats({"seamark:type": ["buoy_lateral", "buoy_cardinal", "buoy_special_purpose", "buoy_safe_water", "buoy_isolated_danger"]})
beacons = feats({"seamark:type": ["beacon_lateral", "beacon_cardinal", "beacon_isolated_danger", "beacon_safe_water", "beacon_special_purpose"]})
lights  = feats({"seamark:type": ["light_minor", "light_major", "light_vessel"]})
tss = feats({"seamark:type": ["traffic_separation_scheme", "separation_zone", "separation_line", "roundabout", "precautionary_area"]})#traffic seperation and navigation areas
anchorages = feats({"seamark:type": "anchorage"})
moorings   = feats({"seamark:type": "mooring"})
restricted = feats({"seamark:type": ["restricted_area", "caution_area", "prohibited_area"]})
wrecks       = feats({"seamark:type": "wreck"})
obstructions = feats({"seamark:type": "obstruction"})
rocks_reefs  = feats({"seamark:type": ["rock", "rock_awash", "reef"]})
soundings = feats({"seamark:sounding": True})   # often accompanied by seamark:depth=*

#cables pipeline utilities
pipelines = feats({"man_made": "pipeline"})  # filter attributes: location=underwater / substance=oil/gas
sub_cables = feats({"seamark:type": "cable_submarine"})

#safety constraints
military = feats({"military": True})  # polygons/areas
protected = feats({"boundary": "protected_area"})
nature_res = feats({"leisure": "nature_reserve"})  # used in some places
access_no = feats({"access": ["no", "private"]})

#Named sea areas/bays/straits
seas = feats({"place": "sea"})
bays = feats({"natural": "bay"})
straits = feats({"natural": "strait"})

#Bridges/Tunnels over/under waterways for crossings
bridges = feats({"bridge": True})
tunnels = feats({"tunnel": True})

###########################################################################

# --- (2) SMALL SAVE HELPER (always overwrites since GPKG was reset) ---
def save_layer(gdf, name):
    # Always create the layer (even if empty) so nothing stale remains
    if gdf is None:
        gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    gdf.to_file(OUT_GPKG, layer=name, driver="GPKG")

# A) Save frame (WGS84)
save_layer(frame_wgs84, "frame_wgs84")

# B) Save WGS84 source layers (no extra in-memory copies)
save_layer(ocean,     "ocean_wgs84")
save_layer(land,      "land_wgs84")
save_layer(water,     "water_wgs84")
save_layer(waterways, "waterways_wgs84")
save_layer(coast,     "coast_wgs84")
save_layer(roads,     "roads_wgs84")

save_layer(docks, "docks_wgs84")
save_layer(harbours, "habours_wgs84")
save_layer(ferry_terms, "ferry_terms_wgs84")
save_layer(ferry_routes, "ferry_routes_wgs84")
save_layer(tss, "tss_wgs84")
save_layer(rocks_reefs, "rocks_reefs_wgs84")
save_layer(bridges, "bridges_wgs84")
save_layer(seas, "seas_wgs84")

# C) Web-mercator for quick plots
to_3857 = lambda g: g.to_crs("EPSG:3857") if not g.empty else gpd.GeoDataFrame(geometry=[], crs="EPSG:3857")
save_layer(to_3857(ocean),     "ocean_3857")
save_layer(to_3857(land),      "land_3857")
save_layer(to_3857(water),     "water_3857")
save_layer(to_3857(waterways), "waterways_3857")
save_layer(to_3857(coast),     "coast_3857")
save_layer(to_3857(roads),     "roads_3857")
save_layer(to_3857(frame_wgs84), "frame_3857")

save_layer(to_3857(docks), "docks_3857")
save_layer(to_3857(harbours), "habours_3857")
save_layer(to_3857(ferry_terms), "ferry_terms_3857")
save_layer(to_3857(ferry_routes), "ferry_routes_3857")
save_layer(to_3857(tss), "tss_3857")
save_layer(to_3857(rocks_reefs), "rocks_reefs_3857")
save_layer(to_3857(bridges), "bridges_3857")
save_layer(to_3857(seas), "seas_3857")


# D) UTM for analysis/buffering
base_for_crs = land if not land.empty else ocean
utm_crs = base_for_crs.estimate_utm_crs()
to_utm = lambda g: g.to_crs(utm_crs) if not g.empty else gpd.GeoDataFrame(geometry=[], crs=utm_crs)

ocean_utm     = to_utm(ocean);      save_layer(ocean_utm,     "ocean_utm")
land_utm      = to_utm(land);       save_layer(land_utm,      "land_utm")
water_utm     = to_utm(water);      save_layer(water_utm,     "water_utm")
waterways_utm = to_utm(waterways);  save_layer(waterways_utm, "waterways_utm")
coast_utm     = to_utm(coast);      save_layer(coast_utm,     "coast_utm")
roads_utm     = to_utm(roads);      save_layer(roads_utm,     "roads_utm")
frame_utm     = to_utm(frame_wgs84);save_layer(frame_utm,     "frame_utm")

docks_utm      = to_utm(docks);       save_layer(docks_utm,      "docks_utm")
harbours_utm      = to_utm(harbours);       save_layer(harbours_utm,      "harbours_utm")
ferry_terms_utm      = to_utm(ferry_terms);       save_layer(ferry_terms_utm,      "ferry_terms_utm")
ferry_routes_utm      = to_utm(ferry_routes);       save_layer(ferry_routes_utm,      "ferry_routes_utm")
tss_utm      = to_utm(tss);       save_layer(tss_utm,      "tss_utm")
rocks_reefs_utm      = to_utm(rocks_reefs);       save_layer(rocks_reefs_utm,      "rocks_reefs_utm")
bridges_utm      = to_utm(bridges);       save_layer(bridges_utm,      "bridges_utm")
seas_utm      = to_utm(seas);       save_layer(seas_utm,      "seas_utm")


# E) Union masks (single-geometry layers)
if not ocean_utm.empty:
    gpd.GeoDataFrame(geometry=[unary_union(ocean_utm.geometry)], crs=utm_crs)\
        .to_file(OUT_GPKG, layer="ocean_union_utm", driver="GPKG")
if not land_utm.empty:
    gpd.GeoDataFrame(geometry=[unary_union(land_utm.geometry)], crs=utm_crs)\
        .to_file(OUT_GPKG, layer="land_union_utm", driver="GPKG")
if not water_utm.empty:
    gpd.GeoDataFrame(geometry=[unary_union(water_utm.geometry)], crs=utm_crs)\
        .to_file(OUT_GPKG, layer="water_union_utm", driver="GPKG")
if not coast_utm.empty:
    gpd.GeoDataFrame(geometry=[unary_union(coast_utm.geometry)], crs=utm_crs)\
        .to_file(OUT_GPKG, layer="coast_union_utm", driver="GPKG")


if not docks_utm.empty:
    gpd.GeoDataFrame(geometry=[unary_union(docks_utm.geometry)], crs=utm_crs)\
        .to_file(OUT_GPKG, layer="docks_union_utm", driver="GPKG")    
if not harbours_utm.empty:
    gpd.GeoDataFrame(geometry=[unary_union(harbours_utm.geometry)], crs=utm_crs)\
        .to_file(OUT_GPKG, layer="harbours_union_utm", driver="GPKG")    
if not ferry_terms_utm.empty:
    gpd.GeoDataFrame(geometry=[unary_union(ferry_terms_utm.geometry)], crs=utm_crs)\
        .to_file(OUT_GPKG, layer="ferry_terms_union_utm", driver="GPKG")    
if not ferry_routes_utm.empty:
    gpd.GeoDataFrame(geometry=[unary_union(ferry_routes_utm.geometry)], crs=utm_crs)\
        .to_file(OUT_GPKG, layer="ferry_routes_union_utm", driver="GPKG")    
if not tss_utm.empty:
    gpd.GeoDataFrame(geometry=[unary_union(tss_utm.geometry)], crs=utm_crs)\
        .to_file(OUT_GPKG, layer="tss_union_utm", driver="GPKG")    
if not rocks_reefs_utm.empty:
    gpd.GeoDataFrame(geometry=[unary_union(rocks_reefs_utm.geometry)], crs=utm_crs)\
        .to_file(OUT_GPKG, layer="rocks_reefs_union_utm", driver="GPKG")    
if not bridges_utm.empty:
    gpd.GeoDataFrame(geometry=[unary_union(bridges_utm.geometry)], crs=utm_crs)\
        .to_file(OUT_GPKG, layer="bridges_union_utm", driver="GPKG")
if not seas_utm.empty:
    gpd.GeoDataFrame(geometry=[unary_union(seas_utm.geometry)], crs=utm_crs)\
        .to_file(OUT_GPKG, layer="seas_union_utm", driver="GPKG")

print(f"Saved fresh layers to {OUT_GPKG}")

# Quick exact-fit render (optional)
if not to_3857(frame_wgs84).empty:
    frame_3857 = gpd.read_file(OUT_GPKG, layer="frame_3857")
    fminx, fminy, fmaxx, fmaxy = frame_3857.total_bounds
    aspect = (fmaxx - fminx) / max(1e-9, (fmaxy - fminy))
    width_in = 12.0
    height_in = width_in / aspect
    fig, ax = plt.subplots(figsize=(width_in, height_in), dpi=220)
    gpd.read_file(OUT_GPKG, layer="land_3857").plot(ax=ax, facecolor="#e6e6e6", edgecolor="#c8c8c8", lw=0.3, zorder=0)
    gpd.read_file(OUT_GPKG, layer="ocean_3857").plot(ax=ax, facecolor="#a0c8f0", edgecolor="none", zorder=1)
    gpd.read_file(OUT_GPKG, layer="water_3857").plot(ax=ax, facecolor="#a0c8f0", edgecolor="#74a8d8", lw=0.4, zorder=2)
    gpd.read_file(OUT_GPKG, layer="coast_3857").plot(ax=ax, color="#2f7f3f", lw=1.2, zorder=3)

    gpd.read_file(OUT_GPKG, layer="docks_3857").plot(ax=ax, facecolor="red", edgecolor="black", lw=0.4, zorder=2)
    gpd.read_file(OUT_GPKG, layer="habours_3857").plot(ax=ax, facecolor="red", edgecolor="black", lw=0.4, zorder=2)
    gpd.read_file(OUT_GPKG, layer="ferry_terms_3857").plot(ax=ax, facecolor="red", edgecolor="black", lw=0.4, zorder=2)
    gpd.read_file(OUT_GPKG, layer="ferry_routes_3857").plot(ax=ax, facecolor="red", edgecolor="black", lw=0.4, zorder=2)
    gpd.read_file(OUT_GPKG, layer="tss_3857").plot(ax=ax, facecolor="red", edgecolor="black", lw=0.4, zorder=2)
    gpd.read_file(OUT_GPKG, layer="rocks_reefs_3857").plot(ax=ax, facecolor="red", edgecolor="black", lw=0.4, zorder=2)
    gpd.read_file(OUT_GPKG, layer="bridges_3857").plot(ax=ax, facecolor="red", edgecolor="black", lw=0.4, zorder=2)
    gpd.read_file(OUT_GPKG, layer="seas_3857").plot(ax=ax, facecolor="red", edgecolor="black", lw=0.4, zorder=2)

    ax.set_xlim(fminx, fmaxx); ax.set_ylim(fminy, fmaxy)
    ax.set_aspect("equal"); ax.set_axis_off(); ax.margins(0)
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig("figures/map_fit.png", dpi=300, bbox_inches="tight", pad_inches=0)
    plt.show()
