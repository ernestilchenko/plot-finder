# The `Plot` object

`Plot` is a [Pydantic v2](https://docs.pydantic.dev/) model. Constructing one
triggers a lookup against the selected country's cadastre and fills in the
geometry and attributes.

## Construction

```python
Plot(
    country,          # required: "PL" | "FR" | "ES" | "NL"
    plot_id=None,     # cadastral id / reference / designation
    address=None,     # free-form address (geocoded)
    x=None, y=None,   # coordinates
    srid=None,        # coordinate CRS (defaults to the country's native CRS)
)
```

Rules:

- **`country` is required** — there is no default.
- Provide **one** of: `plot_id`, `address`, or both `x` and `y`.
- `srid` defaults per country (PL → 2180, FR/ES/NL → 4326). It is the CRS of the
  **input** coordinates.

## Common fields

| Field | Type | Description |
|-------|------|-------------|
| `country` | `str` | Country code, echoed back |
| `plot_id` | `str` | Cadastral identifier for the country |
| `address` | `str \| None` | The input address, if one was given |
| `x`, `y` | `float \| None` | Input coordinates |
| `srid` | `int` | CRS of the coordinates |
| `geom_wkt` | `str` | Parcel geometry as WKT |
| `geom_extent` | `str \| None` | Bounding box, when the source provides one |
| `datasource` | `str` | Human-readable origin of the data |

## Computed properties

| Property | Type | Description |
|----------|------|-------------|
| `area` | `float` | Area in **m²**, measured in the country's metric CRS |
| `centroid` | `(float, float)` | Centroid of the geometry |
| `geojson` | `dict` | Geometry as a GeoJSON mapping |

## Country attributes

The remaining attributes depend on `country` and come from the matching class in
`plot_finder.countries`:

| Country | Attributes |
|---------|-----------|
| `Poland` | `voivodeship`, `county`, `commune`, `region`, `parcel` |
| `France` | `department`, `insee`, `commune`, `section`, `numero` |
| `Spain` | `province`, `municipality` |
| `Netherlands` | `municipality`, `section`, `parcel_number` |

They are exposed **flat** on the plot and included in `model_dump()`:

```python
p = Plot(country="PL", x=639231, y=486743)
p.voivodeship          # 'mazowieckie'
p.model_dump().keys()  # common fields + country attributes + computed props
```

## Serialization

```python
p.model_dump()        # dict
p.model_dump_json()    # JSON string
```

Both include the common fields, the country attributes and the computed
`area` / `centroid` / `geojson`.

## Exceptions

| Exception | Raised by |
|-----------|-----------|
| `PlotNotFoundError` | any country — no parcel for the query |
| `AddressNotFoundError` | address geocoding returned nothing |
| `ULDKError` | Poland (ULDK / GUGiK) |
| `IGNError` | France (IGN apicarto) |
| `CatastroError` | Spain (Dirección General del Catastro) |
| `KadasterError` | Netherlands (PDOK Kadaster) |
