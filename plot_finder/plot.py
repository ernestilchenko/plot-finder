from typing import Any

import httpx
import shapely.wkt
from pydantic import BaseModel, computed_field, model_validator

from plot_finder.exceptions import AddressNotFoundError, GeocodeError, GugikError, PlotNotFoundError, ULDKError

_ULDK_URL = "https://uldk.gugik.gov.pl/"
_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_RESULT_FIELDS = "teryt,voivodeship,county,commune,region,parcel,geom_wkt,geom_extent,datasource"


class Plot(BaseModel):
    plot_id: str | None = None
    address: str | None = None
    x: float | None = None
    y: float | None = None
    voivodeship: str | None = None
    county: str | None = None
    commune: str | None = None
    region: str | None = None
    parcel: str | None = None
    srid: int = 2180
    geom_wkt: str | None = None
    geom_extent: str | None = None
    datasource: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def area(self) -> float | None:
        if not self.geom_wkt:
            return None
        geom = shapely.wkt.loads(self.geom_wkt)
        return round(geom.area, 2)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def centroid(self) -> tuple[float, float] | None:
        if not self.geom_wkt:
            return None
        geom = shapely.wkt.loads(self.geom_wkt)
        return geom.centroid.x, geom.centroid.y

    @computed_field  # type: ignore[prop-decorator]
    @property
    def geojson(self) -> dict[str, Any] | None:
        if not self.geom_wkt:
            return None
        geom = shapely.wkt.loads(self.geom_wkt)
        return shapely.geometry.mapping(geom)

    @model_validator(mode="after")
    def _auto_fetch(self) -> "Plot":
        if self.voivodeship is not None:
            return self
        if self.address and not self.plot_id and self.x is None:
            self._geocode()
        if not self.plot_id and self.x is None:
            raise ValueError("Either 'plot_id', 'address', or both 'x' and 'y' must be provided")
        if self.x is not None and self.y is None:
            raise ValueError("Both 'x' and 'y' must be provided")
        self._fetch()
        return self

    def _geocode(self) -> None:
        params = {"q": self.address, "format": "json", "limit": 1}
        headers = {"User-Agent": "plot-finder/1.0"}
        try:
            resp = httpx.get(_NOMINATIM_URL, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise GeocodeError(f"Geocoding request failed: {exc}") from exc

        results = resp.json()
        if not results:
            raise AddressNotFoundError(f"No results for address: {self.address}")

        self.y = float(results[0]["lat"])
        self.x = float(results[0]["lon"])
        self.srid = 4326

    def _fetch(self) -> None:
        if self.x is not None:
            xy = f"{self.x},{self.y}"
            if self.srid != 2180:
                xy += f",{self.srid}"
            params = {
                "request": "GetParcelByXY",
                "xy": xy,
                "result": _RESULT_FIELDS,
                "srid": str(self.srid),
            }
        else:
            params = {
                "request": "GetParcelById",
                "id": self.plot_id,
                "result": _RESULT_FIELDS,
                "srid": str(self.srid),
            }

        try:
            resp = httpx.get(_ULDK_URL, params=params, timeout=30)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ULDKError(f"HTTP request failed: {exc}") from exc

        lines = resp.text.strip().splitlines()
        if not lines:
            raise ULDKError("Empty response from ULDK API")

        status = lines[0].strip()
        if status.startswith("-1") or len(lines) < 2:
            query = f"xy={self.x},{self.y}" if self.x is not None else self.plot_id
            raise PlotNotFoundError(f"Parcel not found: {query}")

        parts = lines[1].split("|")
        field_names = _RESULT_FIELDS.split(",")
        for name, value in zip(field_names, parts):
            val = value.strip() or None
            if name == "teryt":
                self.plot_id = val
            else:
                setattr(self, name, val)

        if self.geom_wkt and ";" in self.geom_wkt:
            _, wkt = self.geom_wkt.split(";", 1)
            self.geom_wkt = wkt

    def gugik(self) -> list["GugikEntry"]:
        """Fetch GUGiK integration data for this plot's TERYT ID.

        Requires ``beautifulsoup4``: ``pip install plot-finder[geo]``
        """
        from plot_finder.gugik import GugikEntry

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError(
                "beautifulsoup4 is required for GUGiK queries. "
                "Install it with: pip install plot-finder[geo]"
            )

        if not self.plot_id:
            raise GugikError("plot_id is required for GUGiK queries")

        teryt = self.plot_id
        url = (
            f"https://integracja.gugik.gov.pl/eziudp/index.php"
            f"?teryt={teryt}&rodzaj=&nazwa=&zbior=&temat=&usluga=&adres="
        )

        try:
            resp = httpx.get(url, timeout=30)
        except httpx.HTTPError as exc:
            raise GugikError(f"GUGiK request failed: {exc}") from exc

        if resp.status_code != 200:
            raise GugikError(f"GUGiK returned {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.find_all("tr", class_="row")
        entries: list[GugikEntry] = []

        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 7:
                organ = cols[1].get_text(strip=True)
                nazwa = cols[2].get_text(strip=True)
                wms = cols[5].find("a")["href"] if cols[5].find("a") else None
                wfs = cols[6].find("a")["href"] if cols[6].find("a") else None
                entries.append(GugikEntry(organ=organ, nazwa=nazwa, wms=wms, wfs=wfs))

        return entries
