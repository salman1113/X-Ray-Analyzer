"""
Grad-CAM visualization generator.

Grad-CAM (Gradient-weighted Class Activation Mapping) highlights the
regions in an X-ray that the model focused on when making its prediction.

How it works:
  1. Register a forward hook on the last convolutional layer (DenseNet's denseblock4).
  2. Run a forward + backward pass.
  3. Global-average-pool the gradients → importance weights per feature map.
  4. Weighted-sum the feature maps → raw heatmap.
  5. Normalize, resize to original image size, apply a color map.
  6. Blend heatmap (40%) over the original X-ray (60%) → overlay image.
  7. Save to disk and return the saved path.
"""

import logging
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image

logger = logging.getLogger(__name__)

# ── Target layer in DenseNet121 ─────────────────────────────────────────────
# denseblock4 is the last convolutional block before the global average pool.
_TARGET_LAYER_NAME = "features.denseblock4"


def _get_target_layer(model: nn.Module) -> nn.Module:
    """Navigate DenseNet's nested module tree to denseblock4."""
    return model.features.denseblock4


async def generate_gradcam(
    image_path: str,
    model: nn.Module,
    tensor: torch.Tensor,
    predicted_class_idx: int,
    output_dir: str,
    scan_id: str,
) -> str | None:
    """
    Generate a Grad-CAM heatmap overlay for the given X-ray scan.

    Args:
        image_path        : Path to the original X-ray image (for overlay).
        model             : The loaded DenseNet121 model.
        tensor            : Preprocessed input tensor [1, 3, 224, 224].
        predicted_class_idx: Index of the predicted class (0=Normal, 1=Pneumonia).
        output_dir        : Directory to save the heatmap image.
        scan_id           : Unique scan ID used in the output filename.

    Returns:
        Path to the saved heatmap PNG, or None if generation fails.
    """
    device = next(model.parameters()).device
    tensor = tensor.to(device)

    # ── 1. Register hooks to capture activations and gradients ─────────────
    activations: list[torch.Tensor] = []
    gradients: list[torch.Tensor] = []

    target_layer = _get_target_layer(model)

    fwd_hook = target_layer.register_forward_hook(lambda _, __, output: activations.append(output))
    bwd_hook = target_layer.register_full_backward_hook(
        lambda _, __, grad_output: gradients.append(grad_output[0])
    )

    try:
        # ── 2. Forward + backward pass ──────────────────────────────────────
        # Clone and detach so we get a fresh leaf tensor that supports grad
        tensor_grad = tensor.clone().detach().requires_grad_(True)

        model.zero_grad()
        output = model(tensor_grad)  # [1, num_classes]
        score = output[0, predicted_class_idx]  # scalar for target class
        score.backward()

        if not activations or not gradients:
            logger.warning("Grad-CAM hooks did not capture data for scan %s", scan_id)
            return None

        # ── 3. Compute channel-wise importance weights ─────────────────────
        act = activations[0].detach()  # [1, C, H, W]
        grad = gradients[0].detach()  # [1, C, H, W]
        weights = grad.mean(dim=(2, 3), keepdim=True)  # [1, C, 1, 1]

        # ── 4. Weighted combination of activation maps ─────────────────────
        cam = (weights * act).sum(dim=1, keepdim=True)  # [1, 1, H, W]
        cam = torch.relu(cam)  # only positive influence
        cam = cam.squeeze().cpu().numpy()  # [H, W] or scalar
        cam = np.atleast_2d(cam)  # ensure 2-D even if squeezed too far

        # ── 5. Normalize to [0, 255] ────────────────────────────────────────
        cam_min, cam_max = cam.min(), cam.max()
        if cam_max - cam_min < 1e-8:
            logger.warning("Grad-CAM has near-zero activation for scan %s", scan_id)
            cam = np.zeros_like(cam, dtype=np.uint8)
        else:
            cam = ((cam - cam_min) / (cam_max - cam_min) * 255).astype(np.uint8)

        # ── 6. Resize heatmap to original image size ────────────────────────
        original = Image.open(image_path).convert("RGB")
        orig_w, orig_h = original.size
        cam_resized = cv2.resize(cam, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)

        # ── 7. Apply colormap and blend ─────────────────────────────────────
        heatmap_bgr = cv2.applyColorMap(cam_resized, cv2.COLORMAP_JET)  # BGR
        heatmap_rgb = cv2.cvtColor(heatmap_bgr, cv2.COLOR_BGR2RGB)  # RGB

        orig_np = np.array(original)
        overlay = cv2.addWeighted(orig_np, 0.6, heatmap_rgb, 0.4, 0)

        # ── 8. Save overlay image ───────────────────────────────────────────
        out_path = Path(output_dir) / f"{scan_id}_gradcam.png"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(overlay).save(str(out_path))

        logger.info("Grad-CAM saved to %s", out_path)
        return str(out_path)

    except Exception as exc:
        logger.exception("Grad-CAM generation failed for scan %s: %s", scan_id, exc)
        return None

    finally:
        fwd_hook.remove()
        bwd_hook.remove()
        model.zero_grad()
