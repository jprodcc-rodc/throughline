"""U12 · Embedder backend abstraction.

`BaseEmbedder` is the interface every backend implements; the
`rag_server`'s FastAPI app, the `ingest_qdrant.py` vault ingester, and
any future tools pick up a concrete embedder via `create_embedder()`.

v0.2.0 ships two reference backends:

- `bge-m3`   — local 1024-dim BAAI/bge-m3 via transformers + torch.
              Default for Full-privacy / Local-only missions.
- `openai`  — OpenAI-compatible `text-embedding-3-small` via the
              embeddings API. 1536-dim; reference for the cloud path.

Other backends (nomic-embed, MiniLM, Jina, Voyage…) are intentionally
not implemented in this commit. The registry is the public plug-in
point — downstream users register via `register_embedder(name, ctor)`
and get the same call-site surface.

Design notes:
- Torch / transformers are imported LAZILY inside `BgeM3Embedder.ensure_loaded()`
  so `create_embedder("openai")` doesn't pay the multi-second torch
  import tax.
- `vector_size` is a property of the embedder, not a global constant.
  `ingest_qdrant.py` reads it at collection-create time so the Qdrant
  schema always matches the active model.
- Changing the embedder invalidates the Qdrant collection's stored
  vectors — the ingester's `--rebuild` flag handles this; see
  `scripts/ingest_qdrant.py`.
"""
from __future__ import annotations

import abc
import os
from typing import Callable, Dict, List, Optional


class BaseEmbedder(abc.ABC):
    """Every embedder implements the same three things.

    Implementations MUST return L2-normalised vectors of exactly
    `vector_size` floats so the downstream Qdrant schema and cosine
    arithmetic stay valid.
    """

    name: str = ""
    vector_size: int = 0

    @abc.abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts. Empty list in → empty list out."""

    def ensure_loaded(self) -> None:
        """Optional eager-init hook for backends with heavy startup
        (model download, CUDA warmup). Default is a no-op so
        call-sites can invoke it unconditionally."""


# =========================================================
# BgeM3Embedder — local torch + transformers (the v0.1 default)
# =========================================================

class BgeM3Embedder(BaseEmbedder):
    """Wraps the existing rag_server.py code paths. Imports torch +
    transformers lazily — instantiating this class is free; only
    `ensure_loaded()` / the first `embed()` pays the model-load cost."""

    name = "bge-m3"
    vector_size = 1024

    def __init__(self, model_path: Optional[str] = None,
                  device: Optional[str] = None,
                  max_length: int = 1024) -> None:
        self.model_path = model_path or os.getenv("EMBED_MODEL", "BAAI/bge-m3")
        self.device_override = device
        self.max_length = max_length
        self._tokenizer = None
        self._model = None
        self._torch_device = None

    def ensure_loaded(self) -> None:
        if self._model is not None:
            return
        import torch  # local import; heavy
        from transformers import AutoModel, AutoTokenizer

        def _pick_device() -> "torch.device":
            if self.device_override:
                return torch.device(self.device_override)
            if torch.backends.mps.is_available():
                return torch.device("mps")
            if torch.cuda.is_available():
                return torch.device("cuda")
            return torch.device("cpu")

        self._torch_device = _pick_device()
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        m = AutoModel.from_pretrained(self.model_path, torch_dtype=torch.float16)
        self._model = m.to(self._torch_device).eval()

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        self.ensure_loaded()
        import torch
        import torch.nn.functional as F

        inputs = self._tokenizer(
            texts, max_length=self.max_length, padding=True,
            truncation=True, return_tensors="pt",
        ).to(self._torch_device)
        with torch.no_grad():
            outputs = self._model(**inputs)
            embeddings = outputs.last_hidden_state[:, 0]
            embeddings = F.normalize(embeddings, p=2, dim=1)
        return embeddings.cpu().tolist()


# =========================================================
# OpenAIEmbedder — reference cloud alternate
# =========================================================

class OpenAIEmbedder(BaseEmbedder):
    """Calls the OpenAI-compatible /v1/embeddings endpoint.

    Works with any provider exposing the OpenAI schema — OpenAI
    itself, Azure OpenAI, together.ai, or a local self-hosted TEI
    server. The `base_url` + `api_key` come from env vars so nothing
    is hard-coded.

    Model defaults to `text-embedding-3-small` (1536-dim). Users can
    swap via `OPENAI_EMBED_MODEL`; if they pick a differently-sized
    model they must set `OPENAI_EMBED_DIM` to match so the Qdrant
    collection schema aligns.
    """

    name = "openai"

    def __init__(self, model: Optional[str] = None,
                  base_url: Optional[str] = None,
                  api_key: Optional[str] = None,
                  vector_size: Optional[int] = None) -> None:
        self.model = model or os.getenv("OPENAI_EMBED_MODEL",
                                         "text-embedding-3-small")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL")
                          or "https://api.openai.com/v1").rstrip("/")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.vector_size = int(vector_size or os.getenv("OPENAI_EMBED_DIM")
                                or 1536)

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        import json
        import urllib.request
        url = f"{self.base_url}/embeddings"
        body = json.dumps({"model": self.model, "input": texts}).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        if self.api_key:
            req.add_header("Authorization", f"Bearer {self.api_key}")
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        data = payload.get("data") or []
        return [item["embedding"] for item in data]


# =========================================================
# Registry + factory
# =========================================================

_REGISTRY: Dict[str, Callable[[], BaseEmbedder]] = {
    "bge-m3": BgeM3Embedder,
    "openai": OpenAIEmbedder,
}

# Names that route to the same implementation, either because they
# are aliases for the same model or because v0.2.0 hasn't shipped a
# distinct backend for them yet. Documented here rather than silently
# elsewhere so users reading the registry know what they're getting.
_ALIASES: Dict[str, str] = {
    "nomic":       "bge-m3",   # TODO(v0.3): dedicated Nomic impl
    "minilm":      "bge-m3",   # TODO(v0.3): dedicated MiniLM impl
    "jina":        "openai",   # Jina exposes an OpenAI-compatible endpoint
    "voyage":      "openai",   # ditto for Voyage
    "cohere":      "openai",   # ditto for Cohere embeddings
}


def register_embedder(name: str, ctor: Callable[[], BaseEmbedder]) -> None:
    """Plug-in point for downstream users adding an embedder without
    patching this module."""
    _REGISTRY[name] = ctor


def available_embedders() -> List[str]:
    return sorted(set(_REGISTRY.keys()) | set(_ALIASES.keys()))


def create_embedder(name: Optional[str] = None) -> BaseEmbedder:
    """Resolve `name` (or env var `EMBEDDER`, or default `bge-m3`) to
    a concrete embedder instance. Unknown names raise ValueError with
    a list of knowns — silent fallback would route writes into the
    wrong vector space."""
    chosen = (name or os.getenv("EMBEDDER") or "bge-m3").strip().lower()
    if chosen in _REGISTRY:
        return _REGISTRY[chosen]()
    if chosen in _ALIASES:
        return _REGISTRY[_ALIASES[chosen]]()
    known = ", ".join(available_embedders())
    raise ValueError(
        f"Unknown embedder: {chosen!r}. Known: {known}. "
        f"Register additional backends with register_embedder()."
    )
