#empty for now
import fiona
from shapely.geometry import shape
from src.utils import get_integer_multiple_bounds
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
import numpy as np
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe
import cmocean
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import cartopy.crs as ccrs
from cartopy.io.shapereader import Reader
from cartopy.feature import ShapelyFeature, BORDERS, LAKES, RIVERS, COASTLINE, OCEAN
from src.paths import  SHAPEFILES

def plot_shapefile_overview(
    shapefile,
    title=None,
    padding=2,
    figsize=(10, 8),
    ax=None,
):
    """
    Plot a simple overview map of a shapefile (context / locator map).
    automaticcaly extents to integer bounds as used in pcr glob modelling

    Parameters
    ----------
    shapefile : pathlib.Path or str
        Path to the shapefile (.shp)
    title : str, optional
        Figure title
    padding : float, optional
        Padding (degrees) around shapefile extent
    figsize : tuple, optional
        Figure size if ax is not provided
    ax : cartopy.mpl.geoaxes.GeoAxes, optional
        Existing axes to plot on

    Returns
    -------
    fig, ax
    """

    # Create figure/axes if needed
    if ax is None:
        fig = plt.figure(figsize=figsize)
        ax = plt.axes(projection=ccrs.PlateCarree())
    else:
        fig = ax.figure

    # Background features
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.COASTLINE, linewidth=1)
    ax.add_feature(cfeature.RIVERS, linewidth=1)
    ax.add_feature(cfeature.LAKES)
    ax.add_feature(cfeature.OCEAN, facecolor="#a2daff", edgecolor="none")
    ax.add_feature(
        cfeature.BORDERS,
        linewidth=0.5,
        linestyle="--",
        alpha=0.3,
    )

    # Plot shapefile geometries
    with fiona.open(shapefile) as src:
        for feat in src:
            geom = shape(feat["geometry"])
            ax.add_geometries(
                [geom],
                crs=ccrs.PlateCarree(),
                facecolor="blue",
                edgecolor="black",
                alpha=0.3,
            )


    lon_min, lat_min, lon_max, lat_max = get_integer_multiple_bounds(
        shapefile,
        multiple=3,
    )
    
    ax.set_extent(
        [
            lon_min - padding,
            lon_max + padding,
            lat_min - padding,
            lat_max + padding,
        ],
        crs=ccrs.PlateCarree(),
    )

    # Gridlines
    gl = ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)
    gl.top_labels = False
    gl.right_labels = False

    # Title
    if title is not None:
        ax.set_title(title)
    if title is None:
        stem = Path(shapefile).stem
        title = f"Shapefile overview: {stem}.shp"

    ax.set_title(title)

    return fig, ax


def plot_precipitation_map(
    da,                     # xarray DataArray, e.g., pr resampled/averaged
    title="Average Yearly Precipitation (mm/year)",
    vmin=0,
    vmax=2000,
    n_levels=21,
    contour_lines=None,     # custom contour lines labels, e.g. [100,200,...]
    stations=None,          # list of dicts: [{"lat":..., "lon":..., "name":...}, ...]
    figsize=(5, 4),
    dpi=200,
    cmap="YlGnBu",
    savepath=None,
):
    """
    Plot a filled contour map of precipitation with optional stations and contour lines.
    
    Parameters
    ----------
    da : xarray.DataArray
        2D precipitation array (lat, lon)
    title : str
        Figure title
    vmin, vmax : float
        Min and max for color scale
    n_levels : int
        Number of contour levels
    contour_lines : list of float
        Specific contour levels to label
    stations : list of dict
        Each dict: {"lat": float, "lon": float, "name": str}
    figsize : tuple
        Figure size
    dpi : int
        Figure DPI
    cmap : str
        Colormap
    savepath : str or Path
        Path to save figure (optional)
    """
    
    levels = np.linspace(vmin, vmax, n_levels)
    
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi,
                           subplot_kw={'projection': ccrs.PlateCarree()})
    
    # Filled contours
    im = ax.contourf(
        da['lon'], da['lat'], da,
        levels=levels,
        cmap=cmap,
        extend='both'
    )
    
    # Contour lines
    cs = ax.contour(
        da['lon'], da['lat'], da,
        levels=levels,
        colors='k',
        linewidths=0.2,
        linestyles='--'
    )
    
    # Add contour labels
    if contour_lines is not None:
        ax.clabel(
            cs,
            levels=contour_lines,
            inline=True,
            fmt="%.0f",
            fontsize=6
        )
    
    # Plot stations
    if stations is not None:
        for s in stations:
            marker = Line2D([s['lon']], [s['lat']],
                            marker='o', color='tab:red', markersize=5,
                            transform=ccrs.PlateCarree(),
                            markeredgecolor='white', markeredgewidth=1)
            ax.add_line(marker)
            
            ax.text(
                s['lon']+0.3, s['lat'], s['name'],
                transform=ccrs.PlateCarree(),
                fontsize=7,
                color='tab:red',
                path_effects=[pe.withStroke(linewidth=1, foreground="white")]
            )
    
    # Map features
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.LAKES, alpha=0.5)
    ax.add_feature(cfeature.OCEAN,facecolor="#a2daff", edgecolor="none", zorder=2)
    ax.add_feature(cfeature.RIVERS)
    
    ax.set_title(title)
    
    # Colorbar
    cbar = fig.colorbar(im, ax=ax, orientation="vertical",
                        shrink=0.7,
                        aspect=25,
                        pad=0.02)
    cbar.set_label("mm/year")
    
    # Gridlines
    gl = ax.gridlines(draw_labels=True, linestyle="--", linewidth=0.5)
    gl.top_labels = False
    gl.right_labels = False
    
    fig.tight_layout(pad=0.1)
    
    # Save figure if path provided
    if savepath is not None:
        plt.savefig(savepath, bbox_inches='tight', pad_inches=0.05, dpi=dpi)
    
    plt.show()
    
    return fig, ax

