"""Air-purifier design calculation workflow."""

from __future__ import annotations

import math

from .calculations import (
    cadr_from_airflow,
    required_cadr_for_clean_ach,
    required_cadr_for_target_concentration,
    time_to_fraction_remaining_min,
)
from .models import DesignInputs, DesignResult, FanSpec, FilterSpec, FormaldehydeSpec

EPS = 1e-9


def design_air_purifier(inputs: DesignInputs) -> DesignResult:
    """Size filter media and estimate P-CADR and F-CADR."""
    room = inputs.room
    filt = inputs.filter
    fan = inputs.fan
    particle = inputs.particle
    hcho = inputs.formaldehyde
    volume = room.volume_m3

    room_required_p = required_cadr_for_clean_ach(
        volume,
        particle.target_clean_ach,
        particle.existing_removal_ach,
    )
    room_required_f_ach = required_cadr_for_clean_ach(
        volume,
        hcho.target_clean_ach,
        hcho.existing_removal_ach,
    )
    required_f_concentration = 0.0
    if hcho.target_concentration_ug_m3 is not None:
        required_f_concentration = required_cadr_for_target_concentration(
            room_volume_m3=volume,
            target_concentration_ug_m3=hcho.target_concentration_ug_m3,
            source_generation_ug_h=hcho.source_generation_ug_h,
            ventilation_m3h=hcho.ventilation_m3h,
            outdoor_concentration_ug_m3=hcho.outdoor_concentration_ug_m3,
            natural_loss_ach=hcho.existing_removal_ach,
        )
    room_required_f = max(room_required_f_ach, required_f_concentration)
    required_p = inputs.required_p_cadr_m3h or room_required_p
    required_f = inputs.required_f_cadr_m3h or room_required_f
    requirement_basis = (
        "direct CADR requirements"
        if inputs.required_p_cadr_m3h is not None or inputs.required_f_cadr_m3h is not None
        else "room-derived targets"
    )

    design_required_p = required_p * inputs.safety_factor
    design_required_f = required_f * inputs.safety_factor

    media_area = 0.0
    minimum_required_media_area = 0.0
    design_airflow = 0.0
    hcho_efficiency = hcho.single_pass_efficiency if hcho.single_pass_efficiency is not None else 0.25
    supplied_media_area = filt.supplied_media_area_m2

    for _ in range(12):
        particle_effective = particle.single_pass_efficiency * (1.0 - filt.bypass_fraction) * room.mixing_effectiveness
        hcho_effective = max(EPS, hcho_efficiency * (1.0 - filt.bypass_fraction) * room.mixing_effectiveness)

        flow_for_particles = design_required_p / max(particle_effective, EPS)
        flow_for_hcho = design_required_f / hcho_effective
        next_design_airflow = max(flow_for_particles, flow_for_hcho)

        area_by_velocity = next_design_airflow / 3600.0 / filt.media_velocity_limit_m_s
        area_by_pressure = _media_area_required_by_pressure(next_design_airflow, fan, filt, loaded=True)
        next_required_media_area = (
            max(area_by_velocity, area_by_pressure)
            if math.isfinite(area_by_pressure)
            else area_by_velocity
        )
        next_media_area = supplied_media_area if supplied_media_area is not None else next_required_media_area

        next_hcho_efficiency = _formaldehyde_efficiency(hcho, next_design_airflow, next_media_area)
        if (
            abs(next_design_airflow - design_airflow) < 0.01
            and abs(next_media_area - media_area) < 1e-5
            and abs(next_hcho_efficiency - hcho_efficiency) < 1e-5
        ):
            design_airflow = next_design_airflow
            media_area = next_media_area
            minimum_required_media_area = next_required_media_area
            hcho_efficiency = next_hcho_efficiency
            break
        design_airflow = next_design_airflow
        media_area = next_media_area
        minimum_required_media_area = next_required_media_area
        hcho_efficiency = next_hcho_efficiency

    clean_airflow = _actual_airflow(fan, filt, media_area, loaded=False, flow_hint=design_airflow)
    loaded_airflow = _actual_airflow(fan, filt, media_area, loaded=True, flow_hint=design_airflow)
    if supplied_media_area is not None:
        hcho_efficiency = _formaldehyde_efficiency(hcho, loaded_airflow, media_area)

    clean_dp = _system_pressure_drop(fan, filt, clean_airflow, media_area, loaded=False)
    loaded_dp = _system_pressure_drop(fan, filt, loaded_airflow, media_area, loaded=True)
    media_velocity_clean = _media_velocity(clean_airflow, media_area)
    media_velocity_loaded = _media_velocity(loaded_airflow, media_area)
    frontal_area = filt.supplied_frontal_area_m2 if supplied_media_area is not None else media_area / filt.pleat_area_multiplier
    if frontal_area is None:
        frontal_area = media_area / filt.pleat_area_multiplier

    clean_p_cadr = cadr_from_airflow(
        clean_airflow,
        particle.single_pass_efficiency,
        bypass_fraction=filt.bypass_fraction,
        mixing_effectiveness=room.mixing_effectiveness,
    )
    clean_f_cadr = cadr_from_airflow(
        clean_airflow,
        hcho_efficiency,
        bypass_fraction=filt.bypass_fraction,
        mixing_effectiveness=room.mixing_effectiveness,
    )
    loaded_p_cadr = cadr_from_airflow(
        loaded_airflow,
        particle.single_pass_efficiency,
        bypass_fraction=filt.bypass_fraction,
        mixing_effectiveness=room.mixing_effectiveness,
    )
    loaded_f_cadr = cadr_from_airflow(
        loaded_airflow,
        hcho_efficiency,
        bypass_fraction=filt.bypass_fraction,
        mixing_effectiveness=room.mixing_effectiveness,
    )

    p_total_loss = particle.existing_removal_ach + loaded_p_cadr / volume
    f_total_loss = hcho.existing_removal_ach + loaded_f_cadr / volume

    service_life, capture_rate = _formaldehyde_service_life(hcho, clean_airflow, hcho_efficiency, filt)
    available_pressure = _fan_available_pressure(fan, design_airflow)
    required_pressure = _system_pressure_drop(fan, filt, design_airflow, media_area, loaded=True)
    pressure_margin = None if available_pressure is None else available_pressure - required_pressure

    warnings = _warnings(
        required_p=required_p,
        required_f=required_f,
        loaded_p_cadr=loaded_p_cadr,
        loaded_f_cadr=loaded_f_cadr,
        pressure_margin=pressure_margin,
        service_life=service_life,
        hcho=hcho,
        supplied_media_area=supplied_media_area,
        minimum_required_media_area=minimum_required_media_area,
        media_velocity_loaded=media_velocity_loaded,
        media_velocity_limit=filt.media_velocity_limit_m_s,
    )

    return DesignResult(
        room_volume_m3=volume,
        room_floor_area_m2=room.floor_area_m2,
        required_p_cadr_m3h=required_p,
        required_f_cadr_m3h=required_f,
        requirement_basis=requirement_basis,
        design_airflow_m3h=design_airflow,
        required_media_area_m2=media_area,
        minimum_required_media_area_m2=minimum_required_media_area,
        media_area_basis="user-defined fixed media" if supplied_media_area is not None else "sized to requirements",
        frontal_area_m2=frontal_area,
        clean_airflow_m3h=clean_airflow,
        loaded_airflow_m3h=loaded_airflow,
        media_velocity_clean_m_s=media_velocity_clean,
        media_velocity_loaded_m_s=media_velocity_loaded,
        clean_pressure_drop_pa=clean_dp,
        loaded_pressure_drop_pa=loaded_dp,
        fan_available_pressure_at_design_pa=available_pressure,
        pressure_margin_at_design_pa=pressure_margin,
        particle_efficiency_used=particle.single_pass_efficiency,
        formaldehyde_efficiency_used=hcho_efficiency,
        clean_p_cadr_m3h=clean_p_cadr,
        clean_f_cadr_m3h=clean_f_cadr,
        loaded_p_cadr_m3h=loaded_p_cadr,
        loaded_f_cadr_m3h=loaded_f_cadr,
        clean_p_ach=clean_p_cadr / volume,
        clean_f_ach=clean_f_cadr / volume,
        loaded_p_ach=loaded_p_cadr / volume,
        loaded_f_ach=loaded_f_cadr / volume,
        p_time_to_80_percent_reduction_min=time_to_fraction_remaining_min(p_total_loss, 0.2),
        f_time_to_80_percent_reduction_min=time_to_fraction_remaining_min(f_total_loss, 0.2),
        formaldehyde_service_life_h=service_life,
        formaldehyde_capture_rate_mg_h=capture_rate,
        warnings=warnings,
    )


