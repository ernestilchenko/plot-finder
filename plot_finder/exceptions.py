class ULDKError(Exception):
    """Base error for ULDK API issues."""


class PlotNotFoundError(ULDKError):
    """Raised when the ULDK API returns no result for the given parcel ID."""
