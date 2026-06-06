"""Command-line interface for pyFiltration."""

from __future__ import annotations

import argparse
import json
import webbrowser
from pathlib import Path

from .calculations import cadr_from_decay, decay_rate_from_samples
from .config import load_design_config
from .design import design_air_purifier
from .report import write_summary_files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pyfiltration")
    subparsers = parser.add_subparsers(dest="command", required=True)

    design_parser = subparsers.add_parser("design", help="Run purifier design sizing from a config file.")
    design_parser.add_argument("config", type=Path)
    design_parser.add_argument("--out", type=Path, default=Path("reports/design"))
    design_parser.add_argument("--no-plots", action="store_true")

    lab_parser = subparsers.add_parser("lab-cadr", help="Calculate CADR from decay-rate data.")
    lab_parser.add_argument("--volume-m3", type=float, required=True)
    lab_parser.add_argument("--natural-decay-h", type=float)
    lab_parser.add_argument("--total-decay-h", type=float)
    lab_parser.add_argument("--natural-samples", type=Path, help="JSON list of [time, concentration] samples.")
    lab_parser.add_argument("--total-samples", type=Path, help="JSON list of [time, concentration] samples.")
    lab_parser.add_argument("--time-unit", choices=["s", "min", "h"], default="min")
    lab_parser.add_argument("--background", type=float, default=0.0)

    ui_parser = subparsers.add_parser("ui", help="Run the local browser UI.")
    ui_parser.add_argument("--host", default="127.0.0.1")
    ui_parser.add_argument("--port", type=int, default=8000)
    ui_parser.add_argument("--open", action="store_true", help="Open the UI in the default browser.")

    args = parser.parse_args(argv)
    if args.command == "design":
        return _run_design(args)
    if args.command == "lab-cadr":
        return _run_lab_cadr(args)
    if args.command == "ui":
        return _run_ui(args)
    parser.error("unknown command")
    return 2


def _run_design(args: argparse.Namespace) -> int:
    inputs = load_design_config(args.config)
    result = design_air_purifier(inputs)
    json_path, md_path = write_summary_files(inputs, result, args.out)
    plot_paths = []
    if not args.no_plots:
        from .visualization import write_plots

        plot_paths = write_plots(inputs, result, args.out)

    print(f"Room: {inputs.room.name}")
    print(f"Required P-CADR: {result.required_p_cadr_m3h:.1f} m3/h")
    print(f"Loaded P-CADR:   {result.loaded_p_cadr_m3h:.1f} m3/h")
    print(f"Required F-CADR: {result.required_f_cadr_m3h:.1f} m3/h")
    print(f"Loaded F-CADR:   {result.loaded_f_cadr_m3h:.1f} m3/h")
    print(f"Media basis:     {result.media_area_basis}")
    print(f"Media area used: {result.required_media_area_m2:.3f} m2")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    for plot_path in plot_paths:
        print(f"Wrote {plot_path}")
    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"- {warning}")
    return 0


def _run_lab_cadr(args: argparse.Namespace) -> int:
    if args.natural_samples and args.total_samples:
        natural_samples = _read_samples(args.natural_samples)
        total_samples = _read_samples(args.total_samples)
        natural_decay = decay_rate_from_samples(
            natural_samples,
            time_unit=args.time_unit,
            background_concentration=args.background,
        )
        total_decay = decay_rate_from_samples(
            total_samples,
            time_unit=args.time_unit,
            background_concentration=args.background,
        )
    elif args.natural_decay_h is not None and args.total_decay_h is not None:
        natural_decay = args.natural_decay_h
        total_decay = args.total_decay_h
    else:
        raise SystemExit("provide either decay rates or both natural and total sample files")

    cadr = cadr_from_decay(args.volume_m3, total_decay, natural_decay)
    print(f"Natural decay: {natural_decay:.4f} 1/h")
    print(f"Total decay:   {total_decay:.4f} 1/h")
    print(f"CADR:          {cadr:.2f} m3/h")
    return 0


def _run_ui(args: argparse.Namespace) -> int:
    from .webapp import run_server

    url = f"http://{args.host}:{args.port}"
    if args.open:
        webbrowser.open(url)
    run_server(host=args.host, port=args.port)
    return 0


def _read_samples(path: Path) -> list[tuple[float, float]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("sample file must contain a JSON list")
    samples: list[tuple[float, float]] = []
    for item in data:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError("each sample must be [time, concentration]")
        samples.append((float(item[0]), float(item[1])))
    return samples


if __name__ == "__main__":
    raise SystemExit(main())
