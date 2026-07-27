class ULDKError(Exception):
    """Base error for the Polish ULDK (GUGiK) API."""


class IGNError(Exception):
    """Base error for the French IGN (apicarto cadastre) API."""


class CatastroError(Exception):
    """Base error for the Spanish Dirección General del Catastro API."""


class KadasterError(Exception):
    """Base error for the Dutch PDOK Kadaster (Kadastrale Kaart) API."""


class GeoAdminError(Exception):
    """Base error for the Swiss geo.admin.ch (swisstopo) API."""


class MaaametError(Exception):
    """Base error for the Estonian Maa-amet (Land Board) API."""


class DLSError(Exception):
    """Base error for the Cyprus Department of Lands and Surveys API."""


class RCError(Exception):
    """Base error for the Lithuanian Registrų centras (geoportal.lt) API."""


class VZDError(Exception):
    """Base error for the Latvian Valsts zemes dienests (kadastrs.lv) API."""


class DGTError(Exception):
    """Base error for the Portuguese Direção-Geral do Território (SNIC) API."""


class PlotNotFoundError(Exception):
    """Raised when no parcel is found for the given query."""


class GeocodeError(Exception):
    """Base error for geocoding issues."""


class AddressNotFoundError(GeocodeError):
    """Raised when the geocoder returns no results for the given address."""
