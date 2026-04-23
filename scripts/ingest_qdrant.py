"""Ingest an Obsidian-style vault into Qdrant via a bge-m3 embedding endpoint.

Scans the vault, reads frontmatter + body, embeds the first ~2000 chars with
bge-m3 through the RAG server (OpenAI-compatible /v1/embeddings), and upserts
one point per note into the configured Qdrant collection.

=== CRITICAL: forward-slash path normalisation ===

Point IDs are derived from the note's relative path via md5. If the same
vault is ingested from both Windows (backslash separators) and macOS/Linux
(forward-slash) without normalisation, you get **two** points per note with
different IDs -> duplicate retrieval, double-sized collection, inconsistent
rerank results.

We always normalise paths with `.replace(os.sep, "/")` before hashing AND
before writing the `path` payload field. This MUST be preserved on any
platform. See `make_point_id()` and `read_note()` below.

=== Configuration (env vars) ===

    VAULT_PATH                   Path to the Obsidian vault root (required)
    RAG_EMBED_URL                OpenAI-compatible embedding endpoint.
                                 Default: http://localhost:8000/v1
    QDRANT_URL                   Default: http://localhost:6333
    RAG_COLLECTION               Qdrant collection name. Default: obsidian_notes
    INGEST_VECTOR_SIZE           Embedding dimensionality. Default: 1024 (bge-m3)
    INGEST_BATCH_SIZE            Embedding + upsert batch size. Default: 20
    INGEST_INCLUDE                JSON list of top-level folders to scan.
                                 Defaults to the first-digit pattern [1-9]0_*
                                 (common in Johnny-Decimal layouts).
    INGEST_EXTRA_WHITELIST       JSON list of extra paths (relative to vault)
                                 to also scan. Default: [].
"""

import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package is required. pip install openai", file=sys.stderr)
    sys.exit(1)


# ==========================================
# Configuration
# ==========================================

VAULT = os.getenv("VAULT_PATH", "").strip()
if not VAULT:
    print("ERROR: VAULT_PATH env var is required (absolute path to vault root).", file=sys.stderr)
    sys.exit(2)

EMBED_URL = os.getenv("RAG_EMBED_URL", "http://localhost:8000/v1")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("RAG_COLLECTION", "obsidian_notes")
BATCH_SIZE = int(os.getenv("INGEST_BATCH_SIZE", "20"))


def _resolve_vector_size() -> int:
    """U12 — let the active embedder declare its dimensionality.

    Precedence:
      1. INGEST_VECTOR_SIZE env var (explicit override wins)
      2. Active EMBEDDER's declared vector_size (via create_embedder)
      3. 1024 (bge-m3 default)
    """
    override = os.getenv("INGEST_VECTOR_SIZE", "").strip()
    if override:
        try:
            return int(override)
        except ValueError:
            pass
    try:
        # Local import so we don't pull torch in unless we actually
        # need to ask an embedder for its size.
        from rag_server.embedders import create_embedder  # type: ignore
        return create_embedder().vector_size or 1024
    except Exception as e:
        print(f"[ingest] embedder size lookup failed, defaulting to 1024: {e}",
              file=sys.stderr)
        return 1024


VECTOR_SIZE = _resolve_vector_size()


def _parse_json_list(env_name: str, default):
    raw = os.getenv(env_name, "").strip()
    if not raw:
        return default
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass
    print(f"WARN: {env_name} is not valid JSON list; using default.", file=sys.stderr)
    return default


# Top-level folder scan rules. Default: any folder whose name starts with
# [1-9]0_ — this is the Johnny-Decimal convention used by the original vault.
# Override by exporting INGEST_INCLUDE as a JSON list of exact folder names
# or regex patterns (prefix `re:` for regex).
INCLUDE_PATTERNS = _parse_json_list("INGEST_INCLUDE", ["re:^[1-9]0_"])

# Extra whitelist: relative paths inside the vault that should also be
# scanned even if they don't match INCLUDE_PATTERNS. Example use case:
# an inbox folder holding a small set of curated overview notes you want
# in the retrieval index.
EXTRA_WHITELIST = _parse_json_list("INGEST_EXTRA_WHITELIST", [])


embed_client = OpenAI(api_key="not-needed", base_url=EMBED_URL, timeout=120)


def qdrant_request(method, path, data=None):
    url = QDRANT_URL + path
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"Qdrant error: {e.code} {err_body[:200]}")
        return None
    except Exception as e:
        print(f"Qdrant error: {e}")
        return None


def create_collection():
    result = qdrant_request("GET", f"/collections/{COLLECTION}")
    if result and result.get("status") == "ok":
        print(f"Collection '{COLLECTION}' already exists.")
        return True

    result = qdrant_request("PUT", f"/collections/{COLLECTION}", {
        "vectors": {
            "size": VECTOR_SIZE,
            "distance": "Cosine",
        }
    })
    if result and result.get("status") == "ok":
        print(f"Collection '{COLLECTION}' created.")
        return True
    print("Failed to create collection!")
    return False


def _folder_matches(name: str) -> bool:
    for pat in INCLUDE_PATTERNS:
        if isinstance(pat, str) and pat.startswith("re:"):
            if re.match(pat[3:], name):
                return True
        elif pat == name:
            return True
    return False


