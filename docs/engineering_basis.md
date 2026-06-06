# Engineering Basis

This repository estimates air-purifier sizing with explicit assumptions. It is intended for design studies, prototype screening, and engineering reports. It does not replace certified laboratory testing.

## CADR From Decay Tests

For a well-mixed chamber or room:

```text
CADR = V * (k_total - k_natural)
```

Where:

- `CADR` is the clean air delivery rate.
- `V` is chamber volume.
- `k_total` is the measured first-order decay rate with the purifier running.
- `k_natural` is the natural decay rate without the purifier.

The code uses `m3/h` internally. If decay rates are fitted from concentration samples in `1/min`, they are converted to `1/h`.

## Design CADR Estimate

For early sizing:

```text
P-CADR = Q * eta_p * (1 - bypass) * mixing
F-CADR = Q * eta_f * (1 - bypass) * mixing
```

Where:

- `Q` is actual airflow through the filter.
- `eta_p` is particle single-pass efficiency at the design particle size or range.
- `eta_f` is formaldehyde single-pass efficiency at the design concentration, humidity, temperature, and media condition.
- `bypass` is the fraction of flow that avoids the filter media.
- `mixing` is a room/purifier placement effectiveness factor.

For particulates, use measured filter efficiency at the relevant media velocity when available. For PM2.5-style calculations from smoke and dust CADR:

```text
PM2.5 CADR = sqrt(smoke CADR * dust CADR)
```

## Required CADR

For a target clean-air change rate:

```text
required CADR = room volume * max(target clean ACH - existing removal ACH, 0)
```

For continuous source control:

```text
required CADR = (source + ventilation * outdoor concentration) / target concentration
                - ventilation
                - natural_loss_ach * room volume
```

The calculator uses the larger of the ACH-based and concentration-based requirements when both are provided.

## Filter Area

Media area is sized from the controlling constraint:

```text
area_by_velocity = airflow / media_velocity_limit
```

Pressure drop is scaled with a power law:

```text
delta_p = delta_p_ref * (media_velocity / velocity_ref) ^ exponent
```

If a fan curve is provided, the required media area is also checked against available fan pressure at the design airflow. The loaded-filter multiplier is applied to verify end-of-life performance.

When a fixed filter size is supplied, the calculator does not increase the media area. It evaluates the supplied area instead:

```text
media area = fixed media area
```

or, when panel dimensions are supplied:

```text
media area = frontal width * frontal height * pleat area multiplier
```

The resulting pressure drop is solved against the fan curve to estimate clean and loaded airflow. CADR is then calculated from the delivered airflow, not from the target airflow.

## Formaldehyde Capacity

F-CADR is an initial or current performance value. Sorbent media can lose capacity as it loads. The service-life estimate is:

```text
usable capacity = carbon mass * capacity per gram * utilization factor
capture rate = airflow * challenge concentration * formaldehyde efficiency
service life = usable capacity / capture rate
```

This is intentionally conservative and should be replaced with media supplier breakthrough data when available.

## Key Parameters To Document

- Room length, width, height, and volume
- Target clean ACH for particles and formaldehyde
- Indoor concentration target and continuous source rate, if known
- Ventilation flow and outdoor concentration
- Natural particle deposition or gas loss rate
- Particle efficiency versus particle size and media velocity
- Formaldehyde efficiency versus concentration, RH, temperature, and aging
- Filter bypass leakage
- Filter media velocity limit
- Fixed media area, or frontal width and height
- Pleat area multiplier
- Clean and loaded pressure drop
- Fan free airflow, shutoff pressure, and system losses
- Carbon mass, capacity, utilization, and replacement interval

## References

- U.S. DOE and eCFR Appendix FF reference AHAM AC-1-2020 and AHAM AC-7-2022 for room air-cleaner CADR and energy test procedures.
- The DOE air-cleaner test-procedure documents describe PM2.5 CADR as a geometric average of smoke and dust CADR.
- GB/T 18801-2022 defines CADR for particulate and gaseous pollutants in `m3/h` and includes tests for particulate and gaseous pollutant cleaning.
- NIST has published work using CADR for chemical and particle removal, while also accounting for air-cleaner byproduct formation.