def plot_dem_map(
    da,
    title=None,
    cmap="terrain",
    figsize=(10,8),
    savepath=None,
    shapefile=None,
):
    """
    Plot a DEM (digital elevation) DataArray using Cartopy.

    Parameters
    ----------
    da : xarray.DataArray
        2D elevation data (lat, lon)
    title : str
        Figure title
    cmap : str
        Colormap
    figsize : tuple
        Figure size
    savepath : str or Path
        Optional path to save the figure
    """
    fig, ax = plt.subplots(figsize=figsize, subplot_kw={'projection': ccrs.PlateCarree()})
    
    im = ax.pcolormesh(
        da['lon'], da['lat'], da,
        cmap=cmap,
        shading='auto',
    )
    
    # Map features
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.LAKES)
    ax.add_feature(cfeature.OCEAN,facecolor="#a2daff", edgecolor="none", zorder=2)
    ax.add_feature(cfeature.RIVERS)

    # Overlay shapefile if provided
    if shapefile is not None:
        with fiona.open(shapefile) as src:
            for feat in src:
                geom = shape(feat["geometry"])
                ax.add_geometries(
                    [geom],
                    crs=ccrs.PlateCarree(),
                    facecolor="none",
                    # edgecolor=outline_color,
                    # alpha=outline_alpha,
                    # linewidth=outline_linewidth
                )
    
    
    if title is None:
        title = "DEM map"
    ax.set_title(title)
    
    cbar = fig.colorbar(im, ax=ax, orientation='vertical', shrink=0.7)
    cbar.set_label("Elevation (m)")
    
    if savepath is not None:
        plt.savefig(savepath, bbox_inches='tight', dpi=200)
    
    plt.show()
    
    return fig, ax