def find_notes(vault):
    """Enumerate .md files to ingest.

    Rules:
    1. Any top-level folder matching INCLUDE_PATTERNS is walked recursively.
    2. Each path in EXTRA_WHITELIST (relative to the vault root) is also
       walked recursively. This lets users opt specific overview/dashboard
       folders into the retrieval index.

    Anything else at the vault root is ignored. This keeps inboxes, triage
    buffers, private-profile folders, and raw-archive directories out of
    RAG recall by default.
    """
    notes = []
    for name in os.listdir(vault):
        if not _folder_matches(name):
            continue
        folder = os.path.join(vault, name)
        if not os.path.isdir(folder):
            continue
        for root, _dirs, files in os.walk(folder):
            for f in files:
                if f.endswith(".md"):
                    notes.append(os.path.join(root, f))

    for rel in EXTRA_WHITELIST:
        extra = os.path.join(vault, rel)
        if not os.path.isdir(extra):
            continue
        for root, _dirs, files in os.walk(extra):
            for f in files:
                if f.endswith(".md"):
                    notes.append(os.path.join(root, f))

    # De-dup in case EXTRA_WHITELIST overlaps INCLUDE_PATTERNS.
    return sorted(set(notes))


def _norm_path(abs_path: str) -> str:
    """Normalise a note path for use as point_id hash input and payload.

    Always forward-slash. See module docstring for why this matters.
    """
    rel = os.path.relpath(abs_path, VAULT)
    return rel.replace(os.sep, "/")


def read_note(path):
    # utf-8-sig: upstream notes may carry a BOM from legacy tools.
    with open(path, "r", encoding="utf-8-sig") as f:
        content = f.read()

    m = re.match(r"^---\s*\n(.*?)\n---", content, flags=re.DOTALL)
    title = os.path.basename(path).replace(".md", "")
    ki = "universal"
    tags = []
    date = ""
    body = content

    if m:
        fm_text = m.group(1)
        body = content[m.end():].strip()
        for line in fm_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("title:"):
                title = stripped.split(":", 1)[1].strip().strip('"')
            elif stripped.startswith("knowledge_identity:"):
                ki = stripped.split(":", 1)[1].strip().strip('"')
            elif stripped.startswith("date:"):
                date = stripped.split(":", 1)[1].strip().strip('"')
            elif stripped.startswith("- "):
                tags.append(stripped[2:].strip())

    return {
        "title": title,
        "knowledge_identity": ki,
        "tags": tags,
        "date": date,
        "body": body[:20000],
        # Normalised to forward-slash — see module docstring "CRITICAL" section.
        "path": _norm_path(path),
    }


def make_point_id(path):
    # NOTE: `path` must already be forward-slash normalised. Without that,
    # Windows and Mac ingests of the same vault produce *different* IDs
    # for identical notes and the collection ends up with duplicate points.
    h = hashlib.md5(path.encode("utf-8")).hexdigest()
    return int(h[:16], 16) & 0x7FFFFFFFFFFFFFFF


def get_embeddings_batch(texts):
    resp = embed_client.embeddings.create(model="bge-m3", input=texts)
    return [d.embedding for d in resp.data]


def upsert_batch(points):
    result = qdrant_request("PUT", f"/collections/{COLLECTION}/points", {
        "points": points,
    })
    if result and result.get("status") == "ok":
        return True
    return False


def main():
    start_ts = time.time()
    print("Creating Qdrant collection if needed...")
    if not create_collection():
        return

    print(f"Scanning vault: {VAULT}")
    all_notes = find_notes(VAULT)
    print(f"Total notes found: {len(all_notes)}")

    print("Reading notes...")
    notes = []
    for path in all_notes:
        notes.append(read_note(path))

    print("Generating embeddings and upserting to Qdrant...")
    success = 0
    errors = 0

    for start in range(0, len(notes), BATCH_SIZE):
        batch = notes[start:start + BATCH_SIZE]
        # Embed only the first ~2000 chars. bge-m3 max_length=512 tokens;
        # over-long inputs are truncated at the tokenizer anyway. body_full
        # still keeps the whole thing in the payload for LLM injection.
        texts = [n["body"][:2000] for n in batch]

        try:
            embeddings = get_embeddings_batch(texts)
        except Exception as e:
            print(f"Embedding error at {start}: {e}")
            errors += len(batch)
            continue

        points = []
        for i, note in enumerate(batch):
            point_id = make_point_id(note["path"])
            points.append({
                "id": point_id,
                "vector": embeddings[i],
                "payload": {
                    "title": note["title"],
                    "knowledge_identity": note["knowledge_identity"],
                    "tags": note["tags"],
                    "date": note["date"],
                    "path": note["path"],
                    "body_preview": note["body"][:500],
                    "body_full": note["body"],
                },
            })

        if upsert_batch(points):
            success += len(batch)
        else:
            errors += len(batch)

        done = min(start + BATCH_SIZE, len(notes))
        if done % 200 == 0 or done >= len(notes):
            print(f"  {done} / {len(notes)} (success={success} errors={errors})")

        time.sleep(0.05)

    print("")
    print("=== DONE ===")
    print(f"Total:   {len(notes)}")
    print(f"Success: {success}")
    print(f"Errors:  {errors}")

    result = qdrant_request("GET", f"/collections/{COLLECTION}")
    points_count = None
    if result:
        points_count = result.get("result", {}).get("points_count", 0)
        print(f"Qdrant points count: {points_count}")

    elapsed = int(time.time() - start_ts)
    mins = elapsed // 60
    secs = elapsed % 60
    print(f"Elapsed: {mins}m{secs}s")


if __name__ == "__main__":
    main()
