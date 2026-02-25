"""CLI for plot-finder.

Usage::

    plot-finder analyze 141201_1.0001.6509 --radius 2000
    plot-finder search --address "Warszawa, Marszalkowska 1"
    plot-finder elevation 141201_1.0001.6509
    plot-finder climate 141201_1.0001.6509
    plot-finder sunlight 141201_1.0001.6509
    plot-finder noise 141201_1.0001.6509
    plot-finder risks 141201_1.0001.6509
"""
from __future__ import annotations

import argparse
import json
import sys

from plot_finder.plot import Plot
from plot_finder.analyzer import PlotAnalyzer
from plot_finder.report import PlotReporter

_BANNER = r"""
           __      __        _____           __
    ____  / /___  / /_      / __(_)___  ____/ /__  _____
   / __ \/ / __ \/ __/_____/ /_/ / __ \/ __  / _ \/ ___/
  / /_/ / / /_/ / /_/_____/ __/ / / / / /_/ /  __/ /
 / .___/_/\____/\__/     /_/ /_/_/ /_/\__,_/\___/_/
/_/
"""


def _banner() -> None:
    print(_BANNER)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="plot-finder",
        description="Analyze Polish land parcels from the command line.",
    )
    sub = parser.add_subparsers(dest="command")

    # --- analyze (full report) ---
    ana = sub.add_parser("analyze", help="Full report for a plot")
    ana.add_argument("plot_id", help="TERYT parcel ID")
    ana.add_argument("--radius", type=int, default=1000, help="Search radius in meters (default: 1000)")
    ana.add_argument("--json", action="store_true", dest="as_json", help="Output raw JSON")
    ana.add_argument("--openweather-key", default=None, help="OpenWeatherMap API key")

    # --- search (find plot by address) ---
    srch = sub.add_parser("search", help="Find a plot by address or coordinates")
    srch.add_argument("--address", default=None, help="Street address to geocode")
    srch.add_argument("--plot-id", default=None, help="TERYT parcel ID")
    srch.add_argument("--x", type=float, default=None, help="X coordinate")
    srch.add_argument("--y", type=float, default=None, help="Y coordinate")
    srch.add_argument("--json", action="store_true", dest="as_json", help="Output raw JSON")

    # --- places ---
    plc = sub.add_parser("places", help="Nearby places (education, transport, etc.)")
    plc.add_argument("plot_id", help="TERYT parcel ID")
    plc.add_argument("--radius", type=int, default=1000, help="Search radius in meters (default: 1000)")
    plc.add_argument("--category", default=None,
                     choices=["education", "finance", "transport", "infrastructure", "green_areas", "water", "nuisances"],
                     help="Single category (default: all)")
    plc.add_argument("--json", action="store_true", dest="as_json", help="Output raw JSON")

    # --- elevation ---
    elev = sub.add_parser("elevation", help="Elevation, slope, aspect")
    elev.add_argument("plot_id", help="TERYT parcel ID")
    elev.add_argument("--json", action="store_true", dest="as_json", help="Output raw JSON")

    # --- climate ---
    clim = sub.add_parser("climate", help="Climate data (last 365 days)")
    clim.add_argument("plot_id", help="TERYT parcel ID")
    clim.add_argument("--json", action="store_true", dest="as_json", help="Output raw JSON")

    # --- sunlight ---
    slt = sub.add_parser("sunlight", help="Sunrise, sunset, daylight hours")
    slt.add_argument("plot_id", help="TERYT parcel ID")
    slt.add_argument("--date", default=None, help="Date (YYYY-MM-DD), default: today")
    slt.add_argument("--json", action="store_true", dest="as_json", help="Output raw JSON")

    # --- noise ---
    ns = sub.add_parser("noise", help="Noise level estimation")
    ns.add_argument("plot_id", help="TERYT parcel ID")
    ns.add_argument("--json", action="store_true", dest="as_json", help="Output raw JSON")

    # --- risks ---
    rsk = sub.add_parser("risks", help="Environmental and geological risks")
    rsk.add_argument("plot_id", help="TERYT parcel ID")
    rsk.add_argument("--json", action="store_true", dest="as_json", help="Output raw JSON")

    return parser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_analyzer(plot_id: str, radius: int = 1000, openweather_key: str | None = None) -> PlotAnalyzer:
    plot = Plot(plot_id=plot_id)
    return PlotAnalyzer(plot, radius=radius, openweather_api_key=openweather_key)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def _cmd_analyze(args: argparse.Namespace) -> None:
    analyzer = _make_analyzer(args.plot_id, args.radius, args.openweather_key)
    report = PlotReporter(analyzer).report()

    if args.as_json:
        print(report.model_dump_json(indent=2))
        return

    _print_report(report)


