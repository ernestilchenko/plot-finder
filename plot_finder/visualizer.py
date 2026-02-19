from __future__ import annotations

import io
import math
from typing import TYPE_CHECKING

import httpx

try:
    import folium
except ImportError:
    folium = None  # type: ignore[assignment]

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None  # type: ignore[assignment,misc]
    ImageDraw = None  # type: ignore[assignment,misc]

if TYPE_CHECKING:
    from plot_finder.report import PlotReport

_TILE_SIZE = 256
_TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"

_CATEGORY_COLORS: dict[str, str] = {
    "education": "blue",
    "finance": "green",
    "transport": "orange",
    "infrastructure": "purple",
    "parks": "darkgreen",
    "water": "cadetblue",
}

_CATEGORY_ICONS: dict[str, str] = {
    "education": "graduation-cap",
    "finance": "university",
    "transport": "bus",
    "infrastructure": "building",
    "parks": "tree",
    "water": "tint",
}


def _latlon_to_pixel(lat: float, lon: float, zoom: int) -> tuple[float, float]:
    n = 2 ** zoom
    x = (lon + 180.0) / 360.0 * n * _TILE_SIZE
    lat_rad = math.radians(lat)
    y = (
        (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi)
        / 2.0
        * n
        * _TILE_SIZE
    )
    return x, y


def _meters_per_pixel(lat: float, zoom: int) -> float:
    return 156543.03 * math.cos(math.radians(lat)) / (2 ** zoom)


def _auto_zoom(lat: float, radius_m: int, img_width: int) -> int:
    for z in range(18, 0, -1):
        mpp = _meters_per_pixel(lat, z)
        if radius_m / mpp * 2.5 < img_width:
            return z
    return 1


