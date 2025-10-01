# readgpkg_min.py
import geopandas as gpd
import matplotlib.pyplot as plt

gpkg = "files/basemap.gpkg"

# Read the exact AOI box + layers (UTM = metric CRS)
# You can also read frame_wgs84, frame_3857 frame_utm depending on the format you want for your application.
frame = gpd.read_file(gpkg, layer="frame_3857")
ocean = gpd.read_file(gpkg, layer="ocean_3857")
land  = gpd.read_file(gpkg, layer="land_3857")

# Optional extras (comment out if you don’t want them)
try:
    water = gpd.read_file(gpkg, layer="water_3857")
except Exception:
    water = gpd.GeoDataFrame(geometry=[], crs=ocean.crs)

try:
    coast = gpd.read_file(gpkg, layer="coast_3857")
except Exception:
    coast = gpd.GeoDataFrame(geometry=[], crs=ocean.crs)

# Make the figure match the AOI aspect exactly
minx, miny, maxx, maxy = frame.total_bounds
aspect = (maxx - minx) / max(1e-9, (maxy - miny))
width_in = 12.0
height_in = width_in / aspect

fig, ax = plt.subplots(figsize=(width_in, height_in), dpi=220)

# Draw: land (grey) → ocean (blue) → (optional) inland water → (optional) coastline
if not land.empty:
    land.plot(ax=ax, facecolor="#e6e6e6", edgecolor="#bbbbbb", linewidth=0.3, zorder=0)
if not ocean.empty:
    ocean.plot(ax=ax, facecolor="#a0c8f0", edgecolor="none", zorder=1)
if not water.empty:
    water.plot(ax=ax, facecolor="#a0c8f0", edgecolor="#74a8d8", linewidth=0.4, alpha=0.95, zorder=2)
if not coast.empty:
    coast.plot(ax=ax, color="#2f7f3f", linewidth=1.2, zorder=3)

# Fit exactly to the box, no margins
ax.set_xlim(minx, maxx); ax.set_ylim(miny, maxy)
# ax.set_aspect("equal", adjustable="box")
ax.set_aspect("equal"); ax.set_axis_off(); ax.margins(0)
# ax.set_axis_off()
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
# plt.tight_layout(pad=0)
plt.savefig("figures/map_fit.png", dpi=300, bbox_inches="tight", pad_inches=0)
plt.show()