def _cmd_search(args: argparse.Namespace) -> None:
    if not args.address and not args.plot_id and args.x is None:
        print("Error: provide --address, --plot-id, or --x/--y", file=sys.stderr)
        sys.exit(1)

    plot = Plot(plot_id=args.plot_id, address=args.address, x=args.x, y=args.y)

    if args.as_json:
        print(plot.model_dump_json(indent=2))
        return

    print(f"Plot ID:      {plot.plot_id}")
    print(f"Voivodeship:  {plot.voivodeship}")
    print(f"County:       {plot.county}")
    print(f"Commune:      {plot.commune}")
    print(f"Parcel:       {plot.parcel}")
    if plot.area:
        print(f"Area:         {plot.area} m2")
    if plot.centroid:
        print(f"Centroid:     {plot.centroid[0]:.2f}, {plot.centroid[1]:.2f}")


def _cmd_places(args: argparse.Namespace) -> None:
    analyzer = _make_analyzer(args.plot_id, args.radius)

    if args.category:
        places = getattr(analyzer, args.category)(radius=args.radius)
        result = {args.category: places}
    else:
        result = analyzer.all_places(radius=args.radius)

    if args.as_json:
        print(json.dumps(
            {k: [p.model_dump() for p in v] for k, v in result.items()},
            indent=2, ensure_ascii=False,
        ))
        return

    for cat, places in result.items():
        if not places:
            continue
        print(f"{cat.replace('_', ' ').capitalize()} ({len(places)}):")
        for p in places[:10]:
            label = p.name or p.kind
            print(f"  {label} — {p.distance_m}m, walk {p.walk_min}min")
        if len(places) > 10:
            print(f"  ... and {len(places) - 10} more")
        print()


def _cmd_elevation(args: argparse.Namespace) -> None:
    analyzer = _make_analyzer(args.plot_id)
    elev = analyzer.elevation()

    if args.as_json:
        print(elev.model_dump_json(indent=2))
        return

    print(f"Elevation: {elev.elevation_m} m a.s.l.")
    if elev.slope_deg is not None:
        print(f"Slope:     {elev.slope_deg} deg")
    if elev.aspect:
        print(f"Aspect:    {elev.aspect}", end="")
        if elev.aspect_deg is not None:
            print(f" ({elev.aspect_deg} deg)", end="")
        print()


def _cmd_climate(args: argparse.Namespace) -> None:
    analyzer = _make_analyzer(args.plot_id)
    c = analyzer.climate()

    if args.as_json:
        print(c.model_dump_json(indent=2))
        return

    rows = [
        ("Avg temperature", f"{c.avg_temp} C" if c.avg_temp is not None else None),
        ("Max temperature", f"{c.max_temp} C" if c.max_temp is not None else None),
        ("Min temperature", f"{c.min_temp} C" if c.min_temp is not None else None),
        ("Precipitation", f"{c.total_precipitation_mm} mm" if c.total_precipitation_mm is not None else None),
        ("Rain", f"{c.total_rain_mm} mm" if c.total_rain_mm is not None else None),
        ("Snowfall", f"{c.total_snow_cm} cm" if c.total_snow_cm is not None else None),
        ("Sunshine", f"{c.sunshine_hours} h" if c.sunshine_hours is not None else None),
        ("Avg wind", f"{c.avg_wind_speed} km/h" if c.avg_wind_speed is not None else None),
        ("Max wind", f"{c.max_wind_speed} km/h" if c.max_wind_speed is not None else None),
        ("Frost days", str(c.frost_days) if c.frost_days is not None else None),
        ("Hot days (>30C)", str(c.hot_days) if c.hot_days is not None else None),
        ("Rainy days", str(c.rainy_days) if c.rainy_days is not None else None),
        ("Snow days", str(c.snow_days) if c.snow_days is not None else None),
    ]
    for label, val in rows:
        if val is not None:
            print(f"{label:20s} {val}")


def _cmd_sunlight(args: argparse.Namespace) -> None:
    from datetime import date

    analyzer = _make_analyzer(args.plot_id)
    for_date = date.fromisoformat(args.date) if args.date else None
    s = analyzer.sunlight(for_date=for_date)

    if args.as_json:
        print(s.model_dump_json(indent=2))
        return

    print(f"Date:          {s.date}")
    print(f"Dawn:          {s.dawn}")
    print(f"Sunrise:       {s.sunrise}")
    print(f"Solar noon:    {s.solar_noon}")
    print(f"Sunset:        {s.sunset}")
    print(f"Dusk:          {s.dusk}")
    print(f"Daylight:      {s.daylight_hours} h")
    print(f"Sun elevation: {s.sun_elevation} deg")
    print(f"Sun azimuth:   {s.sun_azimuth} deg")
    if s.golden_hour_morning:
        print(f"Golden AM:     {s.golden_hour_morning}")
    if s.golden_hour_evening:
        print(f"Golden PM:     {s.golden_hour_evening}")
    if s.shadow_length_10m is not None:
        print(f"Shadow (10m):  {s.shadow_length_10m} m")


