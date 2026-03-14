"""Plot boundary overlay for WMS map images.

MapServer-based WMS servers (Geoportal, GUGiK) do **not** support SLD
``UserLayer``/``InlineFeature``, so the overlay is drawn client-side
with Pillow.

When the original WMS tile is blank (common for draft POG plans), an
orthophoto base from Geoportal is fetched automatically so the user
sees geographical context with the plot boundary.
"""
from __future__ import annotations

import logging
import re
from io import BytesIO

import shapely.wkt
from pyproj import Transformer
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import transform

_log = logging.getLogger("plot_finder")

_WMS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://mapy.geoportal.gov.pl/",
}


# ------------------------------------------------------------------
# Geometry helpers
# ------------------------------------------------------------------

def _geom_to_2180(geom_wkt: str, srid: int) -> Polygon | MultiPolygon:
    """Load WKT and transform to EPSG:2180."""
    geom = shapely.wkt.loads(geom_wkt)
    if srid == 2180:
        return geom
    t = Transformer.from_crs(f"EPSG:{srid}", "EPSG:2180", always_xy=True)
    return transform(t.transform, geom)


def _geo_to_pixel(
    x: float, y: float,
    bbox: tuple[float, float, float, float],
    size: tuple[int, int],
) -> tuple[int, int]:
    """Convert EPSG:2180 coordinate to pixel position."""
    minx, miny, maxx, maxy = bbox
    w, h = size
    px = int((x - minx) / (maxx - minx) * w)
    py = int((maxy - y) / (maxy - miny) * h)
    return px, py


# ------------------------------------------------------------------
# URL helpers
# ------------------------------------------------------------------

def _bbox_from_url(url: str) -> tuple[float, float, float, float] | None:
    m = re.search(r"[&?]BBOX=([^&]+)", url, re.IGNORECASE)
    if not m:
        return None
    parts = m.group(1).split(",")
    if len(parts) != 4:
        return None
    try:
        return (float(parts[0]), float(parts[1]),
                float(parts[2]), float(parts[3]))
    except ValueError:
        return None


def _size_from_url(url: str) -> tuple[int, int]:
    wm = re.search(r"[&?]WIDTH=(\d+)", url, re.IGNORECASE)
    hm = re.search(r"[&?]HEIGHT=(\d+)", url, re.IGNORECASE)
    return (int(wm.group(1)) if wm else 800,
            int(hm.group(1)) if hm else 800)



# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def overlay_url(
    base_url: str,
    geom_wkt: str | None,  # noqa: ARG001
    srid: int,              # noqa: ARG001
    layers: list[str],      # noqa: ARG001
    *,
    enabled: bool = True,   # noqa: ARG001
) -> str:
    """Return *base_url* unchanged.

    Kept for backward-compatibility with call sites in ``analyzer.py``
    and ``_async.py``.  The actual overlay is drawn client-side by
    :func:`draw_boundary`.
    """
    return base_url


def draw_boundary(
    img_bytes: bytes,
    geom_wkt: str,
    srid: int,
    bbox: tuple[float, float, float, float],
    size: tuple[int, int] = (800, 800),
    *,
    stroke_color: str = "red",
    stroke_width: int = 3,
    fill_color: tuple[int, int, int, int] = (255, 0, 0, 38),
) -> bytes:
    """Draw the plot polygon on a WMS PNG image.

    Returns new PNG bytes with the boundary overlay.
    Requires ``Pillow``: ``pip install plot-finder[viz]``.
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        raise ImportError(
            "Pillow is required for boundary overlay. "
            "Install it with: pip install plot-finder[viz]"
        )

    geom = _geom_to_2180(geom_wkt, srid)

    img = Image.open(BytesIO(img_bytes)).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    def _draw_poly(poly: Polygon) -> None:
        coords = [_geo_to_pixel(x, y, bbox, size) for x, y in poly.exterior.coords]
        if fill_color:
            draw.polygon(coords, fill=fill_color)
        draw.line(coords + [coords[0]], fill=stroke_color, width=stroke_width)

    if isinstance(geom, MultiPolygon):
        for p in geom.geoms:
            _draw_poly(p)
    else:
        _draw_poly(geom)

    result = Image.alpha_composite(img, overlay)
    buf = BytesIO()
    result.save(buf, format="PNG")
    return buf.getvalue()


def _fetch_image(url: str) -> bytes | None:
    """Download a WMS image, returns bytes or None on failure."""
    import httpx

    try:
        resp = httpx.get(
            url, timeout=30, follow_redirects=True, headers=_WMS_HEADERS,
        )
        if resp.status_code != 200:
            return None
        ct = resp.headers.get("content-type", "")
        if "image" not in ct and "png" not in ct:
            return None
        return resp.content
    except Exception:
        return None


def fetch_wms_with_overlay(
    wms_url: str,
    geom_wkt: str | None,
    srid: int,
    *,
    enabled: bool = True,
) -> bytes | None:
    """Download a WMS image and draw the plot boundary on it.

    Returns PNG bytes, or *None* when the overlay is disabled, geometry
    is missing, or the download fails.  If the tile is blank the
    boundary is still drawn on the empty image.
    """
    if not wms_url or not enabled or not geom_wkt:
        return None

    bbox = _bbox_from_url(wms_url)
    size = _size_from_url(wms_url)
    if bbox is None:
        return None

    try:
        img_data = _fetch_image(wms_url)

        if img_data is None:
            # Server error — create a white canvas so at least
            # the plot boundary is visible.
            from PIL import Image
            canvas = Image.new("RGBA", size, (255, 255, 255, 255))
            buf = BytesIO()
            canvas.save(buf, format="PNG")
            img_data = buf.getvalue()

        return draw_boundary(img_data, geom_wkt, srid, bbox, size)
    except Exception:
        _log.debug("Failed to fetch/render WMS overlay", exc_info=True)
        return None
