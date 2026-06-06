"""Dependency-free SVG visualizations for engineering reports."""

from __future__ import annotations

import math
from html import escape
from pathlib import Path
from typing import NamedTuple

from .design import _fan_available_pressure, _system_pressure_drop
from .models import DesignInputs, DesignResult

WIDTH = 900
HEIGHT = 540
LEFT = 82
RIGHT = 82
TOP = 64
BOTTOM = 78
PLOT_W = WIDTH - LEFT - RIGHT
PLOT_H = HEIGHT - TOP - BOTTOM


class Series(NamedTuple):
    name: str
    values: list[float]
    color: str
    axis: str = "left"
    dash: str = ""


def write_plots(inputs: DesignInputs, result: DesignResult, output_dir: str | Path) -> list[Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = [
        _plot_cadr_breakdown(result, output / "cadr_breakdown.svg"),
        _plot_fan_pressure(inputs, result, output / "fan_pressure_curve.svg"),
        _plot_area_sensitivity(inputs, result, output / "filter_area_sensitivity.svg"),
        _plot_room_decay(inputs, result, output / "room_decay.svg"),
        _plot_formaldehyde_capacity(inputs, result, output / "formaldehyde_capacity.svg"),
    ]
    return paths


def _plot_cadr_breakdown(result: DesignResult, path: Path) -> Path:
    groups = ["P-CADR", "F-CADR"]
    data = [
        ("Required", "#525252", [result.required_p_cadr_m3h, result.required_f_cadr_m3h]),
        ("Clean filter", "#2f80ed", [result.clean_p_cadr_m3h, result.clean_f_cadr_m3h]),
        ("Loaded filter", "#27ae60", [result.loaded_p_cadr_m3h, result.loaded_f_cadr_m3h]),
    ]
    return _write_grouped_bar_chart(path, "Required vs estimated CADR", groups, data, "CADR (m3/h)")


def _plot_fan_pressure(inputs: DesignInputs, result: DesignResult, path: Path) -> Path:
    fan = inputs.fan
    filt = inputs.filter
    max_flow = fan.free_airflow_m3h if fan.has_curve and fan.free_airflow_m3h else max(result.design_airflow_m3h * 1.4, 1.0)
    x_values = [max_flow * i / 100 for i in range(101)]
    series = [
        Series(
            "Clean system pressure",
            [_system_pressure_drop(fan, filt, q, result.required_media_area_m2, loaded=False) for q in x_values],
            "#2f80ed",
        ),
        Series(
            "Loaded system pressure",
            [_system_pressure_drop(fan, filt, q, result.required_media_area_m2, loaded=True) for q in x_values],
            "#eb5757",
        ),
    ]
    if fan.has_curve:
        series.append(
            Series("Fan available pressure", [_fan_available_pressure(fan, q) or 0.0 for q in x_values], "#111111")
        )
    return _write_line_chart(
        path,
        "Fan and system pressure",
        x_values,
        series,
        "Airflow (m3/h)",
        "Pressure (Pa)",
        markers=[
            (result.clean_airflow_m3h, result.clean_pressure_drop_pa, "#2f80ed", "Clean"),
            (result.loaded_airflow_m3h, result.loaded_pressure_drop_pa, "#eb5757", "Loaded"),
        ],
    )


def _plot_area_sensitivity(inputs: DesignInputs, result: DesignResult, path: Path) -> Path:
    flow = result.design_airflow_m3h
    x_values = [0.08 + i * 0.005 for i in range(65)]
    areas = [flow / 3600.0 / v for v in x_values]
    clean_dp = [
        inputs.filter.pressure_drop_ref_pa
        * (v / inputs.filter.pressure_drop_ref_velocity_m_s) ** inputs.filter.pressure_drop_exponent
        for v in x_values
    ]
    loaded_dp = [dp * inputs.filter.loaded_pressure_drop_multiplier for dp in clean_dp]
    return _write_line_chart(
        path,
        "Filter area and pressure sensitivity",
        x_values,
        [
            Series("Media area", areas, "#2f80ed", "left"),
            Series("Clean filter delta P", clean_dp, "#27ae60", "right"),
            Series("Loaded filter delta P", loaded_dp, "#eb5757", "right", "6 4"),
        ],
        "Media velocity (m/s)",
        "Media area (m2)",
        y2_label="Filter pressure drop (Pa)",
        vlines=[(inputs.filter.media_velocity_limit_m_s, "#525252", "Velocity limit")],
    )


def _plot_room_decay(inputs: DesignInputs, result: DesignResult, path: Path) -> Path:
    volume = result.room_volume_m3
    x_values = [float(i) for i in range(181)]
    p_natural = inputs.particle.existing_removal_ach
    p_total = p_natural + result.loaded_p_cadr_m3h / volume
    f_natural = inputs.formaldehyde.existing_removal_ach
    f_total = f_natural + result.loaded_f_cadr_m3h / volume
    return _write_line_chart(
        path,
        "Well-mixed room decay",
        x_values,
        [
            Series("Particle natural", [math.exp(-p_natural * t / 60) for t in x_values], "#9b9b9b"),
            Series("Particle with purifier", [math.exp(-p_total * t / 60) for t in x_values], "#2f80ed"),
            Series("Formaldehyde natural", [math.exp(-f_natural * t / 60) for t in x_values], "#bdbdbd", "left", "6 4"),
            Series("Formaldehyde with purifier", [math.exp(-f_total * t / 60) for t in x_values], "#27ae60"),
        ],
        "Time (min)",
        "Fraction remaining",
        y_min=0.0,
        y_max=1.0,
        hlines=[(0.2, "#525252", "80 percent reduction")],
    )


def _plot_formaldehyde_capacity(inputs: DesignInputs, result: DesignResult, path: Path) -> Path:
    capacity = (
        inputs.formaldehyde.carbon_mass_g
        * inputs.formaldehyde.capacity_mg_per_g
        * inputs.formaldehyde.capacity_utilization
    )
    if result.formaldehyde_capture_rate_mg_h is None or capacity <= 0:
        return _write_message_svg(path, "Formaldehyde sorbent capacity", "Capacity data incomplete")
    life = result.formaldehyde_service_life_h or 0.0
    max_h = max(life * 1.1, 24.0)
    x_values = [max_h * i / 100 for i in range(101)]
    captured = [min(capacity, h * result.formaldehyde_capture_rate_mg_h) for h in x_values]
    remaining = [max(0.0, capacity - value) for value in captured]
    return _write_line_chart(
        path,
        "Formaldehyde sorbent capacity",
        x_values,
        [
            Series("Captured formaldehyde", captured, "#eb5757"),
            Series("Remaining usable capacity", remaining, "#27ae60"),
        ],
        "Operating hours",
        "Mass (mg)",
        vlines=[(life, "#525252", "Estimated service life")],
    )


def _write_grouped_bar_chart(
    path: Path,
    title: str,
    groups: list[str],
    data: list[tuple[str, str, list[float]]],
    y_label: str,
) -> Path:
    max_y = _nice_max(max(max(values) for _, _, values in data))
    parts = _svg_base(title)
    parts.extend(_axes(title, "Metric", y_label, y_max=max_y))

    group_w = PLOT_W / len(groups)
    bar_w = group_w / (len(data) + 1.4)
    for group_index, label in enumerate(groups):
        center = LEFT + group_w * (group_index + 0.5)
        start = center - bar_w * len(data) / 2
        parts.append(_text(center, HEIGHT - 42, label, size=13, anchor="middle"))
        for series_index, (_, color, values) in enumerate(data):
            value = values[group_index]
            x = start + series_index * bar_w
            y = _y(value, 0.0, max_y)
            h = TOP + PLOT_H - y
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w * 0.82:.1f}" height="{h:.1f}" fill="{color}"/>')
            parts.append(_text(x + bar_w * 0.41, y - 6, f"{value:.0f}", size=11, anchor="middle", fill="#333333"))

    parts.extend(_legend([(name, color, "") for name, color, _ in data]))
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def _write_line_chart(
    path: Path,
    title: str,
    x_values: list[float],
    series: list[Series],
    x_label: str,
    y_label: str,
    *,
    y_min: float | None = None,
    y_max: float | None = None,
    y2_label: str | None = None,
    hlines: list[tuple[float, str, str]] | None = None,
    vlines: list[tuple[float, str, str]] | None = None,
    markers: list[tuple[float, float, str, str]] | None = None,
) -> Path:
    left_values = [value for item in series if item.axis == "left" for value in item.values]
    right_values = [value for item in series if item.axis == "right" for value in item.values]
    x_min = min(x_values)
    x_max = max(x_values)
    left_min = 0.0 if y_min is None else y_min
    left_max = _nice_max(max(left_values) if y_max is None else y_max)
    right_min = 0.0
    right_max = _nice_max(max(right_values)) if right_values else left_max

    parts = _svg_base(title)
    parts.extend(_axes(title, x_label, y_label, y_max=left_max, y_min=left_min, y2_label=y2_label, y2_max=right_max))

    for value, color, label in hlines or []:
        y = _y(value, left_min, left_max)
        parts.append(f'<line x1="{LEFT}" x2="{LEFT + PLOT_W}" y1="{y:.1f}" y2="{y:.1f}" stroke="{color}" stroke-dasharray="3 4"/>')
        parts.append(_text(LEFT + PLOT_W - 4, y - 6, label, size=11, anchor="end", fill=color))

    for value, color, label in vlines or []:
        x = _x(value, x_min, x_max)
        parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{TOP}" y2="{TOP + PLOT_H}" stroke="{color}" stroke-dasharray="4 4"/>')
        parts.append(_text(x + 6, TOP + 16, label, size=11, fill=color))

    for item in series:
        axis_min, axis_max = (right_min, right_max) if item.axis == "right" else (left_min, left_max)
        points = [
            f"{_x(x, x_min, x_max):.1f},{_y(y, axis_min, axis_max):.1f}"
            for x, y in zip(x_values, item.values, strict=True)
        ]
        dash = f' stroke-dasharray="{item.dash}"' if item.dash else ""
        parts.append(
            f'<polyline points="{" ".join(points)}" fill="none" stroke="{item.color}" stroke-width="2.5"{dash}/>'
        )

    for x_value, y_value, color, label in markers or []:
        x = _x(x_value, x_min, x_max)
        y = _y(y_value, left_min, left_max)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}" stroke="#ffffff" stroke-width="1.5"/>')
        parts.append(_text(x + 8, y - 8, label, size=11, fill=color))

    parts.extend(_x_ticks(x_min, x_max))
    parts.extend(_legend([(item.name, item.color, item.dash) for item in series]))
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def _svg_base(title: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        _text(WIDTH / 2, 30, title, size=20, anchor="middle", weight="700"),
    ]


