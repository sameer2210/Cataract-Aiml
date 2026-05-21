import torch
import torch.nn as nn
import cv2

from PIL import Image

from torchvision import transforms
from torchvision.models import (
    efficientnet_b3,
    EfficientNet_B3_Weights
)

from app.preprocessing import (
    center_black_lens_hough_from_bgr,
    preprocess_lens_with_mask
)

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

checkpoint_path = "weights/best_efficientnet_b3_cataract.pth"

checkpoint = torch.load(
    checkpoint_path,
    map_location=device
)

class_names = checkpoint["class_names"]

IMG_SIZE = checkpoint["img_size"]

num_classes = 4

model = efficientnet_b3(weights=None)

in_features = model.classifier[1].in_features

model.classifier[1] = nn.Linear(
    in_features,
    num_classes
)

model.load_state_dict(
    checkpoint["model_state_dict"]
)

model = model.to(device)

model.eval()

weights = EfficientNet_B3_Weights.IMAGENET1K_V1

imagenet_mean = weights.transforms().mean
imagenet_std = weights.transforms().std

eval_transform = transforms.Compose([
    transforms.Resize((320, 320)),
    transforms.CenterCrop(IMG_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=imagenet_mean,
        std=imagenet_std
    ),
])


def predict_image(image_path):

    img_bgr = cv2.imread(image_path)

    if img_bgr is None:
        raise ValueError(
            f"Could not read image: {image_path}"
        )

    centered_bgr, center_mask = (
        center_black_lens_hough_from_bgr(img_bgr)
    )

    processed_bgr = preprocess_lens_with_mask(
        centered_bgr,
        center_mask
    )

    processed_rgb = cv2.cvtColor(
        processed_bgr,
        cv2.COLOR_BGR2RGB
    )

    processed_pil = Image.fromarray(processed_rgb)

    tensor = eval_transform(
        processed_pil
    ).unsqueeze(0).to(device)

    with torch.no_grad():

        outputs = model(tensor)

        probs = torch.softmax(outputs, dim=1)

        conf, pred_idx = torch.max(
            probs,
            dim=1
        )

    pred_class = class_names[pred_idx.item()]

    confidence = conf.item()

    return pred_class, confidence