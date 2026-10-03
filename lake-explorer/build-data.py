"""Rebuild the static lake comparison data from the versioned analysis outputs."""
from __future__ import annotations

import ast
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "代码" / "output" / "lake_v2"
CONFIG = ROOT / "代码" / "13_lake_v2" / "lakes_config_v2.py"
DEST = Path(__file__).resolve().parent / "data"
ORDER = ["tianchi", "fuxian", "lugu", "qinghai", "changbaishan", "hulun"]


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_config() -> dict:
    tree = ast.parse(CONFIG.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "LAKES_V2"
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise ValueError("LAKES_V2 was not found")


def compact_geometry(path: Path) -> dict:
    geo = json.loads(path.read_text(encoding="utf-8"))
    try:
        from shapely.geometry import mapping, shape
        geometry = shape(geo["features"][0]["geometry"]).simplify(
            0.0004, preserve_topology=True
        )
        return mapping(geometry)
    except ImportError:
        return geo["features"][0]["geometry"]


def check_summaries(models: list[dict], summaries: list[dict]) -> None:
    primary = [r for r in models if r["kind"] == "future"
               and r["pet_method"] == "oudin"
               and r["runoff_method"] == "schreiber"]
    if len(summaries) != 24:
        raise ValueError(f"Expected 24 lake/scenario/window summaries, got {len(summaries)}")
    for summary in summaries:
        rows = [r for r in primary if r["lake_id"] == summary["lake_id"]
                and r["scenario"] == summary["scenario"]
                and r["window"] == summary["window"]]
        values = sorted(r["dW_mm"] for r in rows if r["dW_mm"] is not None)
        if len(values) != int(summary["n_models"]):
            raise ValueError(f"Mode count mismatch: {summary}")
        midpoint = median(values) if values else None
        if midpoint is None:
            raise ValueError(f"No future mode rows: {summary}")
        checks = {
            "dW_median_mm": midpoint,
            "dW_min_mm": values[0],
            "dW_max_mm": values[-1],
            "pos_models": sum(v > 0 for v in values),
        }
        for key, value in checks.items():
            if abs(float(summary[key]) - value) > 0.11:
                raise ValueError(f"Summary mismatch ({key}): {summary}")
        cross_zero = values[0] < 0 < values[-1]
        if str(summary["cross_zero"]).lower() != str(cross_zero).lower():
            raise ValueError(f"Zero-crossing mismatch: {summary}")


def main() -> None:
    DEST.mkdir(exist_ok=True)
    configs = load_config()
    models = read_csv(OUT / "lake_model_results.csv")
    summaries = read_csv(OUT / "lake_summary.csv")
    validations = read_csv(OUT / "validation_results.csv")
    basin_checks = json.loads((OUT / "basins" / "basins_summary.json").read_text(encoding="utf-8"))
    for row in models:
        for key in ("P_l_mm", "E_l_mm", "P_c_mm", "PET_c_mm", "R_c_mm",
                    "W_mm", "dP_l_mm", "dE_l_mm", "dRc_mm", "dW_mm",
                    "geom_mm", "dW_geo1_mm"):
            row[key] = float(row[key]) if row[key] else None
    check_summaries(models, summaries)

    lakes = []
    for lake_id in ORDER:
        conf = configs[lake_id]
        lakes.append({
            "id": lake_id,
            "name": conf["name"],
            "type": conf["type"],
            "climate": conf["climate"],
            "lat": conf["lat"],
            "lon": conf["lon"],
            "lake_km2": conf["area_lake_km2"],
            "land_km2": conf["area_land_km2"],
            "basin_km2": conf["area_basin_km2"],
            "land_lake_ratio": conf["ac_al_land"],
            "boundary_basis": "公开面积主口径；河流域线供空间定位参考",
            "elev_m": conf.get("elev_m"),
            "elev_src": conf.get("elev_src"),
        })
        basin_dir = OUT / "basins"
        for suffix in ("basin", "lake"):
            source = basin_dir / f"{lake_id}_{suffix}.geojson"
            if source.exists():
                target = DEST / f"{lake_id}-{suffix}.json"
                target.write_text(json.dumps(compact_geometry(source),
                                             ensure_ascii=False,
                                             separators=(",", ":")),
                                  encoding="utf-8")

    payload = {
        "metadata": {
            "title": "典型湖泊气候供水敏感性比较",
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "baseline": "1981–2010",
            "future_windows": ["2041-2060", "2081-2100"],
            "scenarios": ["ssp245", "ssp585"],
            "models": ["MPI-ESM1-2-HR", "MRI-ESM2-0", "EC-Earth3",
                       "CanESM5", "NorESM2-LM"],
            "methods": [{"pet": p, "runoff": r} for p in ("oudin", "hamon")
                        for r in ("schreiber", "turcpike")],
            "primary_method": {"pet": "oudin", "runoff": "schreiber"},
            "units": "mm·a⁻¹",
            "source": "代码/output/lake_v2/{lake_model_results,lake_summary,validation_results}.csv",
            "note": "筛查级气候供水指标；不是水位或湖泊蓄量预测。观测响应检验当前仅适用于青海湖案例，且年际供水序列采用固定气候态蒸发和产流。",
            "elevation_note": "湖面海拔为公开资料常用整数值（逐湖来源见 lakes[].elev_src），随水位年际波动，仅用于定位图着色与数量级示意。",
        },
        "lakes": lakes,
        "models": models,
        "published_summary": summaries,
        "boundaries": {item["lake_id"]: {
            "deviation_pct": item.get("basin_dev_pct"),
            "method": item.get("basin_source"),
        } for item in basin_checks},
        "validation": validations,
    }
    dest = DEST / "lake-data.json"
    dest.write_text(json.dumps(payload, ensure_ascii=False,
                               separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {dest.name}: {len(models)} model rows, "
          f"{len(summaries)} summary rows, {len(lakes)} lakes")


if __name__ == "__main__":
    main()
