import httpx


def get(url: str, error, *, params=None, headers=None, timeout=40):
    """GET ``url``, raising ``error`` on any HTTP failure. Returns the response."""
    try:
        resp = httpx.get(url, params=params, headers=headers, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        return resp
    except httpx.HTTPError as exc:
        raise error(f"request failed: {exc}") from exc


def get_features(url: str, error, *, params=None, headers=None, timeout=40) -> list:
    """GET a GeoJSON/ArcGIS endpoint and return its ``features`` list."""
    resp = get(url, error, params=params, headers=headers, timeout=timeout)
    try:
        return resp.json().get("features") or []
    except ValueError as exc:
        raise error(f"invalid JSON response: {exc}") from exc
