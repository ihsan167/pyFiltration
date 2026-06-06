"""Data models for purifier design calculations."""

from __future__ import annotations

from dataclasses import asdict, dataclass


def _require_positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value!r}")


def _require_non_negative(name: str, value: float) -> None:
    if value < 0:
        raise ValueError(f"{name} must be non-negative, got {value!r}")


def _require_fraction(name: str, value: float) -> None:
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1, got {value!r}")


@dataclass(frozen=True)
class RoomSpec:
    name: str
    length_m: float
    width_m: float
    height_m: float
    mixing_effectiveness: float = 1.0

    def __post_init__(self) -> None:
        _require_positive("room.length_m", self.length_m)
        _require_positive("room.width_m", self.width_m)
        _require_positive("room.height_m", self.height_m)
        _require_fraction("room.mixing_effectiveness", self.mixing_effectiveness)

    @property
    def floor_area_m2(self) -> float:
        return self.length_m * self.width_m

    @property
    def volume_m3(self) -> float:
        return self.floor_area_m2 * self.height_m


@dataclass(frozen=True)
class ParticleSpec:
    target_clean_ach: float
    single_pass_efficiency: float
    existing_removal_ach: float = 0.0

    def __post_init__(self) -> None:
        _require_positive("particle.target_clean_ach", self.target_clean_ach)
        _require_fraction("particle.single_pass_efficiency", self.single_pass_efficiency)
        _require_non_negative("particle.existing_removal_ach", self.existing_removal_ach)


@dataclass(frozen=True)
class FormaldehydeSpec:
    target_clean_ach: float
    existing_removal_ach: float = 0.0
    target_concentration_ug_m3: float | None = None
    source_generation_ug_h: float = 0.0
    outdoor_concentration_ug_m3: float = 0.0
    ventilation_m3h: float = 0.0
    single_pass_efficiency: float | None = None
    first_order_rate_s: float | None = None
    carbon_bed_depth_m: float = 0.0
    bed_porosity: float = 0.45
    challenge_concentration_ug_m3: float = 80.0
    carbon_mass_g: float = 0.0
    capacity_mg_per_g: float = 0.0
    capacity_utilization: float = 0.5
    temperature_c: float = 25.0
    relative_humidity_percent: float = 50.0

    def __post_init__(self) -> None:
        _require_positive("formaldehyde.target_clean_ach", self.target_clean_ach)
        _require_non_negative("formaldehyde.existing_removal_ach", self.existing_removal_ach)
        _require_non_negative("formaldehyde.source_generation_ug_h", self.source_generation_ug_h)
        _require_non_negative("formaldehyde.outdoor_concentration_ug_m3", self.outdoor_concentration_ug_m3)
        _require_non_negative("formaldehyde.ventilation_m3h", self.ventilation_m3h)
        _require_positive("formaldehyde.challenge_concentration_ug_m3", self.challenge_concentration_ug_m3)
        _require_non_negative("formaldehyde.carbon_mass_g", self.carbon_mass_g)
        _require_non_negative("formaldehyde.capacity_mg_per_g", self.capacity_mg_per_g)
        _require_fraction("formaldehyde.capacity_utilization", self.capacity_utilization)
        _require_fraction("formaldehyde.bed_porosity", self.bed_porosity)
        _require_fraction("formaldehyde.relative_humidity_percent / 100", self.relative_humidity_percent / 100)
        if self.target_concentration_ug_m3 is not None:
            _require_positive("formaldehyde.target_concentration_ug_m3", self.target_concentration_ug_m3)
        if self.single_pass_efficiency is not None:
            _require_fraction("formaldehyde.single_pass_efficiency", self.single_pass_efficiency)
        if self.first_order_rate_s is not None:
            _require_positive("formaldehyde.first_order_rate_s", self.first_order_rate_s)
        _require_non_negative("formaldehyde.carbon_bed_depth_m", self.carbon_bed_depth_m)


