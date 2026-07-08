import io
import cv2
import numpy as np
import torch
from torchvision import models, transforms
from PIL import Image
from typing import Tuple, Dict, Any, List
from ultralytics import YOLO
from pytorch_gradcam import GradCAM
from pytorch_gradcam.utils.image import show_cam_on_image
from pytorch_gradcam.utils.model_targets import ClassifierOutputTarget
import boto3
import uuid
import asyncio
from fastapi import UploadFile
import os
import logging

logger = logging.getLogger(__name__)

# Device setup
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def preprocess_image(image_bytes: bytes) -> Tuple[torch.Tensor, np.ndarray]:
    """
    OpenCV Preprocessing Pipeline:
    1. Grayscale
    2. Resize to 512x512 with aspect-ratio padding
    3. CLAHE
    4. Gaussian Blur
    5. Normalize [0, 1]
    6. ImageNet normalization (single-channel)
    7. Convert to PyTorch tensor
    """
    # Load image from bytes
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError("Invalid image file format")

    # 1. Convert to Grayscale if RGB
    if len(img.shape) == 3 and img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    elif len(img.shape) == 3 and img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        
    # 2. Resize to 512x512 with aspect-ratio-preserving padding
    target_size = 512
    h, w = img.shape
    scale = target_size / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    top = (target_size - new_h) // 2
    bottom = target_size - new_h - top
    left = (target_size - new_w) // 2
    right = target_size - new_w - left
    
    padded = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=0)
    
    # Visual RGB copy (required for GradCAM overlay)
    vis_img = cv2.cvtColor(padded, cv2.COLOR_GRAY2RGB)
    vis_img = np.float32(vis_img) / 255.0
    
    # 3. Apply CLAHE (Contrast Enhancement)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(padded)
    
    # 4. Gaussian Blur (Noise Reduction, 3x3)
    blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
    
    # 5. Normalize [0, 1]
    normalized = blurred.astype(np.float32) / 255.0
    
    # 6. ImageNet normalization for single-channel (mean=[0.485], std=[0.229])
    normalized = (normalized - 0.485) / 0.229
    
    # 7. Convert to PyTorch tensor with batch and channel dimension
    tensor = torch.from_numpy(normalized).unsqueeze(0).unsqueeze(0)  # Shape: (1, 1, 512, 512)
    
    return tensor.to(DEVICE), vis_img

class ModelManager:
    """Singleton Manager for EfficientNet-B4 and YOLOv8 models"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._init_models()
        return cls._instance
        
    def _init_models(self):
        try:
            logger.info("MOCK MODE: Skipping EfficientNet-B4 & YOLOv8 model loading...")
            # self.eff_net = models.efficientnet_b4(weights=None)
            # self.eff_net.features[0][0] = torch.nn.Conv2d(1, 48, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1), bias=False)
            # self.eff_net.classifier[1] = torch.nn.Linear(in_features=1792, out_features=2, bias=True)
            # self.eff_net.eval().to(DEVICE)
            # target_layers = [self.eff_net.features[-1]]
            # self.cam = GradCAM(model=self.eff_net, target_layers=target_layers)
            # self.yolo = YOLO('yolov8n-med.pt')
            logger.info("Models initialized in MOCK mode.")
        except Exception as e:
            logger.error(f"Error loading models: {e}")

    def run_inference(self, tensor: torch.Tensor, vis_img: np.ndarray) -> Dict[str, Any]:
        # MOCK Inference Response
        prediction_label = "abnormal"
        conf_score = 0.88
        localization_boxes = [{"label": "fracture", "confidence": 0.88, "bbox": [150, 200, 250, 300]}]
        
        # Create a dummy heatmap image for testing (just the original image overlaid with boxes)
        heatmap_img = vis_img.copy()
        
        # Overlay Bounding Boxes on the Heatmap
        for b in localization_boxes:
            x1, y1, x2, y2 = b["bbox"]
            cv2.rectangle(heatmap_img, (x1, y1), (x2, y2), (255, 0, 0), 2)
            label_text = f"{b['label']} {b['confidence']:.2f}"
            cv2.putText(heatmap_img, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            
        # Convert output heatmap back to bytes format for S3 upload
        heatmap_bgr = cv2.cvtColor(heatmap_img * 255, cv2.COLOR_RGB2BGR) if heatmap_img.dtype == np.float32 else cv2.cvtColor(heatmap_img, cv2.COLOR_RGB2BGR)
        _, buffer = cv2.imencode('.jpg', heatmap_bgr)
        heatmap_bytes = buffer.tobytes()
        
        return {
            "prediction": prediction_label,
            "confidence_score": conf_score,
            "heatmap_bytes": heatmap_bytes,
            "localization": localization_boxes
        }

async def upload_to_s3(file_bytes: bytes, filename: str, content_type: str = "image/jpeg") -> str:
    """Async file upload to AWS S3 storage"""
    loop = asyncio.get_event_loop()
    
    # Example Boto3 setup
    # s3_client = boto3.client('s3', 
    #                          aws_access_key_id=os.getenv("AWS_ACCESS_KEY"), 
    #                          aws_secret_access_key=os.getenv("AWS_SECRET_KEY"), 
    #                          region_name=os.getenv("AWS_REGION", "us-east-1"))
    bucket = os.getenv("AWS_S3_BUCKET", "xray-analyzer-bucket")
    
    def _upload():
        # s3_client.put_object(Bucket=bucket, Key=filename, Body=file_bytes, ContentType=content_type)
        return f"https://{bucket}.s3.amazonaws.com/{filename}"
    
    try:
        url = await loop.run_in_executor(None, _upload)
        return url
    except Exception as e:
        logger.error(f"S3 Upload failed: {e}")
        return f"https://mock-s3-bucket.s3.amazonaws.com/{filename}"