class PlotVisualizer:
    """Interactive (folium) and static (PIL) map visualizer for a PlotReport.

    Parameters
    ----------
    report : PlotReport
        The report to visualize.
    colors : dict[str, str] | None
        Override category colours, e.g. ``{"education": "#1f77b4"}``.
        Folium icons accept: red, blue, green, purple, orange, darkred,
        darkblue, darkgreen, cadetblue, darkpurple, pink, lightblue,
        lightgreen, beige, white, lightgray, gray, black, lightred.
        PIL (``image()``) accepts any CSS colour name or hex string.
    plot_color : str
        Colour of the centre marker and radius circle.
    """

    def __init__(
        self,
        report: PlotReport,
        *,
        colors: dict[str, str] | None = None,
        plot_color: str = "red",
    ) -> None:
        self._report = report
        self._colors = {**_CATEGORY_COLORS, **(colors or {})}
        self._plot_color = plot_color

    # ------------------------------------------------------------------
    # Interactive HTML map (folium)
    # ------------------------------------------------------------------

    def map(self) -> folium.Map:
        if folium is None:
            raise ImportError(
                "folium is required for interactive maps. "
                "Install it with: pip install plot-finder[viz]"
            )
        r = self._report
        m = folium.Map(location=[r.lat, r.lon], zoom_start=15)

        folium.Marker(
            location=[r.lat, r.lon],
            popup=f"<b>{r.plot_id}</b>",
            icon=folium.Icon(color=self._plot_color, icon="home", prefix="fa"),
        ).add_to(m)

        folium.Circle(
            location=[r.lat, r.lon],
            radius=r.radius,
            color=self._plot_color,
            fill=False,
            dash_array="5 5",
            weight=2,
        ).add_to(m)

        for category in _CATEGORY_COLORS:
            places: list = getattr(r, category, [])
            if not places:
                continue
            color = self._colors.get(category, "gray")
            fg = folium.FeatureGroup(name=category.capitalize())
            icon_name = _CATEGORY_ICONS.get(category, "info-sign")
            for place in places:
                popup_html = (
                    f"<b>{place.name or 'N/A'}</b><br>"
                    f"Kind: {place.kind}<br>"
                    f"Distance: {place.distance_m}m<br>"
                    f"Walk: {place.walk_min} min | "
                    f"Bike: {place.bike_min} min | "
                    f"Car: {place.car_min} min"
                )
                folium.Marker(
                    location=[place.lat, place.lon],
                    popup=folium.Popup(popup_html, max_width=250),
                    icon=folium.Icon(color=color, icon=icon_name, prefix="fa"),
                ).add_to(fg)
            fg.add_to(m)

        folium.LayerControl().add_to(m)
        return m

    # ------------------------------------------------------------------
    # Static PNG/JPG image (PIL + OSM tiles)
    # ------------------------------------------------------------------

    def image(
        self,
        width: int = 800,
        height: int = 600,
        zoom: int | None = None,
        marker_radius: int = 6,
    ) -> Image.Image:
        """Render a static map image from OpenStreetMap tiles.

        Returns a ``PIL.Image.Image`` — call ``.save("map.png")`` on it,
        or pass it to ``save()`` directly.
        """
        if Image is None:
            raise ImportError(
                "Pillow is required for static map images. "
                "Install it with: pip install plot-finder[viz]"
            )
        r = self._report
        z = zoom or _auto_zoom(r.lat, r.radius, width)

        # --- fetch and stitch tiles ---
        cx, cy = _latlon_to_pixel(r.lat, r.lon, z)
        x_min = cx - width / 2
        y_min = cy - height / 2

        tx_min = int(x_min // _TILE_SIZE)
        tx_max = int((cx + width / 2) // _TILE_SIZE)
        ty_min = int(y_min // _TILE_SIZE)
        ty_max = int((cy + height / 2) // _TILE_SIZE)

        canvas = Image.new(
            "RGB",
            ((tx_max - tx_min + 1) * _TILE_SIZE, (ty_max - ty_min + 1) * _TILE_SIZE),
            (230, 230, 230),
        )

        n_tiles = 2 ** z
        with httpx.Client(
            headers={"User-Agent": "plot-finder/0.1"},
            timeout=10,
        ) as client:
            for tx in range(tx_min, tx_max + 1):
                for ty in range(ty_min, ty_max + 1):
                    if ty < 0 or ty >= n_tiles:
                        continue
                    url = _TILE_URL.format(z=z, x=tx % n_tiles, y=ty)
                    resp = client.get(url)
                    if resp.status_code == 200:
                        tile = Image.open(io.BytesIO(resp.content)).convert("RGB")
                        canvas.paste(
                            tile,
                            ((tx - tx_min) * _TILE_SIZE, (ty - ty_min) * _TILE_SIZE),
                        )

        ox = int(x_min - tx_min * _TILE_SIZE)
        oy = int(y_min - ty_min * _TILE_SIZE)
        img = canvas.crop((ox, oy, ox + width, oy + height))

        # --- draw overlay ---
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        def to_px(lat: float, lon: float) -> tuple[int, int]:
            px, py = _latlon_to_pixel(lat, lon, z)
            return int(px - x_min), int(py - y_min)

        # search radius circle
        mpp = _meters_per_pixel(r.lat, z)
        rpx = int(r.radius / mpp)
        center = to_px(r.lat, r.lon)
        draw.ellipse(
            (
                center[0] - rpx,
                center[1] - rpx,
                center[0] + rpx,
                center[1] + rpx,
            ),
            outline=self._plot_color,
            width=2,
        )

        # category markers
        mr = marker_radius
        for category in _CATEGORY_COLORS:
            places = getattr(r, category, [])
            color = self._colors.get(category, "gray")
            for place in places:
                px = to_px(place.lat, place.lon)
                draw.ellipse(
                    (px[0] - mr, px[1] - mr, px[0] + mr, px[1] + mr),
                    fill=color,
                    outline="white",
                    width=1,
                )

        # centre marker (bigger)
        cr = mr + 3
        draw.ellipse(
            (center[0] - cr, center[1] - cr, center[0] + cr, center[1] + cr),
            fill=self._plot_color,
            outline="white",
            width=2,
        )

        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay)
        return img.convert("RGB")

    # ------------------------------------------------------------------
    # save — auto-detect format by extension
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        """Save map to *path*.

        ``.png`` / ``.jpg`` / ``.jpeg`` → static image (PIL).
        Anything else (e.g. ``.html``) → interactive folium map.
        """
        if path.lower().endswith((".png", ".jpg", ".jpeg")):
            self.image().save(path)
        else:
            self.map().save(path)
