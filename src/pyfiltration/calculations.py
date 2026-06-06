"""Core CADR and mass-balance calculations."""

from __future__ import annotations

import math
from collections.abc import Sequence


def cadr_from_decay(
    chamber_volume_m3: float,
    total_decay_per_h: float,
    natural_decay_per_h: float,
) -> float:
    """Calculate CADR from first-order decay constants in 1/h."""
    if chamber_volume_m3 <= 0:
        raise ValueError("chamber_volume_m3 must be positive")
    if total_decay_per_h < 0 or natural_decay_per_h < 0:
        raise ValueError("decay rates must be non-negative")
    return max(0.0, chamber_volume_m3 * (total_decay_per_h - natural_decay_per_h))


def decay_rate_from_samples(
    samples: Sequence[tuple[float, float]],
    *,
    time_unit: str = "min",
    background_concentration: float = 0.0,
) -> float:
    """Fit a first-order decay rate from `(time, concentration)` samples.

    Returns the decay constant in 1/h.
    """
    if len(samples) < 2:
        raise ValueError("at least two samples are required")
    scale_to_h = {"min": 60.0, "h": 1.0, "s": 3600.0}.get(time_unit)
    if scale_to_h is None:
        raise ValueError("time_unit must be one of: 's', 'min', 'h'")

    x_values: list[float] = []
    y_values: list[float] = []
    for time_value, concentration in samples:
        adjusted = concentration - background_concentration
        if adjusted <= 0:
            raise ValueError("all background-adjusted concentrations must be positive")
        x_values.append(time_value)
        y_values.append(math.log(adjusted))

    x_mean = sum(x_values) / len(x_values)
    y_mean = sum(y_values) / len(y_values)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values, strict=True))
    denominator = sum((x - x_mean) ** 2 for x in x_values)
    if denominator == 0:
        raise ValueError("sample times must not all be identical")

    slope_per_time_unit = numerator / denominator
    return max(0.0, -slope_per_time_unit * scale_to_h)


def cadr_from_airflow(
    airflow_m3h: float,
    single_pass_efficiency: float,
    *,
    bypass_fraction: float = 0.0,
    mixing_effectiveness: float = 1.0,
) -> float:
    """Estimate effective CADR from airflow and single-pass efficiency."""
    if airflow_m3h < 0:
        raise ValueError("airflow_m3h must be non-negative")
    for name, value in {
        "single_pass_efficiency": single_pass_efficiency,
        "bypass_fraction": bypass_fraction,
        "mixing_effectiveness": mixing_effectiveness,
    }.items():
        if not 0 <= value <= 1:
            raise ValueError(f"{name} must be between 0 and 1")
    return airflow_m3h * single_pass_efficiency * (1.0 - bypass_fraction) * mixing_effectiveness


def pm25_cadr_from_smoke_dust(smoke_cadr: float, dust_cadr: float) -> float:
    """Estimate PM2.5 CADR as the geometric mean of smoke and dust CADR."""
    if smoke_cadr < 0 or dust_cadr < 0:
        raise ValueError("smoke_cadr and dust_cadr must be non-negative")
    return math.sqrt(smoke_cadr * dust_cadr)


def required_cadr_for_clean_ach(
    room_volume_m3: float,
    target_clean_ach: float,
    existing_removal_ach: float = 0.0,
) -> float:
    """CADR needed to reach a target equivalent clean-air change rate."""
    if room_volume_m3 <= 0:
        raise ValueError("room_volume_m3 must be positive")
    if target_clean_ach < 0 or existing_removal_ach < 0:
        raise ValueError("ACH values must be non-negative")
    return room_volume_m3 * max(target_clean_ach - existing_removal_ach, 0.0)


def required_cadr_for_target_concentration(
    *,
    room_volume_m3: float,
    target_concentration_ug_m3: float,
    source_generation_ug_h: float,
    ventilation_m3h: float = 0.0,
    outdoor_concentration_ug_m3: float = 0.0,
    natural_loss_ach: float = 0.0,
) -> float:
    """CADR needed for a steady-state concentration target under a continuous source."""
    if room_volume_m3 <= 0:
        raise ValueError("room_volume_m3 must be positive")
    if target_concentration_ug_m3 <= 0:
        raise ValueError("target_concentration_ug_m3 must be positive")
    if source_generation_ug_h < 0 or ventilation_m3h < 0 or outdoor_concentration_ug_m3 < 0:
        raise ValueError("source, ventilation, and outdoor concentration must be non-negative")
    if natural_loss_ach < 0:
        raise ValueError("natural_loss_ach must be non-negative")

    required_total_removal_m3h = (
        source_generation_ug_h + ventilation_m3h * outdoor_concentration_ug_m3
    ) / target_concentration_ug_m3
    existing_removal_m3h = ventilation_m3h + natural_loss_ach * room_volume_m3
    return max(0.0, required_total_removal_m3h - existing_removal_m3h)


def time_to_fraction_remaining_min(total_loss_per_h: float, fraction_remaining: float) -> float:
    """Time for a first-order process to reach a remaining fraction."""
    if total_loss_per_h <= 0:
        return math.inf
    if not 0 < fraction_remaining < 1:
        raise ValueError("fraction_remaining must be between 0 and 1")
    return -math.log(fraction_remaining) / total_loss_per_h * 60.0
