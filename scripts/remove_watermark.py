"""
Remove Gemini Veo watermark and edge artifacts from all frames in Animation-jpg.
"""
import glob
import os
import time
from PIL import Image, ImageFilter
import numpy as np

def clean_frames(directory="Animation-jpg"):
    files = sorted(glob.glob(os.path.join(directory, "ezgif-frame-*.jpg")))
    print(f"Found {len(files)} frames to clean in {directory}")
    t0 = time.time()

    for idx, fpath in enumerate(files):
        im = Image.open(fpath)
        arr = np.array(im, dtype=np.float32)
        H_full, W_full, _ = arr.shape

        # 1. Clean bottom-right watermark (Veo text + 4-point Gemini star)
        # Region: y from 860 to 1080, x from 1700 to 1920
        y1, y2 = 860, H_full
        x1, x2 = 1700, W_full
        region = arr[y1:y2, x1:x2]
        H, W, _ = region.shape

        # Clean background model using boundary pixels
        c_top_left = region[:15, :15].mean(axis=(0,1))
        c_top_right = region[:15, -15:].mean(axis=(0,1))
        c_bottom_left = region[-25:-10, :15].mean(axis=(0,1))
        grad_x = c_top_right - c_top_left
        c_bottom_right = c_bottom_left + grad_x

        y_grid = np.linspace(0, 1, H)[:, None, None]
        x_grid = np.linspace(0, 1, W)[None, :, None]

        clean_plane = (c_top_left * (1 - x_grid) + c_top_right * x_grid) * (1 - y_grid) + \
                      (c_bottom_left * (1 - x_grid) + c_bottom_right * x_grid) * y_grid

        mask = np.zeros((H, W), dtype=np.float32)
        # Star coordinates: y from 890 to 1000 (rel 30..140), x from 1730 to 1850 (rel 30..150)
        mask[25:145, 25:155] = 1.0
        # Veo + bottom right corner: y from 1025 to 1080 (rel 165..H), x from 1800 to 1920 (rel 100..W)
        mask[165:H, 95:W] = 1.0

        # Smooth boundary with Gaussian blur for seamless blend
        mask_pil = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(8))
        smooth_mask = np.array(mask_pil, dtype=np.float32)[:, :, None] / 255.0

        blended = region * (1.0 - smooth_mask) + clean_plane * smooth_mask
        arr[y1:y2, x1:x2] = blended

        # 2. Clean 0-5px top and bottom black conversion artifacts
        arr[H_full-6:H_full, :] = arr[H_full-7:H_full-6, :]
        arr[0:5, :] = arr[5:6, :]

        # 3. Clean 0-2px left/right border artifacts
        arr[:, 0:2] = arr[:, 2:3]
        arr[:, W_full-2:W_full] = arr[:, W_full-3:W_full-2]

        # Save back with high JPEG quality
        out_im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        out_im.save(fpath, format="JPEG", quality=95, subsampling=0)

        if (idx + 1) % 40 == 0 or idx == len(files) - 1:
            print(f"Processed {idx + 1}/{len(files)} frames ({time.time() - t0:.1f}s)")

    print(f"All {len(files)} frames cleaned successfully in {time.time() - t0:.2f}s.")

if __name__ == "__main__":
    clean_frames()