def _cmd_noise(args: argparse.Namespace) -> None:
    analyzer = _make_analyzer(args.plot_id)
    n = analyzer.noise()

    if args.as_json:
        print(n.model_dump_json(indent=2))
        return

    print(f"Noise level: {n.noise_level_db} dB")
    print(f"Quality:     {n.quality}")
    print(f"Level:       {n.level}")
    print(f"Source:      {n.data_source}")
    if n.sources:
        print(f"Sources ({len(n.sources)}):")
        for src in n.sources:
            print(f"  {src.type}: {src.name} — {src.distance_km} km, {src.impact_db} dB")


def _cmd_risks(args: argparse.Namespace) -> None:
    analyzer = _make_analyzer(args.plot_id)
    r = analyzer.risks()

    if args.as_json:
        print(r.model_dump_json(indent=2))
        return

    if not r.risks:
        print("No risks detected.")
        return

    print(f"Risks ({r.total_risks}):")
    for risk in r.risks:
        marker = "!" if risk.is_at_risk else " "
        print(f"  [{marker}] {risk.risk_type:12s} {risk.level:8s} — {risk.name}")


# ---------------------------------------------------------------------------
# Full report printer
# ---------------------------------------------------------------------------

def _print_report(report) -> None:
    print(f"Plot: {report.plot_id}")
    print(f"Location: {report.lat:.6f}, {report.lon:.6f}")
    print(f"Radius: {report.radius} m")
    print()

    categories = [
        ("Education", report.education),
        ("Finance", report.finance),
        ("Transport", report.transport),
        ("Infrastructure", report.infrastructure),
        ("Green areas", report.green_areas),
        ("Water", report.water),
        ("Nuisances", report.nuisances),
    ]
    for name, places in categories:
        if not places:
            continue
        print(f"{name} ({len(places)}):")
        for p in places[:5]:
            label = p.name or p.kind
            print(f"  {label} — {p.distance_m}m, walk {p.walk_min}min")
        if len(places) > 5:
            print(f"  ... and {len(places) - 5} more")
        print()

    if report.elevation:
        e = report.elevation
        print(f"Elevation: {e.elevation_m} m a.s.l.")
        if e.slope_deg is not None:
            print(f"  Slope: {e.slope_deg} deg, aspect: {e.aspect}")
        print()

    if report.climate:
        c = report.climate
        parts = []
        if c.avg_temp is not None:
            parts.append(f"avg {c.avg_temp} C")
        if c.total_precipitation_mm is not None:
            parts.append(f"precip {c.total_precipitation_mm} mm/yr")
        if c.sunshine_hours is not None:
            parts.append(f"sun {c.sunshine_hours} h/yr")
        if parts:
            print(f"Climate: {', '.join(parts)}")
            print()

    if report.air_quality:
        a = report.air_quality
        print(f"Air quality: AQI {a.aqi} ({a.aqi_label}), PM2.5 {a.pm2_5}, PM10 {a.pm10}")
        print()

    if report.sunlight:
        s = report.sunlight
        print(f"Sunlight: {s.daylight_hours}h, sunrise {s.sunrise}, sunset {s.sunset}")
        print()

    if report.noise:
        n = report.noise
        print(f"Noise: {n.noise_level_db} dB ({n.level})")
        print()

    if report.risks and report.risks.risks:
        print(f"Risks ({report.risks.total_risks}):")
        for r in report.risks.risks:
            print(f"  {r.risk_type}: {r.level} — {r.name}")
        print()

    if report.mpzp:
        m = report.mpzp
        status = "has plan" if m.has_plan else "no plan"
        zone = f", zone: {m.zone_symbol}" if m.zone_symbol else ""
        print(f"MPZP: {status}{zone}")
        print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

_COMMANDS = {
    "analyze": _cmd_analyze,
    "search": _cmd_search,
    "places": _cmd_places,
    "elevation": _cmd_elevation,
    "climate": _cmd_climate,
    "sunlight": _cmd_sunlight,
    "noise": _cmd_noise,
    "risks": _cmd_risks,
}


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        _banner()
        parser.print_help()
        sys.exit(1)

    handler = _COMMANDS.get(args.command)
    if handler:
        handler(args)


if __name__ == "__main__":
    main()
