import cv2
import numpy as np
from PIL import Image

def center_black_lens_hough_from_bgr(image_bgr, extra_radius=3):

    h, w = image_bgr.shape[:2]

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.medianBlur(gray, 5)

    circles = cv2.HoughCircles(
        gray_blur,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=h // 4,
        param1=100,
        param2=30,
        minRadius=max(1, h // 10),
        maxRadius=max(1, h // 3)
    )

    if circles is None:
        x, y = w // 2, h // 2
        r = int(0.38 * min(h, w))
    else:
        circles = np.uint16(np.around(circles))
        x, y, r = circles[0][0]

    r_mask = int(min(r + extra_radius, min(h, w) // 2))
    r_mask = max(r_mask, 1)

    mask = np.zeros((h, w), dtype=np.uint8)

    cv2.circle(mask, (int(x), int(y)), r_mask, 255, -1)

    masked_bgr = cv2.bitwise_and(image_bgr, image_bgr, mask=mask)

    ys, xs = np.where(mask > 0)

    if len(xs) == 0 or len(ys) == 0:
        roi = masked_bgr
    else:
        ymin, ymax = ys.min(), ys.max()
        xmin, xmax = xs.min(), xs.max()
        roi = masked_bgr[ymin:ymax + 1, xmin:xmax + 1]

    centered_bgr = np.zeros_like(image_bgr)

    roi_h, roi_w = roi.shape[:2]

    start_y = max((h - roi_h) // 2, 0)
    start_x = max((w - roi_w) // 2, 0)

    end_y = min(start_y + roi_h, h)
    end_x = min(start_x + roi_w, w)

    roi = roi[:end_y - start_y, :end_x - start_x]

    centered_bgr[start_y:end_y, start_x:end_x] = roi

    center_mask = np.zeros((h, w), dtype=np.uint8)

    cv2.circle(center_mask, (w // 2, h // 2), r_mask, 255, -1)

    return centered_bgr, center_mask


def preprocess_lens_with_mask(
    lens_bgr,
    lens_mask,
    clahe_clip=2.0,
    clahe_grid=(8, 8),
    use_denoise=False
):

    if lens_bgr is None or lens_bgr.size == 0:
        return lens_bgr

    lab = cv2.cvtColor(lens_bgr, cv2.COLOR_BGR2LAB)

    L, A, B = cv2.split(lab)

    clahe = cv2.createCLAHE(
        clipLimit=clahe_clip,
        tileGridSize=clahe_grid
    )

    L_clahe = clahe.apply(L)

    L_processed = L.copy()

    L_processed[lens_mask > 0] = L_clahe[lens_mask > 0]

    if use_denoise:
        L_processed = cv2.GaussianBlur(L_processed, (3, 3), 0)

    lab_processed = cv2.merge((L_processed, A, B))

    processed_bgr = cv2.cvtColor(
        lab_processed,
        cv2.COLOR_LAB2BGR
    )

    return processed_bgr