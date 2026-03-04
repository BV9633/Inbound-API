import os
import time
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from google.cloud import parametermanager_v1


PARAMETER_KEYS = [
    "DDT_CORS_ORIGIN",
    "DDT_GCP_PROJECT_ID",
    "DDT_DATASET",
    "DDT_BUCKET_NAME",
    "DDT_PDF_BASE_PATH",
    "DDT_INVOICE_TABLE_NAME",
    "DDT_WAYBILL_TABLE_NAME",
    "DDT_CBP_TABLE_NAME",
    "DDT_ROLE_MANAGEMENT_TABLE_NAME",
    "DDT_GRAPH_DOCUMENTS_TIMELINE",
    "DDT_WAYBILL_MINIMUM_CONFIDENCE",
    "DDT_RECENT_DOCUMENTS_AGE",
]


class ParameterManagerReader:
    def __init__(self, project_id: str, location: str = "global", ttl_seconds: int = 300):
        self.project_id = project_id
        self.location = location
        self.ttl_seconds = ttl_seconds
        self.client = parametermanager_v1.ParameterManagerClient()
        self._cache: Dict[str, tuple[float, str]] = {}

    def _name(self, parameter_id: str, version_id: str) -> str:
        return (
            f"projects/{self.project_id}/locations/{self.location}/"
            f"parameters/{parameter_id}/versions/{version_id}"
        )

    def read(self, parameter_id: str, version_id: str = "latest", force: bool = False) -> str:
        cache_key = f"{parameter_id}:{version_id}"
        now = time.time()

        if not force and cache_key in self._cache:
            cached_at, cached_val = self._cache[cache_key]
            if now - cached_at < self.ttl_seconds:
                return cached_val

        name = self._name(parameter_id, version_id)

        resp = self.client.render_parameter_version(request={"name": name})
        raw = resp.rendered_payload or resp.payload.data
        value = raw.decode("utf-8").strip()

        self._cache[cache_key] = (now, value)
        return value

    def read_many(self, keys, version_id: str = "latest", force: bool = False) -> Dict[str, str]:
        out = {}
        for k in keys:
            out[k] = self.read(k, version_id=version_id, force=force)
        return out


def _coerce_types(values: Dict[str, str]) -> Dict[str, Any]:
    out: Dict[str, Any] = dict(values)

    if "DDT_RECENT_DOCUMENTS_AGE" in out:
        try:
            out["DDT_RECENT_DOCUMENTS_AGE"] = int(out["DDT_RECENT_DOCUMENTS_AGE"])
        except Exception:
            pass

    if "DDT_WAYBILL_MINIMUM_CONFIDENCE" in out:
        try:
            out["DDT_WAYBILL_MINIMUM_CONFIDENCE"] = float(out["DDT_WAYBILL_MINIMUM_CONFIDENCE"])
        except Exception:
            pass

    if "DDT_CORS_ORIGIN" in out:
        v = str(out["DDT_CORS_ORIGIN"]).strip()
        if v:
            out["DDT_CORS_ORIGIN"] = [x.strip() for x in v.split(",") if x.strip()]
        else:
            out["DDT_CORS_ORIGIN"] = []

    return out


app = FastAPI(title="FastAPI + GCP Parameter Manager")


GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
GCP_PM_LOCATION = os.getenv("GCP_PM_LOCATION", "global")
GCP_PM_VERSION = os.getenv("GCP_PM_VERSION", "latest")
GCP_PM_TTL_SECONDS = int(os.getenv("GCP_PM_TTL_SECONDS", "300"))

_reader: Optional[ParameterManagerReader] = None


@app.on_event("startup")
def load_from_parameter_manager():
    global _reader

    if not GCP_PROJECT_ID:
        raise RuntimeError("Missing env var: GCP_PROJECT_ID")

    _reader = ParameterManagerReader(
        project_id=GCP_PROJECT_ID,
        location=GCP_PM_LOCATION,
        ttl_seconds=GCP_PM_TTL_SECONDS,
    )

    raw = _reader.read_many(PARAMETER_KEYS, version_id=GCP_PM_VERSION, force=True)
    app.state.config = _coerce_types(raw)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/config/keys")
def config_keys():
    cfg = getattr(app.state, "config", None)
    if not cfg:
        raise HTTPException(status_code=500, detail="Config not loaded")
    return {"keys": sorted(cfg.keys())}


@app.get("/example")
def example_usage():
    cfg = getattr(app.state, "config", None)
    if not cfg:
        raise HTTPException(status_code=500, detail="Config not loaded")

    return {
        "DDT_DATASET": cfg.get("DDT_DATASET"),
        "DDT_BUCKET_NAME": cfg.get("DDT_BUCKET_NAME"),
        "DDT_RECENT_DOCUMENTS_AGE": cfg.get("DDT_RECENT_DOCUMENTS_AGE"),
        "DDT_WAYBILL_MINIMUM_CONFIDENCE": cfg.get("DDT_WAYBILL_MINIMUM_CONFIDENCE"),
    }