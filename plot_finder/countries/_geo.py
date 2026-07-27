def reproject(geom, src_srid: int, dst_srid: int):
    if src_srid == dst_srid:
        return geom
    from pyproj import Transformer
    from shapely.ops import transform
    t = Transformer.from_crs(f"EPSG:{src_srid}", f"EPSG:{dst_srid}", always_xy=True)
    return transform(t.transform, geom)


def to_4326(geom, srid: int):
    return reproject(geom, srid, 4326)
