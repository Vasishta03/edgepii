from __future__ import annotations

import gc
import sys
import json
import time
import argparse
import resource
import mimetypes
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .demo import LocalFilter
from .experiment import ROOT

WEB_ROOT = Path(__file__).with_name("web")

MAX_TEXT_LENGTH = 20_000
MODEL_SPECS = {
    "minilm": {
        "label": "MiniLM",
        "detector": "minilm-capid-pilot-s42",
        "relevance": "minilm-relevance-balanced-pilot-s42",
        "threshold": 0.9709891080856324,
        "capid_f1": 0.504,
        "median_ms": 345,
        "peak_ram_mib": 585,
        "summary": "Fastest option with weaker CAPID detection, especially on long contexts.",
    },
    "distilbert": {
        "label": "DistilBERT",
        "detector": "distilbert-capid-pilot-s42",
        "relevance": "distilbert-relevance-balanced-pilot-s42",
        "threshold": 0.9755385518074037,
        "capid_f1": 0.729,
        "median_ms": 734,
        "peak_ram_mib": 870,
        "summary": "Best measured balance of detection quality, stability, and local cost.",
    },
    "bert": {
        "label": "BERT",
        "detector": "bert-capid-pilot-s42",
        "relevance": "bert-relevance-balanced-pilot-s42",
        "threshold": 0.8679852485656739,
        "capid_f1": 0.771,
        "median_ms": 1424,
        "peak_ram_mib": 1192,
        "summary": "Strongest CAPID detector with the highest latency and memory use.",
    },
}


def public_model_specs() -> dict:
    return {
        key: {name: value for name, value in spec.items() if name not in {"detector", "relevance"}}
        for key, spec in MODEL_SPECS.items()
    }


def current_rss_mib() -> float:
    status = Path("/proc/self/status")

    if status.exists():
        for line in status.read_text().splitlines():
            if line.startswith("VmRSS:"):
                return float(line.split()[1]) / 1024
            
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return float(value / 1024 if sys.platform != "darwin" else value / 2**20)


def validate_request(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object")
    
    model = payload.get("model", "distilbert")
    if model not in MODEL_SPECS:
        raise ValueError("Unknown model")
    
    context = payload.get("context", "")
    if not isinstance(context, str):
        raise ValueError("Context and question must be text")
    
    context = context.strip()
    if not context:
        raise ValueError("Enter a context to analyze")
    if len(context) > MAX_TEXT_LENGTH:
        raise ValueError(f"Context and question must each be at most {MAX_TEXT_LENGTH:,} characters")
    
    policy = payload.get("policy", "mask-all")
    if policy not in {"mask-all", "context-aware"}:
        raise ValueError("Unknown masking policy")
    
    try:
        threshold = float(payload.get("threshold", MODEL_SPECS[model]["threshold"]))
    except (TypeError, ValueError) as exc:
        raise ValueError("Threshold must be a number") from exc
    if not 0 <= threshold <= 1:
        raise ValueError("Threshold must be between 0 and 1")
    
    return {
        "model": model,
        "context": context,
        "policy": policy,
        "threshold": threshold,
    }


class ModelManager:
    def __init__(self) -> None:
        self._key: str | None = None
        self._filter: LocalFilter | None = None
        self._lock = threading.Lock()

    def analyze(self, request: dict) -> dict:
        with self._lock:
            model_key = request["model"]

            load_started = time.perf_counter()
            loaded_now = self._key != model_key or self._filter is None

            if loaded_now:
                self._filter = None
                self._key = None
                gc.collect()
                spec = MODEL_SPECS[model_key]

                detector = ROOT / "artifacts" / "runs" / spec["detector"] / "checkpoint"
                relevance = ROOT / "artifacts" / "runs" / spec["relevance"] / "checkpoint"

                if not detector.exists() or not relevance.exists():
                    raise FileNotFoundError(f"Checkpoint is unavailable for {spec['label']}")
                
                self._filter = LocalFilter(detector, relevance)
                self._key = model_key

            load_ms = (time.perf_counter() - load_started) * 1000

            inference_started = time.perf_counter()
            output = self._filter.filter(request["context"], request["policy"], request["threshold"])
            inference_ms = (time.perf_counter() - inference_started) * 1000

        original = request["context"]
        for span in output["spans"]:
            span["value"] = original[span["start"] : span["end"]]

        output.update(
            model=model_key,
            model_label=MODEL_SPECS[model_key]["label"],
            threshold=request["threshold"],
            load_ms=load_ms,
            inference_ms=inference_ms,
            loaded_now=loaded_now,
            protected_prompt=f"Context:\n{output['text']}",
        )
        return output

    def status(self) -> dict:
        with self._lock:
            return {"ram_mib": round(current_rss_mib(), 1), "loaded_model": self._key}


class EdgePIIHandler(BaseHTTPRequestHandler):
    manager: ModelManager
    server_version = "EdgePII/0.1"

    def log_message(self, format: str, *args) -> None:
        safe_args = args[:3]
        super().log_message(format, *safe_args)

    def _json(self, data: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")

        self.send_response(status)

        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
        self.end_headers()

        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path == "/api/models":
            self._json({"models": public_model_specs(), "default": "distilbert"})
            return
        
        if path == "/api/health":
            self._json({"status": "ready", **self.manager.status()})
            return
        
        asset = "index.html" if path == "/" else path.lstrip("/")
        if asset not in {"index.html", "styles.css", "app.js", "favicon.svg"}:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        
        file_path = WEB_ROOT / asset
        if not file_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        
        body = file_path.read_bytes()
        content_type = (mimetypes.guess_type(file_path.name)[0] or "application/octet-stream")

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
        )
        self.end_headers()

        self.wfile.write(body)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/analyze":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > 100_000:
                raise ValueError("Invalid request size")
            
            payload = json.loads(self.rfile.read(content_length))
            request = validate_request(payload)
            self._json({"ok": True, "result": self.manager.analyze(request)})

        except (ValueError, json.JSONDecodeError) as exc:
            self._json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except FileNotFoundError as exc:
            self._json({"ok": False, "error": str(exc)}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self._json(
                {"ok": False, "error": "Analysis failed. Check the local server terminal for details."}, HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            print(f"Analysis failed: {type(exc).__name__}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local EdgePII web interface")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--open", action="store_true", help="Open the interface in the default browser")
    args = parser.parse_args()

    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    
    EdgePIIHandler.manager = ModelManager()
    server = ThreadingHTTPServer((args.host, args.port), EdgePIIHandler)

    url = f"http://{args.host}:{args.port}"
    print(f"EdgePII GUI running at {url}")
    print("Prompts stay on this computer and are not written to disk.")

    if args.open:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping EdgePII GUI")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