def _formaldehyde_efficiency(spec: FormaldehydeSpec, airflow_m3h: float, media_area_m2: float) -> float:
    if spec.single_pass_efficiency is not None:
        return spec.single_pass_efficiency
    if spec.first_order_rate_s is None or spec.carbon_bed_depth_m <= 0:
        return 0.25
    residence_time_s = spec.carbon_bed_depth_m * spec.bed_porosity / max(_media_velocity(airflow_m3h, media_area_m2), EPS)
    return max(0.0, min(0.999, 1.0 - math.exp(-spec.first_order_rate_s * residence_time_s)))


def _formaldehyde_service_life(
    spec: FormaldehydeSpec,
    airflow_m3h: float,
    efficiency: float,
    filt: FilterSpec,
) -> tuple[float | None, float | None]:
    usable_capacity_mg = spec.carbon_mass_g * spec.capacity_mg_per_g * spec.capacity_utilization
    if usable_capacity_mg <= 0:
        return None, None
    capture_rate_mg_h = (
        airflow_m3h
        * spec.challenge_concentration_ug_m3
        / 1000.0
        * efficiency
        * (1.0 - filt.bypass_fraction)
    )
    if capture_rate_mg_h <= 0:
        return None, None
    return usable_capacity_mg / capture_rate_mg_h, capture_rate_mg_h


