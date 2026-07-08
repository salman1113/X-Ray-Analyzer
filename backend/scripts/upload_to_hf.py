"""
upload_to_hf.py
================
One-shot migration utility: pushes local training data and model weights
to Hugging Face Hub so they can be removed from the Git repo.

Run from the backend/ directory:
    python scripts/upload_to_hf.py

Make sure you have set the following in backend/.env:
    HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
    HF_DATASET_REPO=your-username/xray-chest-pneumonia
    HF_MODEL_REPO=your-username/xray-models

Requirements:
    pip install huggingface_hub

Hugging Face setup (one-time):
    1. Create a free account at https://huggingface.co
    2. Go to Settings → Access Tokens → New token (write access)
    3. Create a Dataset repo: https://huggingface.co/new-dataset
    4. Create a Model repo:   https://huggingface.co/new
    5. Fill in HF_TOKEN, HF_DATASET_REPO, HF_MODEL_REPO in .env
    6. Run this script
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent  # backend/
DATA_CHEST  = BACKEND_DIR / "data" / "chest"
MODELS_DIR  = BACKEND_DIR / "routes" / "ai" / "models"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_hf_settings() -> dict:
    """Read HF settings from .env without requiring the full FastAPI stack."""
    env_file = BACKEND_DIR / ".env"
    cfg = {"HF_DATASET_REPO": "", "HF_MODEL_REPO": "", "HF_TOKEN": ""}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                key = key.strip()
                if key in cfg:
                    cfg[key] = val.strip()
    return cfg


def _require_huggingface_hub():
    try:
        import huggingface_hub  # noqa: F401
    except ImportError:
        print("❌  huggingface_hub not installed.")
        print("    Run: pip install huggingface_hub")
        sys.exit(1)


def _validate_settings(cfg: dict) -> None:
    missing = []
    if not cfg["HF_TOKEN"] or cfg["HF_TOKEN"].startswith("hf_xxx"):
        missing.append("HF_TOKEN")
    if not cfg["HF_DATASET_REPO"] or "your-username" in cfg["HF_DATASET_REPO"]:
        missing.append("HF_DATASET_REPO")
    if not cfg["HF_MODEL_REPO"] or "your-username" in cfg["HF_MODEL_REPO"]:
        missing.append("HF_MODEL_REPO")
    if missing:
        print(f"❌  Missing / unconfigured settings in .env: {', '.join(missing)}")
        print("    Please set them and try again.")
        sys.exit(1)


# ── Upload Functions ──────────────────────────────────────────────────────────

def upload_dataset(cfg: dict) -> None:
    """
    Upload the organised chest dataset (train/ + val/) to the HF Dataset repo.
    Uses upload_folder which handles large numbers of files efficiently.
    """
    from huggingface_hub import HfApi

    repo_id = cfg["HF_DATASET_REPO"]
    token   = cfg["HF_TOKEN"]

    if not DATA_CHEST.exists():
        print(f"⚠️   Dataset folder not found: {DATA_CHEST}")
        print("     Run download_and_train.py first to organise the dataset.")
        return

    # Count files for a quick summary
    image_count = sum(1 for f in DATA_CHEST.rglob("*") if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png"})
    print(f"\n☁️   Uploading dataset ({image_count:,} images) → {repo_id}")
    print(f"     Source: {DATA_CHEST}")

    api = HfApi()

    # Ensure the dataset repo exists (creates it if it doesn't)
    try:
        api.create_repo(repo_id=repo_id, repo_type="dataset", token=token, exist_ok=True)
    except Exception as exc:
        print(f"⚠️   Could not create/verify dataset repo: {exc}")

    api.upload_folder(
        folder_path=str(DATA_CHEST),
        repo_id=repo_id,
        repo_type="dataset",
        token=token,
        commit_message="Upload organised chest X-ray dataset (train/val splits)",
        ignore_patterns=["*.git*", ".DS_Store", "Thumbs.db"],
    )
    print(f"✅  Dataset uploaded → https://huggingface.co/datasets/{repo_id}\n")


def upload_models(cfg: dict) -> None:
    """
    Upload all .pth files found in routes/ai/models/ to the HF Model repo.
    """
    from huggingface_hub import HfApi

    repo_id = cfg["HF_MODEL_REPO"]
    token   = cfg["HF_TOKEN"]

    pth_files = list(MODELS_DIR.glob("*.pth"))
    if not pth_files:
        print(f"⚠️   No .pth files found in {MODELS_DIR}")
        return

    print(f"\n☁️   Uploading {len(pth_files)} model weight(s) → {repo_id}")
    api = HfApi()

    # Ensure the model repo exists
    try:
        api.create_repo(repo_id=repo_id, repo_type="model", token=token, exist_ok=True)
    except Exception as exc:
        print(f"⚠️   Could not create/verify model repo: {exc}")

    for pth in pth_files:
        size_mb = pth.stat().st_size / 1_000_000
        print(f"     Uploading {pth.name} ({size_mb:.1f} MB) ...", flush=True)
        api.upload_file(
            path_or_fileobj=str(pth),
            path_in_repo=pth.name,
            repo_id=repo_id,
            repo_type="model",
            token=token,
            commit_message=f"Upload {pth.name}",
        )
        print(f"     ✅ {pth.name} uploaded")

    print(f"\n✅  All models uploaded → https://huggingface.co/{repo_id}\n")


# ── Post-migration Advice ─────────────────────────────────────────────────────

def print_next_steps(cfg: dict) -> None:
    print("=" * 65)
    print("  🎉  Migration complete!")
    print("=" * 65)
    print()
    print("Next steps:")
    print()
    print("  1. Add the following to .gitignore (if not already):")
    print("       backend/data/")
    print("       backend/routes/ai/models/*.pth")
    print()
    print("  2. Remove the heavy local files from Git tracking:")
    print("       git rm -r --cached backend/data/")
    print("       git rm --cached backend/routes/ai/models/*.pth")
    print("       git commit -m 'chore: move data & models to Hugging Face Hub'")
    print()
    print("  3. You can now safely delete the local data/ folder and .pth files.")
    print("     The backend will auto-download weights on first inference.")
    print("     Training scripts will pull the dataset from HF on next run.")
    print()
    print(f"  Dataset: https://huggingface.co/datasets/{cfg['HF_DATASET_REPO']}")
    print(f"  Models:  https://huggingface.co/{cfg['HF_MODEL_REPO']}")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🚀  X-Ray Analyzer — Hugging Face Hub Migration Utility")
    print("=" * 55)

    _require_huggingface_hub()
    cfg = _load_hf_settings()
    _validate_settings(cfg)

    print(f"\n  Dataset repo : {cfg['HF_DATASET_REPO']}")
    print(f"  Model repo   : {cfg['HF_MODEL_REPO']}")
    print(f"  Token        : {cfg['HF_TOKEN'][:8]}{'*' * 12}")

    confirm = input("\n  Proceed with upload? [y/N] ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        sys.exit(0)

    upload_dataset(cfg)
    upload_models(cfg)
    print_next_steps(cfg)
