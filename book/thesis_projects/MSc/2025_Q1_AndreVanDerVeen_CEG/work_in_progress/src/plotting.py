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