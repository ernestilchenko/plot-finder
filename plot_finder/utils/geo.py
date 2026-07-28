import xml.etree.ElementTree as ET

from shapely.geometry import MultiPolygon, Polygon


def reproject(geom, src_srid: int, dst_srid: int):
    if src_srid == dst_srid:
        return geom
    from pyproj import Transformer
    from shapely.ops import transform
    t = Transformer.from_crs(f"EPSG:{src_srid}", f"EPSG:{dst_srid}", always_xy=True)
    return transform(t.transform, geom)


def to_4326(geom, srid: int):
    return reproject(geom, srid, 4326)


def transform_xy(x: float, y: float, src_srid: int, dst_srid: int) -> tuple[float, float]:
    if src_srid == dst_srid:
        return x, y
    from pyproj import Transformer
    return Transformer.from_crs(f"EPSG:{src_srid}", f"EPSG:{dst_srid}", always_xy=True).transform(x, y)


def drop_z(geom):
    if geom.has_z:
        from shapely.ops import transform
        return transform(lambda *c: c[:2], geom)
    return geom


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _rings(element: ET.Element, kind: str, swap: bool) -> list[list[tuple[float, float]]]:
    rings = []
    for holder in element.iter():
        if _local(holder.tag) != kind:
            continue
        coords: list[tuple[float, float]] = []
        for node in holder.iter():
            if _local(node.tag) in ("posList", "pos") and node.text:
                nums = [float(v) for v in node.text.split()]
                if swap:
                    coords += [(nums[i + 1], nums[i]) for i in range(0, len(nums), 2)]
                else:
                    coords += [(nums[i], nums[i + 1]) for i in range(0, len(nums), 2)]
        if len(coords) >= 4:
            rings.append(coords)
    return rings


def gml_geometry(element: ET.Element, swap: bool = False):
    """Build a shapely Polygon/MultiPolygon from a GML feature element.

    ``swap`` swaps posList lat/lon pairs to lon/lat (needed for geographic CRS
    output like EPSG:4258/6706); leave it ``False`` for projected coordinates.
    """
    shells = _rings(element, "exterior", swap)
    if not shells:
        return None
    holes = _rings(element, "interior", swap)
    if len(shells) == 1:
        return Polygon(shells[0], holes)
    return MultiPolygon([Polygon(s) for s in shells])


def iter_features(root: ET.Element, name: str | None = None):
    """Yield feature elements from a GML document.

    With ``name`` given, yields every element with that local tag name; otherwise
    yields the feature inside each ``wfs:member`` / ``gml:featureMember``.
    """
    if name is not None:
        for element in root.iter():
            if _local(element.tag) == name:
                yield element
        return
    for member in root.iter():
        if _local(member.tag) in ("member", "featureMember"):
            feat = next(iter(member), None)
            if feat is not None:
                yield feat


def gml_attrs(feat: ET.Element) -> dict:
    """Collect leaf-element text of a GML feature as ``{local_name: text}``."""
    return {_local(e.tag): e.text.strip() for e in feat.iter() if not list(e) and e.text and e.text.strip()}
