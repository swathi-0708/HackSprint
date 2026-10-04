"""Hash + disk cache. One folder per agreement: data/cache/<agreement_id>/."""
import hashlib
import json
from pathlib import Path

from .config import CACHE_DIR


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def agreement_id_for(path) -> str:
    return sha256_file(path)[:12]


def _p(agreement_id: str, name: str, cache_dir: Path = None) -> Path:
    d = (cache_dir or CACHE_DIR) / agreement_id
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{name}.json"


def load(agreement_id: str, name: str, cache_dir: Path = None):
    p = _p(agreement_id, name, cache_dir)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def save(agreement_id: str, name: str, data, cache_dir: Path = None) -> None:
    _p(agreement_id, name, cache_dir).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
