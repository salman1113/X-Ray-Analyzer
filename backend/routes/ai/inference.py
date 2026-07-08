"""
AI model inference engine — multi-body-part DenseNet121.

One DenseNet121 per body part, each with its own classifier head
sized to that part's condition count. Models are loaded lazily on
first use and cached in memory as a dict keyed by body part name.

Model files live in:  backend/routes/ai/models/<body_part>.pth
Cloud fallback:       Auto-downloaded from Hugging Face Hub if not found locally.
Final fallback:       ImageNet weights if HF is also unavailable (lower accuracy).
"""

import logging
from pathlib import Path

import torch
import torch.nn as nn
from torchvision import models

from routes.ai.body_parts import BodyPartConfig, get_body_part

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent / "models"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# In-memory cache: body_part_key → loaded nn.Module
_model_cache: dict[str, nn.Module] = {}


# ── Cloud Download Helper ─────────────────────────────────────────────────────


def _ensure_model_weights(cfg: BodyPartConfig) -> None:
    """
    If the local .pth file is missing, attempt to download it from
    Hugging Face Hub using the HF_MODEL_REPO and HF_TOKEN settings.

    This is a no-op if:
      - The file already exists locally.
      - HF_MODEL_REPO is not configured (still the placeholder value).
      - huggingface_hub is not installed.
      - The network request fails (logged as a warning, falls through to ImageNet).
    """
    weights_path = MODELS_DIR / cfg.model_file
    if weights_path.exists() and weights_path.stat().st_size > 0:
        return  # Already present — nothing to do

    try:
        from huggingface_hub import hf_hub_download

        from core.settings import settings
    except ImportError:
        logger.warning("huggingface_hub not installed — cannot auto-download model weights.")
        return

    repo_id = settings.HF_MODEL_REPO
    if not repo_id or "your-username" in repo_id:
        logger.warning(
            "HF_MODEL_REPO not configured. Set it in .env to enable auto-download of model weights."
        )
        return

    token = settings.HF_TOKEN or None  # None = public repo, token = private repo
    logger.info(
        "[%s] Weights not found locally. Downloading from HF Hub: %s/%s ...",
        cfg.model_file,
        repo_id,
        cfg.model_file,
    )
    try:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        downloaded = hf_hub_download(
            repo_id=repo_id,
            filename=cfg.model_file,
            token=token,
            local_dir=str(MODELS_DIR),
        )
        logger.info("[%s] Downloaded from HF Hub → %s ✅", cfg.model_file, downloaded)
    except Exception as exc:
        logger.warning(
            "[%s] HF Hub download failed (%s). Will fall back to ImageNet weights.",
            cfg.model_file,
            exc,
        )


# ── Model Construction ────────────────────────────────────────────────────────


def _build_densenet(num_classes: int) -> nn.Module:
    """
    DenseNet121 with a custom classification head.
    num_classes = number of conditions for the target body part.
    """
    net = models.densenet121(weights=models.DenseNet121_Weights.IMAGENET1K_V1)
    in_features = net.classifier.in_features  # 1024
    net.classifier = nn.Linear(in_features, num_classes)
    return net


def _load_model_for_part(body_part_key: str, cfg: BodyPartConfig) -> nn.Module:
    """
    Load (or create) a DenseNet121 for the given body part.
    1. Tries local weights file in models/<body_part>.pth.
    2. If missing, auto-downloads from Hugging Face Hub (HF_MODEL_REPO setting).
    3. Falls back to ImageNet pretrained weights if neither is available.
    """
    num_classes = len(cfg.conditions)
    model = _build_densenet(num_classes)

    # Attempt cloud download if weights are absent
    _ensure_model_weights(cfg)

    weights_path = MODELS_DIR / cfg.model_file
    if weights_path.exists() and weights_path.stat().st_size > 0:
        logger.info("[%s] Loading fine-tuned weights: %s", body_part_key, weights_path)
        state = torch.load(weights_path, map_location=DEVICE)
        # Support both raw state_dict and checkpoint dict
        if isinstance(state, dict) and "model_state_dict" in state:
            state = state["model_state_dict"]
        try:
            model.load_state_dict(state)
            logger.info("[%s] Fine-tuned weights loaded ✅", body_part_key)
        except RuntimeError as e:
            logger.warning(
                "[%s] Weight shape mismatch — falling back to ImageNet weights. Error: %s",
                body_part_key,
                e,
            )
    else:
        logger.warning(
            "[%s] No fine-tuned weights found at %s. "
            "Using ImageNet pretrained weights — accuracy will be limited. "
            "Train a model and place it at models/%s to improve accuracy.",
            body_part_key,
            weights_path,
            cfg.model_file,
        )

    model.to(DEVICE)
    model.eval()
    return model


# ── Public API ────────────────────────────────────────────────────────────────


def get_model(body_part_key: str) -> nn.Module:
    """
    Return the model for the given body part (lazy-loaded, cached).
    Thread-safe for read-after-first-load; first load is synchronous at request time.
    """
    key = body_part_key.lower().strip()
    if key not in _model_cache:
        cfg = get_body_part(key)
        _model_cache[key] = _load_model_for_part(key, cfg)
    return _model_cache[key]


def preload_all_models() -> None:
    """
    Eagerly load all body-part models at startup.
    Call this from core/events.py lifespan if you want zero cold-start latency.
    Only preloads models whose .pth file exists.
    """
    from routes.ai.body_parts import _REGISTRY

    for key, cfg in _REGISTRY.items():
        if (MODELS_DIR / cfg.model_file).exists():
            get_model(key)
            logger.info("Preloaded model for body part: %s", key)


async def run_inference(tensor: torch.Tensor, body_part_key: str) -> dict:
    """
    Run the appropriate DenseNet121 model on a preprocessed input tensor.

    Args:
        tensor:         Shape [1, 3, 224, 224] — output of preprocess_image().
        body_part_key:  e.g. "chest", "knee", "hand", "spine" …

    Returns:
        {
          "body_part":     "knee",
          "prediction":    "Osteoarthritis",
          "confidence":    0.8732,
          "probabilities": {"Normal": 0.08, "Osteoarthritis": 0.87, "Fracture": 0.03, "Effusion": 0.02}
        }
    """
    cfg = get_body_part(body_part_key)
    model = get_model(body_part_key)

    tensor = tensor.to(DEVICE)

    with torch.no_grad():
        logits = model(tensor)  # [1, num_classes]
        probs = torch.softmax(logits, dim=1)[0]  # [num_classes]

    predicted_idx = int(probs.argmax().item())
    confidence = float(probs[predicted_idx].item())
    prediction = cfg.conditions[predicted_idx]

    probabilities = {cls: round(float(probs[i].item()), 4) for i, cls in enumerate(cfg.conditions)}

    logger.info(
        "[%s] prediction=%s  confidence=%.1f%%",
        body_part_key,
        prediction,
        confidence * 100,
    )

    return {
        "body_part": body_part_key,
        "prediction": prediction,
        "confidence": round(confidence, 4),
        "probabilities": probabilities,
    }