def _media_velocity(airflow_m3h: float, media_area_m2: float) -> float:
    return airflow_m3h / 3600.0 / max(media_area_m2, EPS)


def _filter_pressure_drop(filt: FilterSpec, airflow_m3h: float, media_area_m2: float, *, loaded: bool) -> float:
    velocity = _media_velocity(airflow_m3h, media_area_m2)
    clean_dp = filt.pressure_drop_ref_pa * (
        velocity / filt.pressure_drop_ref_velocity_m_s
    ) ** filt.pressure_drop_exponent
    return clean_dp * (filt.loaded_pressure_drop_multiplier if loaded else 1.0)


def _system_pressure_drop(
    fan: FanSpec,
    filt: FilterSpec,
    airflow_m3h: float,
    media_area_m2: float,
    *,
    loaded: bool,
) -> float:
    return fan.system_pressure_pa + _filter_pressure_drop(filt, airflow_m3h, media_area_m2, loaded=loaded)


def _fan_available_pressure(fan: FanSpec, airflow_m3h: float) -> float | None:
    if not fan.has_curve:
        return None
    assert fan.free_airflow_m3h is not None
    assert fan.shutoff_pressure_pa is not None
    if airflow_m3h >= fan.free_airflow_m3h:
        return 0.0
    ratio = max(0.0, airflow_m3h / fan.free_airflow_m3h)
    return fan.shutoff_pressure_pa * (1.0 - ratio**fan.curve_exponent)


def _media_area_required_by_pressure(
    airflow_m3h: float,
    fan: FanSpec,
    filt: FilterSpec,
    *,
    loaded: bool,
) -> float:
    available = _fan_available_pressure(fan, airflow_m3h)
    if available is None:
        return 0.0
    allowable_filter_dp = available - fan.system_pressure_pa
    if allowable_filter_dp <= 0:
        return math.inf
    clean_allowable = allowable_filter_dp / (filt.loaded_pressure_drop_multiplier if loaded else 1.0)
    velocity_allowable = filt.pressure_drop_ref_velocity_m_s * (
        clean_allowable / filt.pressure_drop_ref_pa
    ) ** (1.0 / filt.pressure_drop_exponent)
    if velocity_allowable <= 0:
        return math.inf
    return airflow_m3h / 3600.0 / velocity_allowable


def _actual_airflow(
    fan: FanSpec,
    filt: FilterSpec,
    media_area_m2: float,
    *,
    loaded: bool,
    flow_hint: float,
) -> float:
    if not fan.has_curve:
        assert fan.fixed_airflow_m3h is not None
        return fan.fixed_airflow_m3h
    assert fan.free_airflow_m3h is not None
    low = 0.0
    high = fan.free_airflow_m3h
    for _ in range(80):
        mid = (low + high) / 2.0
        available = _fan_available_pressure(fan, mid)
        required = _system_pressure_drop(fan, filt, mid, media_area_m2, loaded=loaded)
        if available is not None and available >= required:
            low = mid
        else:
            high = mid
    return min(low, flow_hint) if not fan.has_curve else low


def _warnings(
    *,
    required_p: float,
    required_f: float,
    loaded_p_cadr: float,
    loaded_f_cadr: float,
    pressure_margin: float | None,
    service_life: float | None,
    hcho: FormaldehydeSpec,
    supplied_media_area: float | None,
    minimum_required_media_area: float,
    media_velocity_loaded: float,
    media_velocity_limit: float,
) -> tuple[str, ...]:
    warnings: list[str] = []
    if loaded_p_cadr + 1e-6 < required_p:
        warnings.append("Loaded P-CADR is below the unsafed particle requirement.")
    if loaded_f_cadr + 1e-6 < required_f:
        warnings.append("Loaded F-CADR is below the unsafed formaldehyde requirement.")
    if pressure_margin is not None and pressure_margin < 0:
        warnings.append("Fan pressure at design airflow is below loaded-filter pressure demand.")
    if supplied_media_area is not None and supplied_media_area + 1e-6 < minimum_required_media_area:
        warnings.append(
            "User-defined media area is below the calculated area needed to meet the target CADR and pressure limits."
        )
    if supplied_media_area is not None and media_velocity_loaded > media_velocity_limit:
        warnings.append("Loaded media velocity is above the selected filter media velocity limit.")
    if service_life is None:
        warnings.append("Formaldehyde service life was not calculated because sorbent capacity data is incomplete.")
    elif service_life < 720:
        warnings.append("Estimated formaldehyde sorbent life is below 720 operating hours.")
    if hcho.relative_humidity_percent > 70:
        warnings.append("High relative humidity can reduce formaldehyde adsorption capacity; verify with media data.")
    return tuple(warnings)
