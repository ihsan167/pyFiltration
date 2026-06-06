# pyFiltration

Engineering calculator for sizing home air-purifier filters and estimating:

- P-CADR: particulate clean air delivery rate, including PM2.5-style estimates.
- F-CADR: formaldehyde clean air delivery rate for gas-phase media.
- Filter media area, frontal area, face velocity, pressure drop, fan margin, service-life indicators, and room decay behavior.

The project is designed for engineers who need transparent assumptions, editable inputs, and plots suitable for design review.

## What It Calculates

The calculator has two complementary modes:

1. Design estimate from airflow and filter data:
   - room volume and target clean ACH
   - continuous pollutant source targets
   - particle and formaldehyde single-pass efficiency
   - bypass leakage
   - mixing effectiveness
   - fan curve
   - pressure drop versus media velocity
   - clean and loaded filter states
   - activated-carbon mass and usable formaldehyde capacity

2. Lab-style CADR from decay measurements:
   - natural decay rate
   - decay rate with purifier running
   - chamber volume
   - CADR = chamber volume times the purifier-attributed decay rate

## Engineering Basis

CADR is commonly measured from decay-rate tests and is often approximated for design as airflow multiplied by single-pass removal efficiency. This repository keeps those paths separate:

- Use measured decay data when you have chamber or room test data.
- Use design estimates when sizing filter area, fan pressure capability, and sorbent media before a prototype exists.

See [docs/engineering_basis.md](docs/engineering_basis.md) for equations, assumptions, and references.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

For development and tests:

```powershell
python -m pip install -e ".[dev]"
```

## Run The Example

```powershell
pyfiltration design examples/home_air_purifier.json --out reports/example
```

The command writes:

- `summary.json`
- `summary.md`
- `cadr_breakdown.svg`
- `fan_pressure_curve.svg`
- `filter_area_sensitivity.svg`
- `room_decay.svg`
- `formaldehyde_capacity.svg`

You can also run the module directly:

```powershell
python -m pyfiltration.cli design examples/home_air_purifier.json --out reports/example
```

## Example Python API

```python
from pyfiltration.config import load_design_config
from pyfiltration.design import design_air_purifier

inputs = load_design_config("examples/home_air_purifier.json")
result = design_air_purifier(inputs)

print(result.loaded_p_cadr_m3h)
print(result.loaded_f_cadr_m3h)
print(result.required_media_area_m2)
```

## Lab CADR From Decay Data

```python
from pyfiltration.calculations import cadr_from_decay

p_cadr = cadr_from_decay(
    chamber_volume_m3=28.5,
    total_decay_per_h=5.2,
    natural_decay_per_h=0.7,
)
```

## Notes

This is an engineering design and analysis tool, not a product certification claim. Formal CADR labels should be based on the applicable laboratory standard and accredited test data.
