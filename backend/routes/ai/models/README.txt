# Place trained model weights here.
#
# File naming convention:
#   <body_part>.pth     e.g. chest.pth, knee.pth, hand.pth, spine.pth
#
# Each .pth file must be a PyTorch state_dict for a DenseNet121 with the
# correct number of output classes for that body part (see body_parts.py).
#
# If a .pth file is missing, the system falls back to ImageNet weights.
