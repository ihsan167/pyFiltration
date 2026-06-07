"""Local browser UI for pyFiltration."""

from __future__ import annotations

import json
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .calculations import cadr_from_decay, fit_decay_from_samples, fitted_concentration
from .config import design_inputs_from_mapping
from .design import design_air_purifier

STATIC_DIR = Path(__file__).with_name("static")

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml; charset=utf-8",
}


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), PyFiltrationHandler)
    print(f"pyFiltration UI running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping pyFiltration UI.")
    finally:
        server.server_close()


class PyFiltrationHandler(BaseHTTPRequestHandler):
    server_version = "pyFiltrationUI/0.1"

    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            self._serve_static("index.html")
            return
        if self.path.startswith("/static/"):
            self._serve_static(self.path.removeprefix("/static/"))
            return
        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path not in {"/api/design", "/api/lab-cadr"}:
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return
        try:
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            payload = json.loads(body.decode("utf-8"))
            if self.path == "/api/design":
                inputs = design_inputs_from_mapping(payload)
                result = design_air_purifier(inputs)
                self._send_json({"inputs": asdict(inputs), "result": result.to_dict()})
                return
            self._send_json(_lab_cadr_from_payload(payload))
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _serve_static(self, relative_path: str) -> None:
        path = (STATIC_DIR / relative_path).resolve()
        if STATIC_DIR.resolve() not in path.parents and path != STATIC_DIR.resolve():
            self._send_json({"error": "Invalid path"}, status=HTTPStatus.BAD_REQUEST)
            return
        if not path.exists() or not path.is_file():
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return
        content_type = CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream")
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload: dict[str, Any], *, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)


def _lab_cadr_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    chamber_volume = float(payload["chamber_volume_m3"])
    time_unit = str(payload.get("time_unit", "min"))
    background = float(payload.get("background_concentration", 0.0) or 0.0)
    natural_samples = _coerce_samples(payload["natural_samples"])
    purifier_samples = _coerce_samples(payload["purifier_samples"])
    natural_fit = fit_decay_from_samples(
        natural_samples,
        time_unit=time_unit,
        background_concentration=background,
    )
    purifier_fit = fit_decay_from_samples(
        purifier_samples,
        time_unit=time_unit,
        background_concentration=background,
    )
    cadr = cadr_from_decay(chamber_volume, purifier_fit.rate_per_h, natural_fit.rate_per_h)
    return {
        "chamber_volume_m3": chamber_volume,
        "time_unit": time_unit,
        "background_concentration": background,
        "natural_decay_per_h": natural_fit.rate_per_h,
        "purifier_decay_per_h": purifier_fit.rate_per_h,
        "net_decay_per_h": max(0.0, purifier_fit.rate_per_h - natural_fit.rate_per_h),
        "cadr_m3h": cadr,
        "natural_fit": _fit_payload(natural_fit),
        "purifier_fit": _fit_payload(purifier_fit),
        "warnings": _lab_cadr_warnings(cadr, natural_fit.r_squared, purifier_fit.r_squared),
    }


def _coerce_samples(values: Any) -> list[tuple[float, float]]:
    if not isinstance(values, list):
        raise ValueError("samples must be a list of [time, concentration] pairs")
    samples: list[tuple[float, float]] = []
    for item in values:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError("each sample must be [time, concentration]")
        samples.append((float(item[0]), float(item[1])))
    return samples


def _fit_payload(fit: Any) -> dict[str, Any]:
    return {
        "decay_per_h": fit.rate_per_h,
        "slope_per_time_unit": fit.slope_per_time_unit,
        "intercept": fit.intercept,
        "r_squared": fit.r_squared,
        "samples": [
            {
                "time": time_value,
                "concentration": concentration,
                "fit": fitted_concentration(fit, time_value),
            }
            for time_value, concentration in fit.adjusted_samples
        ],
    }


def _lab_cadr_warnings(cadr: float, natural_r2: float, purifier_r2: float) -> list[str]:
    warnings: list[str] = []
    if cadr <= 0:
        warnings.append("Purifier decay is not above natural decay, so measured CADR is zero.")
    if natural_r2 < 0.95 or purifier_r2 < 0.95:
        warnings.append("Decay fit R2 is below 0.95; inspect the sample data and test mixing.")
    return warnings