def _axes(
    title: str,
    x_label: str,
    y_label: str,
    *,
    y_max: float,
    y_min: float = 0.0,
    y2_label: str | None = None,
    y2_max: float | None = None,
) -> list[str]:
    parts: list[str] = []
    parts.append(f'<rect x="{LEFT}" y="{TOP}" width="{PLOT_W}" height="{PLOT_H}" fill="#fbfbfb" stroke="#d9d9d9"/>')
    for i in range(6):
        value = y_min + (y_max - y_min) * i / 5
        y = _y(value, y_min, y_max)
        parts.append(f'<line x1="{LEFT}" x2="{LEFT + PLOT_W}" y1="{y:.1f}" y2="{y:.1f}" stroke="#e6e6e6"/>')
        parts.append(_text(LEFT - 10, y + 4, _fmt(value), size=11, anchor="end", fill="#555555"))
        if y2_label and y2_max is not None:
            value2 = y2_max * i / 5
            parts.append(_text(LEFT + PLOT_W + 10, y + 4, _fmt(value2), size=11, fill="#555555"))
    parts.append(f'<line x1="{LEFT}" x2="{LEFT}" y1="{TOP}" y2="{TOP + PLOT_H}" stroke="#777777"/>')
    parts.append(f'<line x1="{LEFT}" x2="{LEFT + PLOT_W}" y1="{TOP + PLOT_H}" y2="{TOP + PLOT_H}" stroke="#777777"/>')
    parts.append(_text(WIDTH / 2, HEIGHT - 16, x_label, size=13, anchor="middle", fill="#333333"))
    parts.append(
        f'<text x="22" y="{TOP + PLOT_H / 2:.1f}" transform="rotate(-90 22 {TOP + PLOT_H / 2:.1f})" '
        f'font-family="Arial, sans-serif" font-size="13" fill="#333333" text-anchor="middle">{escape(y_label)}</text>'
    )
    if y2_label:
        parts.append(
            f'<text x="{WIDTH - 18}" y="{TOP + PLOT_H / 2:.1f}" transform="rotate(90 {WIDTH - 18} {TOP + PLOT_H / 2:.1f})" '
            f'font-family="Arial, sans-serif" font-size="13" fill="#333333" text-anchor="middle">{escape(y2_label)}</text>'
        )
    return parts


