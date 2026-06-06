"""Unit conversion helpers."""

M3H_PER_CFM = 1.69901082
CFM_PER_M3H = 1.0 / M3H_PER_CFM
FT2_PER_M2 = 10.7639104167
M2_PER_FT2 = 1.0 / FT2_PER_M2


def m3h_to_cfm(value_m3h: float) -> float:
    return value_m3h * CFM_PER_M3H


def cfm_to_m3h(value_cfm: float) -> float:
    return value_cfm * M3H_PER_CFM


def m2_to_ft2(value_m2: float) -> float:
    return value_m2 * FT2_PER_M2


def ft2_to_m2(value_ft2: float) -> float:
    return value_ft2 * M2_PER_FT2
