"""
X-Ray image preprocessing pipeline.
- Loads image from local filesystem path
- Resizes to 224x224 (DenseNet/ResNet input size)
- Applies ImageNet normalization
- Returns a model-ready PyTorch tensor + the original PIL image
"""

from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms

# ── ImageNet normalization stats (standard for pretrained torchvision models) ──
_IMAGENET_MEAN = [0.485, 0.456, 0.406]
_IMAGENET_STD = [0.229, 0.224, 0.225]

_transform = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.Grayscale(num_output_channels=3),  # X-rays are grayscale → replicate to 3ch
        transforms.ToTensor(),
        transforms.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
    ]
)


async def preprocess_image(image_path: str) -> tuple[torch.Tensor, Image.Image]:
    """
    Load and preprocess an X-ray image for inference.

    Args:
        image_path: Absolute or relative path to the X-ray image file.

    Returns:
        (tensor, pil_image)
        - tensor      : shape [1, 3, 224, 224] — ready for model forward pass
        - pil_image   : original PIL image (used for Grad-CAM overlay)

    Raises:
        FileNotFoundError: if image_path does not exist on disk.
        ValueError: if the file cannot be opened as an image.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"X-ray image not found at: {image_path}")

    try:
        pil_image = Image.open(path).convert("RGB")
    except Exception as exc:
        raise ValueError(f"Cannot open image at {image_path}: {exc}") from exc

    # Add batch dimension → [1, 3, 224, 224]
    tensor = _transform(pil_image).unsqueeze(0)
    return tensor, pil_image