@dataclass(frozen=True)
class FilterSpec:
    media_velocity_limit_m_s: float
    pleat_area_multiplier: float = 1.0
    fixed_media_area_m2: float | None = None
    frontal_width_m: float | None = None
    frontal_height_m: float | None = None
    bypass_fraction: float = 0.0
    pressure_drop_ref_pa: float = 50.0
    pressure_drop_ref_velocity_m_s: float = 0.2
    pressure_drop_exponent: float = 1.3
    loaded_pressure_drop_multiplier: float = 1.7

    def __post_init__(self) -> None:
        _require_positive("filter.media_velocity_limit_m_s", self.media_velocity_limit_m_s)
        _require_positive("filter.pleat_area_multiplier", self.pleat_area_multiplier)
        _require_fraction("filter.bypass_fraction", self.bypass_fraction)
        _require_positive("filter.pressure_drop_ref_pa", self.pressure_drop_ref_pa)
        _require_positive("filter.pressure_drop_ref_velocity_m_s", self.pressure_drop_ref_velocity_m_s)
        _require_positive("filter.pressure_drop_exponent", self.pressure_drop_exponent)
        _require_positive("filter.loaded_pressure_drop_multiplier", self.loaded_pressure_drop_multiplier)
        if self.fixed_media_area_m2 is not None:
            _require_positive("filter.fixed_media_area_m2", self.fixed_media_area_m2)
        if self.frontal_width_m is not None:
            _require_positive("filter.frontal_width_m", self.frontal_width_m)
        if self.frontal_height_m is not None:
            _require_positive("filter.frontal_height_m", self.frontal_height_m)
        if (self.frontal_width_m is None) != (self.frontal_height_m is None):
            raise ValueError("filter.frontal_width_m and filter.frontal_height_m must be provided together")

    @property
    def supplied_frontal_area_m2(self) -> float | None:
        if self.frontal_width_m is None or self.frontal_height_m is None:
            if self.fixed_media_area_m2 is None:
                return None
            return self.fixed_media_area_m2 / self.pleat_area_multiplier
        return self.frontal_width_m * self.frontal_height_m

    @property
    def supplied_media_area_m2(self) -> float | None:
        if self.fixed_media_area_m2 is not None:
            return self.fixed_media_area_m2
        if self.supplied_frontal_area_m2 is None:
            return None
        return self.supplied_frontal_area_m2 * self.pleat_area_multiplier


@dataclass(frozen=True)
class FanSpec:
    free_airflow_m3h: float | None = None
    shutoff_pressure_pa: float | None = None
    system_pressure_pa: float = 0.0
    curve_exponent: float = 1.7
    fixed_airflow_m3h: float | None = None
    power_w: float | None = None

    def __post_init__(self) -> None:
        _require_non_negative("fan.system_pressure_pa", self.system_pressure_pa)
        _require_positive("fan.curve_exponent", self.curve_exponent)
        if self.fixed_airflow_m3h is not None:
            _require_positive("fan.fixed_airflow_m3h", self.fixed_airflow_m3h)
        if self.free_airflow_m3h is not None:
            _require_positive("fan.free_airflow_m3h", self.free_airflow_m3h)
        if self.shutoff_pressure_pa is not None:
            _require_positive("fan.shutoff_pressure_pa", self.shutoff_pressure_pa)
        if self.power_w is not None:
            _require_positive("fan.power_w", self.power_w)
        if self.fixed_airflow_m3h is None and (
            self.free_airflow_m3h is None or self.shutoff_pressure_pa is None
        ):
            raise ValueError("fan requires fixed_airflow_m3h or both free_airflow_m3h and shutoff_pressure_pa")

    @property
    def has_curve(self) -> bool:
        return self.fixed_airflow_m3h is None


@dataclass(frozen=True)
class DesignInputs:
    room: RoomSpec
    particle: ParticleSpec
    formaldehyde: FormaldehydeSpec
    filter: FilterSpec
    fan: FanSpec
    safety_factor: float = 1.0

    def __post_init__(self) -> None:
        _require_positive("safety_factor", self.safety_factor)


@dataclass(frozen=True)
class DesignResult:
    room_volume_m3: float
    room_floor_area_m2: float
    required_p_cadr_m3h: float
    required_f_cadr_m3h: float
    design_airflow_m3h: float
    required_media_area_m2: float
    minimum_required_media_area_m2: float
    media_area_basis: str
    frontal_area_m2: float
    clean_airflow_m3h: float
    loaded_airflow_m3h: float
    media_velocity_clean_m_s: float
    media_velocity_loaded_m_s: float
    clean_pressure_drop_pa: float
    loaded_pressure_drop_pa: float
    fan_available_pressure_at_design_pa: float | None
    pressure_margin_at_design_pa: float | None
    particle_efficiency_used: float
    formaldehyde_efficiency_used: float
    clean_p_cadr_m3h: float
    clean_f_cadr_m3h: float
    loaded_p_cadr_m3h: float
    loaded_f_cadr_m3h: float
    clean_p_ach: float
    clean_f_ach: float
    loaded_p_ach: float
    loaded_f_ach: float
    p_time_to_80_percent_reduction_min: float
    f_time_to_80_percent_reduction_min: float
    formaldehyde_service_life_h: float | None
    formaldehyde_capture_rate_mg_h: float | None
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
