"""
Universal X-Ray Model Training Script
======================================
Fine-tune a DenseNet121 for ANY body part defined in body_parts.py.

Usage:
    python train_model.py --body_part knee --dataset ./data/knee_xray
    python train_model.py --body_part chest --dataset ./data/chest_xray --epochs 10

Dataset structure required (ImageFolder format):
    data/<body_part>/
    ├── train/
    │   ├── Normal/           ← one folder per condition
    │   ├── Osteoarthritis/
    │   ├── Fracture/
    │   └── Effusion/
    ├── val/
    │   ├── Normal/
    │   └── ...
    └── test/                 (optional)
        └── ...

Recommended public datasets per body part:
    chest   → Kaggle: "Chest X-Ray Images (Pneumonia)" by Paul Mooney
              https://kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia
    knee    → Kaggle: "Knee Osteoarthritis Dataset"
              https://kaggle.com/datasets/shashwatwork/knee-osteoarthritis-dataset-with-severity
    hand    → Kaggle: "Bone Break Classifier"
              https://kaggle.com/datasets/pkdarabi/bone-fracture-detection-computer-vision-project
    spine   → Kaggle: "Vertebral Column Dataset"
              https://kaggle.com/datasets/cesar-valdez/vertebral-column
    hip/shoulder/elbow → MURA dataset (Stanford):
              https://stanfordmlgroup.github.io/competitions/mura/

After training, the script saves:
    backend/routes/ai/models/<body_part>.pth
"""

import argparse
import sys
from pathlib import Path

# ── Make sure we can import body_parts from the backend package ──────────────
BACKEND_DIR = Path(__file__).parent.parent.parent   # adjust if script location changes
sys.path.insert(0, str(BACKEND_DIR))


def parse_args():
    p = argparse.ArgumentParser(description="Train X-Ray DenseNet121 for a body part")
    p.add_argument("--body_part", required=True,
                   help="Body part key (e.g. chest, knee, hand, spine)")
    p.add_argument("--dataset",   required=True,
                   help="Path to dataset root (must contain train/ and val/ subdirs)")
    p.add_argument("--epochs",    type=int, default=8,
                   help="Number of training epochs (default: 8)")
    p.add_argument("--batch_size",type=int, default=32)
    p.add_argument("--lr",        type=float, default=1e-4)
    p.add_argument("--freeze_backbone", action="store_true",
                   help="Freeze DenseNet feature layers, only train the classifier head")
    return p.parse_args()


def main():
    args = parse_args()

    # ── Import after path setup ───────────────────────────────────────────────
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader
    from torchvision import datasets, models, transforms

    from routes.ai.body_parts import get_body_part

    # ── Validate body part ────────────────────────────────────────────────────
    try:
        cfg = get_body_part(args.body_part)
    except KeyError as e:
        print(f"Error: {e}")
        sys.exit(1)

    conditions = cfg.conditions
    num_classes = len(conditions)
    print(f"\n{'='*60}")
    print(f"  Training: {cfg.label}")
    print(f"  Classes ({num_classes}): {conditions}")
    print(f"  Dataset:  {args.dataset}")
    print(f"  Epochs:   {args.epochs}")
    print(f"{'='*60}\n")

    # ── Data transforms ───────────────────────────────────────────────────────
    train_tfm = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.Grayscale(num_output_channels=3),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    val_tfm = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.Grayscale(num_output_channels=3),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    dataset_path = Path(args.dataset)
    train_ds = datasets.ImageFolder(str(dataset_path / "train"), transform=train_tfm)
    val_ds   = datasets.ImageFolder(str(dataset_path / "val"),   transform=val_tfm)

    # Verify dataset classes match registry conditions
    found_classes = sorted(train_ds.classes)
    expected      = sorted(conditions)
    if found_classes != expected:
        print(f"⚠️  WARNING: dataset folders {found_classes} don't match registry {expected}")
        print("   Proceeding with dataset classes...")
        conditions  = train_ds.classes
        num_classes = len(conditions)

    train_dl = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,  num_workers=4, pin_memory=True)
    val_dl   = DataLoader(val_ds,   batch_size=args.batch_size, shuffle=False, num_workers=4, pin_memory=True)

    print(f"Train samples: {len(train_ds)}   Val samples: {len(val_ds)}")
    print(f"Class mapping: {dict(zip(train_ds.classes, range(num_classes)))}\n")

    # ── Build model ───────────────────────────────────────────────────────────
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    model = models.densenet121(weights=models.DenseNet121_Weights.IMAGENET1K_V1)
    model.classifier = nn.Linear(model.classifier.in_features, num_classes)

    if args.freeze_backbone:
        print("Freezing backbone — only classifier head will be trained")
        for name, param in model.named_parameters():
            if "classifier" not in name:
                param.requires_grad = False

    model.to(device)

    # ── Training setup ────────────────────────────────────────────────────────
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=args.lr,
    )
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.5)

    best_val_acc = 0.0
    output_path  = Path(__file__).parent / "models" / cfg.model_file

    # ── Training loop ─────────────────────────────────────────────────────────
    for epoch in range(1, args.epochs + 1):
        # Train
        model.train()
        train_loss, train_correct = 0.0, 0
        for images, labels in train_dl:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss    += loss.item() * images.size(0)
            train_correct += (outputs.argmax(1) == labels).sum().item()

        # Validate
        model.eval()
        val_loss, val_correct = 0.0, 0
        with torch.no_grad():
            for images, labels in val_dl:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                val_loss    += criterion(outputs, labels).item() * images.size(0)
                val_correct += (outputs.argmax(1) == labels).sum().item()

        train_acc = train_correct / len(train_ds) * 100
        val_acc   = val_correct   / len(val_ds)   * 100
        train_l   = train_loss    / len(train_ds)
        val_l     = val_loss      / len(val_ds)

        print(
            f"Epoch {epoch:02d}/{args.epochs}  "
            f"Train loss={train_l:.4f} acc={train_acc:.1f}%  "
            f"Val loss={val_l:.4f} acc={val_acc:.1f}%"
            + ("  ← best ✅" if val_acc > best_val_acc else "")
        )

        # Save best checkpoint
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            output_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), str(output_path))

        scheduler.step()

    print(f"\n✅ Training complete!")
    print(f"   Best val accuracy : {best_val_acc:.1f}%")
    print(f"   Saved model to    : {output_path}")
    print(f"\nRestart the backend — it will auto-load the new weights from {cfg.model_file}\n")


if __name__ == "__main__":
    main()