## make koppen-geiger figure
def plot_koppen_geiger(path_to_file, savefig=False, save_dir=None, show_legend=True, show_plot=True, show_title=True):
    """
    Docstring for plot_koppen_geiger
    """
    path_to_file = Path(path_to_file)  # <-- make sure this is here
    parts = path_to_file.parts          # <-- now parts is defined

    with rasterio.open(path_to_file) as src:
        data = src.read(1)

    class_names = ["Af","Am","Aw","BWh","BWk","BSh","BSk","Csa","Csb","Csc",
               "Cwa","Cwb","Cwc","Cfa","Cfb","Cfc","Dsa","Dsb","Dsc","Dsd",
               "Dwa","Dwb","Dwc","Dwd","Dfa","Dfb","Dfc","Dfd","ET","EF"]


    rgb_colors = np.array([
        [0, 0, 255], [0, 120, 255], [70, 170, 250], [255, 0, 0], [255, 150, 150],
        [245, 165, 0], [255, 220, 100], [255, 255, 0], [200, 200, 0], [150, 150, 0],
        [150, 255, 150], [100, 200, 100], [50, 150, 50], [200, 255, 80], [100, 255, 80],
        [50, 200, 0], [255, 0, 255], [200, 0, 200], [150, 50, 150], [150, 100, 150],
        [170, 175, 255], [90, 120, 220], [75, 80, 180], [50, 0, 135], [0, 255, 255],
        [55, 200, 255], [0, 125, 125], [0, 70, 95], [178, 178, 178], [102, 102, 102]
    ])/255


    cmap = ListedColormap(rgb_colors)
    norm = BoundaryNorm(np.arange(0.5, 31.5, 1), cmap.N)

    # --- Shapefiles ---
    shapefiles = {
        # "Amu Darya": {"path": SHAPEFILES/"Chatly_GRDC/Chatly_GRDC.shp", "edgecolor": "blue", "linewidth": 2},
        # "Syr Darya": {"path": SHAPEFILES/"Kazalinsk_GRDC/Kazalinsk_GRDC.shp", "edgecolor": "red", "linewidth": 2},
        "Aral Sea Basin": {"path": SHAPEFILES/"AralSea_basin/AralSea_basin.shp", "edgecolor": "black", "linewidth": 1, "linestyle":"-"}
    }

    
    # --- Cartopy figure ---
    fig = plt.figure(figsize=(10,10), dpi = 300)
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([54, 82, 33, 53], crs=ccrs.PlateCarree())

    # --- Plot raster ---
    ax.imshow(data, cmap=cmap, norm=norm,
            origin='upper',
            extent=[-180, 180, -90, 90],  # full raster extent
            #extent=[54, 82, 33, 53],  # full raster extent
            transform=ccrs.PlateCarree())



    # --- Add map features ---
    ax.add_feature(COASTLINE, linewidth=1, edgecolor='black')
    ax.add_feature(BORDERS, linewidth=1, edgecolor='black', linestyle=':')
    ax.add_feature(LAKES, facecolor='lightblue', edgecolor='blue', zorder = 19)
    ax.add_feature(RIVERS, edgecolor='blue', linewidth=1)
    ax.add_feature(OCEAN, facecolor='lightblue', edgecolor='blue', zorder=20)


    legend_handles = []

    # Köppen classes for legend
    for i, name in enumerate(class_names):
        patch = Patch(facecolor=rgb_colors[i], edgecolor='k', label=f"{i+1}: {name}")
        legend_handles.append(patch)

    # Add shapefiles and legend handles
    for label, cfg in shapefiles.items():
        feature = ShapelyFeature(
            Reader(cfg["path"]).geometries(),
            ccrs.PlateCarree(),
            facecolor="none",
            edgecolor=cfg["edgecolor"],
            linewidth=cfg["linewidth"],
            linestyle=cfg["linestyle"]
        )
        ax.add_feature(feature)
        legend_handles.append(Line2D([0], [0], color=cfg["edgecolor"], linewidth=2, label=label, linestyle=cfg["linestyle"]))

    # --- Gridlines and labels ---
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 10}
    gl.ylabel_style = {'size': 10}

    # --- Combined legend ---
    if show_legend:
        plt.legend(handles=legend_handles, bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)

    # # --- Title ---
    # # plt.title("Köppen-Geiger Map for Aral Sea Basin", fontsize=14)

        # --- Build dynamic title ---
    if len(parts) >= 2 and parts[-2].startswith("ssp"):  # future scenario
        scenario = parts[-2]
        year_range = parts[-3]
        title_str = f"Köppen-Geiger Map ({year_range}, {scenario})"
    else:  # historical
        year_range = parts[-2]
        title_str = f"Köppen-Geiger Map ({year_range})"
    
    if show_title:
        plt.title(title_str, fontsize=14)

    plt.tight_layout()

        # --- Auto filename ---
    if savefig:
        # Extract parts from path
        parts = path_to_file.parts
        # Look for historical (1 folder) vs future (2 folders before filename)
        if len(parts) >= 2 and parts[-2].startswith("ssp"):  # future
            scenario = parts[-2]
            year_range = parts[-3]
            fname = f"koppen_{year_range}_{scenario}.png"
        else:  # historical
            year_range = parts[-2]
            fname = f"koppen_{year_range}.png"

        # Save directory
        if save_dir:
            save_path = Path(save_dir) / fname
        else:
            save_path = Path(fname)

        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    
    if show_plot:
        plt.show()
        return fig, ax
    else:
        plt.close(fig)
        return None









