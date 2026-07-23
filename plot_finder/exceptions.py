class ULDKError(Exception):
    """Base error for the Polish ULDK (GUGiK) API."""


class IGNError(Exception):
    """Base error for the French IGN (apicarto cadastre) API."""


class CatastroError(Exception):
    """Base error for the Spanish Dirección General del Catastro API."""


class PlotNotFoundError(Exception):
    """Raised when no parcel is found for the given query."""


class GeocodeError(Exception):
    """Base error for geocoding issues."""


class AddressNotFoundError(GeocodeError):
    """Raised when the geocoder returns no results for the given address."""
