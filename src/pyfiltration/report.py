"""Report writers for CLI output."""

from __future__ import annotations

import json
from pathlib import Path

from .models import DesignInputs, DesignResult


def write_summary_files(inputs: DesignInputs, result: DesignResult, output_dir: str | Path) -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    json_path = output / "summary.json"
    md_path = output / "summary.md"

    json_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    md_path.write_text(_summary_markdown(inputs, result), encoding="utf-8")
    return json_path, md_path


def _summary_markdown(inputs: DesignInputs, result: DesignResult) -> str:
    warnings = "\n".join(f"- {warning}" for warning in result.warnings) or "- None"
    service_life = (
        f"{result.formaldehyde_service_life_h:.0f} h"
        if result.formaldehyde_service_life_h is not None
        else "not calculated"
    )
    capture_rate = (
        f"{result.formaldehyde_capture_rate_mg_h:.2f} mg/h"
        if result.formaldehyde_capture_rate_mg_h is not None
        else "not calculated"
    )
    pressure_margin = (
        f"{result.pressure_margin_at_design_pa:.1f} Pa"
        if result.pressure_margin_at_design_pa is not None
        else "fixed-flow fan input"
    )

    return f"""# pyFiltration Design Summary

## Room

- Name: {inputs.room.name}
- Floor area: {result.room_floor_area_m2:.2f} m2
- Volume: {result.room_volume_m3:.2f} m3
- Mixing effectiveness: {inputs.room.mixing_effectiveness:.2f}

## CADR

| Metric | Required | Clean estimated | Loaded estimated |
| --- | ---: | ---: | ---: |
| P-CADR | {result.required_p_cadr_m3h:.1f} m3/h | {result.clean_p_cadr_m3h:.1f} m3/h | {result.loaded_p_cadr_m3h:.1f} m3/h |
| F-CADR | {result.required_f_cadr_m3h:.1f} m3/h | {result.clean_f_cadr_m3h:.1f} m3/h | {result.loaded_f_cadr_m3h:.1f} m3/h |

## Filter And Fan

- Media area basis: {result.media_area_basis}
- Design airflow: {result.design_airflow_m3h:.1f} m3/h
- Clean airflow: {result.clean_airflow_m3h:.1f} m3/h
- Loaded airflow: {result.loaded_airflow_m3h:.1f} m3/h
- Media area used: {result.required_media_area_m2:.3f} m2
- Calculated minimum media area: {result.minimum_required_media_area_m2:.3f} m2
- Frontal area: {result.frontal_area_m2:.3f} m2
- Clean pressure drop: {result.clean_pressure_drop_pa:.1f} Pa
- Loaded pressure drop: {result.loaded_pressure_drop_pa:.1f} Pa
- Pressure margin at design airflow: {pressure_margin}

## Performance

- Particle efficiency used: {result.particle_efficiency_used:.3f}
- Formaldehyde efficiency used: {result.formaldehyde_efficiency_used:.3f}
- Clean P-ACH: {result.clean_p_ach:.2f} 1/h
- Loaded P-ACH: {result.loaded_p_ach:.2f} 1/h
- Clean F-ACH: {result.clean_f_ach:.2f} 1/h
- Loaded F-ACH: {result.loaded_f_ach:.2f} 1/h
- Particle time to 80 percent reduction: {result.p_time_to_80_percent_reduction_min:.1f} min
- Formaldehyde time to 80 percent reduction: {result.f_time_to_80_percent_reduction_min:.1f} min
- Formaldehyde capture rate: {capture_rate}
- Estimated formaldehyde service life: {service_life}

## Warnings

{warnings}
"""