def _x_ticks(x_min: float, x_max: float) -> list[str]:
    parts: list[str] = []
    for i in range(6):
        value = x_min + (x_max - x_min) * i / 5
        x = _x(value, x_min, x_max)
        parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{TOP + PLOT_H}" y2="{TOP + PLOT_H + 5}" stroke="#777777"/>')
        parts.append(_text(x, TOP + PLOT_H + 22, _fmt(value), size=11, anchor="middle", fill="#555555"))
    return parts


def _legend(items: list[tuple[str, str, str]]) -> list[str]:
    parts: list[str] = []
    x = LEFT + PLOT_W - 210
    y = TOP + 12
    width = 198
    height = 22 * len(items) + 14
    parts.append(f'<rect x="{x - 10}" y="{y - 12}" width="{width}" height="{height}" fill="#ffffff" stroke="#d9d9d9"/>')
    for index, (name, color, dash) in enumerate(items):
        yy = y + index * 22
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(f'<line x1="{x}" x2="{x + 24}" y1="{yy}" y2="{yy}" stroke="{color}" stroke-width="3"{dash_attr}/>')
        parts.append(_text(x + 32, yy + 4, name, size=11, fill="#333333"))
    return parts


def _write_message_svg(path: Path, title: str, message: str) -> Path:
    parts = _svg_base(title)
    parts.append(_text(WIDTH / 2, HEIGHT / 2, message, size=18, anchor="middle", fill="#555555"))
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def _text(
    x: float,
    y: float,
    content: str,
    *,
    size: int = 12,
    anchor: str = "start",
    fill: str = "#111111",
    weight: str = "400",
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, sans-serif" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(content)}</text>'
    )


def _x(value: float, x_min: float, x_max: float) -> float:
    if x_max == x_min:
        return LEFT
    return LEFT + (value - x_min) / (x_max - x_min) * PLOT_W


def _y(value: float, y_min: float, y_max: float) -> float:
    if y_max == y_min:
        return TOP + PLOT_H
    return TOP + PLOT_H - (value - y_min) / (y_max - y_min) * PLOT_H


def _nice_max(value: float) -> float:
    if value <= 0:
        return 1.0
    exponent = math.floor(math.log10(value))
    base = 10**exponent
    scaled = value / base
    if scaled <= 1:
        nice = 1
    elif scaled <= 2:
        nice = 2
    elif scaled <= 5:
        nice = 5
    else:
        nice = 10
    return nice * base


def _fmt(value: float) -> str:
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}".rstrip("0").rstrip(".")
