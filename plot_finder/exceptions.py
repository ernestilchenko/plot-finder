class ULDKError(Exception):
    """Base error for ULDK API issues."""


class PlotNotFoundError(ULDKError):
    """Raised when the ULDK API returns no result for the given parcel ID."""


class NothingFoundError(Exception):
    """Raised when no places are found within the given radius."""


class OverpassError(Exception):
    """Base error for Overpass API issues."""


class OverpassTimeoutError(OverpassError):
    """Raised when the Overpass API times out (server too busy)."""


class OverpassRateLimitError(OverpassError):
    """Raised when the Overpass API returns 429 Too Many Requests."""


class OSRMError(Exception):
    """Base error for OSRM routing API issues."""


class OSRMTimeoutError(OSRMError):
    """Raised when the OSRM API request times out."""


class OpenWeatherError(Exception):
    """Base error for OpenWeatherMap API issues."""


class OpenWeatherAuthError(OpenWeatherError):
    """Raised when the OpenWeatherMap API key is missing or invalid."""


class OpenMeteoError(Exception):
    """Base error for Open-Meteo API issues."""


class GeocodeError(Exception):
    """Base error for geocoding issues."""


class AddressNotFoundError(GeocodeError):
    """Raised when Nominatim returns no results for the given address."""


class GeoportalError(Exception):
    """Base error for Geoportal WMS/WFS issues."""


class GDDKiAError(Exception):
    """Base error for GDDKiA noise map issues."""


class SOPOError(Exception):
    """Base error for PIG-PIB SOPO landslide API issues."""


class GugikError(Exception):
    """Base error for GUGiK integration portal issues."""
