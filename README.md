# pyFiltration

Engineering calculator for sizing home air-purifier filters and estimating:

- P-CADR: particulate clean air delivery rate, including PM2.5-style estimates.
- F-CADR: formaldehyde clean air delivery rate for gas-phase media.
- Filter media area, frontal area, face velocity, pressure drop, fan margin, service-life indicators, and room decay behavior.
- Fixed filter media evaluation from known media area, frontal width x height with a multiplier, or frontal width x height with pleat count and pleat depth.

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
   - optional fixed media area, multiplier-based dimensions, or pleat-geometry dimensions for evaluating an existing filter

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

## Run The Local UI

```powershell
python -m pyfiltration.cli ui
```

Then open:

```text
http://127.0.0.1:8000
```

The UI lets you edit room dimensions, particle targets, formaldehyde source and media assumptions, filter pressure drop, fan curve, and safety factor. It calculates P-CADR, F-CADR, media area, pressure margin, ACH, decay time, and formaldehyde service life, then draws engineering charts in the browser.

Use the Filter section in either mode:

- `Size required`: the calculator finds the media area needed to meet the CADR targets.
- `Evaluate filter`: enter frontal width and height in `mm`, then choose either `Multiplier` or `Pleat geometry`. The calculator computes unfolded media area in `mm2` and then estimates airflow, pressure drop, P-CADR, and F-CADR for that actual filter size.

Important geometry terms:

- `Frontal area = frontal width * frontal height`
- `Media area = frontal area * pleat multiplier`
- In `Pleat geometry`, pleat depth increases unfolded media area, not frontal area. The calculator uses pleat count, pitch, pleat depth, pleat length, and usable media factor.
- For a flat filter, pleat multiplier is `1`, so media area equals frontal area.
- Use `Known media area` only when the supplier gives the unfolded filter media area directly. In the browser UI, enter that known area in `mm2`.

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
