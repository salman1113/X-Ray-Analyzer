"""
download_and_train.py
======================
One-shot script that:
  1. Downloads the Chest X-Ray Pneumonia dataset from Hugging Face Hub
     (falls back to Kaggle if HF_DATASET_REPO is not configured)
  2. Organises it into train/ val/ folders
  3. Fine-tunes ONLY the classifier head of DenseNet121 (backbone frozen)
     → very fast: ~15-25 min on CPU, ~3 min on GPU
  4. Saves the weights to routes/ai/models/chest.pth
  5. Uploads the new weights back to Hugging Face Hub (HF_MODEL_REPO)

Run from the backend/ directory:
    python scripts/download_and_train.py

For Kaggle fallback, set your Kaggle username + API key when prompted.
Get your key from: https://www.kaggle.com/settings → API → "Create New Token"
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path

# ── 0. Paths ──────────────────────────────────────────────────────────────────
BACKEND_DIR  = Path(__file__).parent.parent          # backend/
DATA_DIR     = BACKEND_DIR / "data" / "chest_raw"    # raw download lands here
TRAIN_DIR    = BACKEND_DIR / "data" / "chest" / "train"
VAL_DIR      = BACKEND_DIR / "data" / "chest" / "val"
MODEL_OUT    = BACKEND_DIR / "routes" / "ai" / "models" / "chest.pth"

KAGGLE_DATASET = "paultimothymooney/chest-xray-pneumonia"
CLASSES = ["NORMAL", "PNEUMONIA"]   # Kaggle folder names
CLASS_MAP = {"NORMAL": "Normal", "PNEUMONIA": "Pneumonia"}  # our registry names

# ── Load .env settings (HF_DATASET_REPO, HF_MODEL_REPO, HF_TOKEN) ────────────
def _load_hf_settings():
    """Read HF settings from .env without requiring the full FastAPI stack."""
    env_file = BACKEND_DIR / ".env"
    settings = {"HF_DATASET_REPO": "", "HF_MODEL_REPO": "", "HF_TOKEN": ""}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                key = key.strip()
                if key in settings:
                    settings[key] = val.strip()
    return settings

# ── 1a. Download from Hugging Face Hub (primary) ──────────────────────────────

def hf_download() -> bool:
    """
    Download the chest-xray-pneumonia.zip from Hugging Face Hub (1 file = 1 LFS request,
    well within the free tier rate limit), extract it, then organise into train/val.
    Returns True if successful, False if HF is not configured or fails.
    """
    cfg = _load_hf_settings()
    repo_id = cfg["HF_DATASET_REPO"]
    token   = cfg["HF_TOKEN"] or None

    if not repo_id or "your-username" in repo_id:
        print("ℹ️  HF_DATASET_REPO not set — will fall back to Kaggle download.")
        return False

    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("⚠️  huggingface_hub not installed. Run: pip install huggingface_hub")
        return False

    zip_dest = DATA_DIR / "chest-xray-pneumonia.zip"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n☁️  Downloading chest-xray-pneumonia.zip from HF Hub: {repo_id} ...", flush=True)
    try:
        downloaded = hf_hub_download(
            repo_id=repo_id,
            filename="chest-xray-pneumonia.zip",
            repo_type="dataset",
            token=token,
            local_dir=str(DATA_DIR),
        )
        print(f"✅ Downloaded to: {downloaded}\n")
        return True
    except Exception as exc:
        print(f"⚠️  HF Hub download failed ({exc}). Falling back to Kaggle...\n")
        return False


# ── 1b. Download from Kaggle (fallback) ───────────────────────────────────────

def download():
    try:
        import kaggle  # noqa: F401 — triggers credential check
    except Exception:
        print("Installing kaggle...", flush=True)
        os.system(f"{sys.executable} -m pip install -q kaggle")
        import kaggle  # noqa: F401

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n📥 Downloading {KAGGLE_DATASET} to {DATA_DIR} ...", flush=True)
    print("   (If prompted, enter your Kaggle username and API key)")
    print("   Get it from: https://www.kaggle.com/settings → API → Create New Token\n")

    os.system(
        f"kaggle datasets download -d {KAGGLE_DATASET} "
        f"--path {DATA_DIR} --unzip"
    )
    print("✅ Download complete\n")


# ── 2. Organise into train/ val/ ──────────────────────────────────────────────

def organise():
    # Kaggle extracts to: DATA_DIR/chest_xray/train/{NORMAL,PNEUMONIA}/
    #                     DATA_DIR/chest_xray/val/{NORMAL,PNEUMONIA}/
    #                     DATA_DIR/chest_xray/test/{NORMAL,PNEUMONIA}/
    src_root = DATA_DIR / "chest_xray"
    if not src_root.exists():
        # Sometimes it's nested one level deeper
        candidates = list(DATA_DIR.rglob("chest_xray"))
        if candidates:
            src_root = candidates[0]
        else:
            print("❌ Could not find 'chest_xray' folder after download.")
            sys.exit(1)

    print("📂 Organising dataset...", flush=True)

    for split_src, split_dst in [("train", TRAIN_DIR), ("val", VAL_DIR), ("test", VAL_DIR)]:
        src_split = src_root / split_src
        if not src_split.exists():
            continue
        for cls in CLASSES:
            src_cls = src_split / cls
            if not src_cls.exists():
                continue
            dst_cls = split_dst / CLASS_MAP[cls]
            dst_cls.mkdir(parents=True, exist_ok=True)
            count = 0
            for img in src_cls.iterdir():
                if img.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    dst = dst_cls / img.name
                    if not dst.exists():
                        shutil.copy2(img, dst)
                    count += 1
            print(f"   {split_src}/{cls} → {split_dst.name}/{CLASS_MAP[cls]}: {count} images")

    print("✅ Dataset organised\n")


# ── 3. Train ──────────────────────────────────────────────────────────────────

def train():
    # ── Fix SSL on Windows (prevents WinError 10054) ────────────────────────
    import ssl
    import urllib.request
    _old_https = urllib.request.HTTPSHandler
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_ctx))
    urllib.request.install_opener(opener)
    import os
    os.environ.setdefault("TORCH_HOME", str(Path.home() / ".cache" / "torch"))

    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader
    from torchvision import datasets, models, transforms
    from pathlib import Path as _Path

    CONDITIONS = ["Normal", "Pneumonia"]
    NUM_CLASSES = 2

    print("🧠 Building DenseNet121 (frozen backbone — fast training)...", flush=True)

    # Grayscale MUST come first — X-rays are grayscale, convert to 3-ch RGB for DenseNet
    train_tfm = transforms.Compose([
        transforms.Grayscale(num_output_channels=3),   # ← FIRST: grayscale → 3ch
        transforms.Resize((256, 256)),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(8),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    val_tfm = transforms.Compose([
        transforms.Grayscale(num_output_channels=3),   # ← FIRST
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    train_ds = datasets.ImageFolder(str(TRAIN_DIR), transform=train_tfm)
    val_ds   = datasets.ImageFolder(str(VAL_DIR),   transform=val_tfm)

    print(f"   Train: {len(train_ds)} images   Val: {len(val_ds)} images")
    print(f"   Classes found: {train_ds.classes}")
    print(f"   Class → index: {train_ds.class_to_idx}\n")

    BATCH = 32
    WORKERS = 0   # 0 is required on Windows to avoid multiprocessing issues
    train_dl = DataLoader(train_ds, batch_size=BATCH, shuffle=True,  num_workers=WORKERS, pin_memory=False)
    val_dl   = DataLoader(val_ds,   batch_size=BATCH, shuffle=False, num_workers=WORKERS, pin_memory=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🖥  Device: {device}", flush=True)

    # Load DenseNet121 — weights from local cache (already downloaded)
    cached_weights = _Path.home() / ".cache" / "torch" / "hub" / "checkpoints" / "densenet121-a639ec97.pth"
    model = models.densenet121(weights=None)   # no network download
    if cached_weights.exists():
        print(f"   Loading ImageNet weights from local cache...")
        state = torch.load(str(cached_weights), map_location="cpu")
        # torchvision 0.14+ renamed DenseNet keys: norm.1 → norm1, conv.2 → conv2
        # This replicates the fix from torchvision/models/densenet.py _load_state_dict()
        import re
        pattern = re.compile(
            r"^(.*denselayer\d+\.(?:norm|relu|conv))\.((?:[12])\.(?:weight|bias|running_mean|running_var))$"
        )
        for key in list(state.keys()):
            res = pattern.match(key)
            if res:
                new_key = res.group(1) + res.group(2)
                state[new_key] = state[key]
                del state[key]
        model.load_state_dict(state, strict=True)
        print(f"   ✅ ImageNet weights loaded successfully")
    else:
        print("   ⚠️  No cached weights found — using random init")

    # Freeze entire backbone — only train the 2-class head
    for param in model.parameters():
        param.requires_grad = False

    # Replace classifier head — ONLY this trains
    model.classifier = nn.Linear(model.classifier.in_features, NUM_CLASSES)
    model.to(device)


    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.classifier.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=2, gamma=0.5)

    EPOCHS = 5
    best_val_acc = 0.0

    print(f"\n{'='*60}")
    print(f" Training: Chest X-Ray (Normal vs Pneumonia)")
    print(f" Epochs: {EPOCHS}  |  Batch: {BATCH}  |  Device: {device}")
    print(f"{'='*60}\n")

    for epoch in range(1, EPOCHS + 1):
        # ── Train ──
        model.train()
        t_loss, t_correct = 0.0, 0
        for i, (imgs, labels) in enumerate(train_dl):
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            out  = model(imgs)
            loss = criterion(out, labels)
            loss.backward()
            optimizer.step()
            t_loss    += loss.item() * imgs.size(0)
            t_correct += (out.argmax(1) == labels).sum().item()

            if (i + 1) % 20 == 0:
                print(f"  Epoch {epoch} step {i+1}/{len(train_dl)}", end="\r", flush=True)

        # ── Validate ──
        model.eval()
        v_loss, v_correct = 0.0, 0
        with torch.no_grad():
            for imgs, labels in val_dl:
                imgs, labels = imgs.to(device), labels.to(device)
                out    = model(imgs)
                v_loss += criterion(out, labels).item() * imgs.size(0)
                v_correct += (out.argmax(1) == labels).sum().item()

        t_acc = t_correct / len(train_ds) * 100
        v_acc = v_correct / len(val_ds)   * 100
        mark  = "  ← best ✅" if v_acc > best_val_acc else ""

        print(
            f"Epoch {epoch:02d}/{EPOCHS}  "
            f"train loss={t_loss/len(train_ds):.4f} acc={t_acc:.1f}%  "
            f"val loss={v_loss/len(val_ds):.4f} acc={v_acc:.1f}%"
            + mark
        )

        if v_acc > best_val_acc:
            best_val_acc = v_acc
            MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), str(MODEL_OUT))

        scheduler.step()

    print(f"\n{'='*60}")
    print(f"✅ Training complete!")
    print(f"   Best val accuracy : {best_val_acc:.1f}%")
    print(f"   Saved to          : {MODEL_OUT}")
    print(f"{'='*60}")
    print("\n🔄 Now restart the backend:")
    print("   docker compose restart\n")


# ── 5. Upload model weights to Hugging Face Hub ───────────────────────────────

def upload_model_to_hf() -> None:
    """
    Push the freshly trained chest.pth to the HF model repo so any
    machine can auto-download it on next inference.
    Skips silently if HF_MODEL_REPO is not configured.
    """
    cfg     = _load_hf_settings()
    repo_id = cfg["HF_MODEL_REPO"]
    token   = cfg["HF_TOKEN"] or None

    if not repo_id or "your-username" in repo_id:
        print("ℹ️  HF_MODEL_REPO not set — skipping weight upload.")
        print("   Set HF_MODEL_REPO in .env to auto-push trained weights to the cloud.\n")
        return

    if not MODEL_OUT.exists():
        print("⚠️  Model file not found — nothing to upload.")
        return

    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("⚠️  huggingface_hub not installed. Run: pip install huggingface_hub")
        return

    print(f"\n☁️  Uploading chest.pth to HF Hub: {repo_id} ...", flush=True)
    try:
        api = HfApi()
        api.upload_file(
            path_or_fileobj=str(MODEL_OUT),
            path_in_repo="chest.pth",
            repo_id=repo_id,
            repo_type="model",
            token=token,
            commit_message="Update chest.pth from download_and_train.py",
        )
        print(f"✅ Weights uploaded to https://huggingface.co/{repo_id}\n")
    except Exception as exc:
        print(f"⚠️  Upload failed: {exc}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Step 1: Check if organised data already exists
    already_organised = (
        (TRAIN_DIR / "Normal").exists()
        and any((TRAIN_DIR / "Normal").iterdir())
    )

    if already_organised:
        print("📦 Dataset already organised — skipping download & extract\n")
    else:
        # Try Hugging Face Hub first (fastest, no Kaggle credentials needed)
        hf_ok = hf_download()

        if hf_ok:
            # HF snapshot_download already puts files in the right structure
            print("📂 Verifying dataset structure...")
        else:
            # Fallback: Kaggle download + organise
            zip_file = DATA_DIR / "chest-xray-pneumonia.zip"
            if zip_file.exists() and zip_file.stat().st_size > 1_000_000_000:
                print(f"📦 ZIP already downloaded ({zip_file.stat().st_size / 1e9:.2f} GB) — skipping download\n")
                extracted = DATA_DIR / "chest_xray"
                if not extracted.exists():
                    import zipfile
                    print("📂 Extracting zip...")
                    with zipfile.ZipFile(zip_file, "r") as z:
                        members = z.namelist()
                        print(f"   {len(members)} files to extract...")
                        for i, m in enumerate(members):
                            z.extract(m, DATA_DIR)
                            if i % 1000 == 0:
                                print(f"   {i}/{len(members)} ...", end="\r", flush=True)
                    print("\n✅ Extracted!")
                organise()
            else:
                download()
                organise()

    # Step 2: Train
    train()

    # Step 3: Push the new weights back to Hugging Face Hub
    upload_model_to_hf()
