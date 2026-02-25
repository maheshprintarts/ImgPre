from PIL import Image
import os
import cv2
import numpy as np


def get_sharpness_score(pil_img):
    """
    Calculates the Laplacian Variance of a PIL image.
    Higher score = sharper/denser pixels.
    """
    open_cv_image = np.array(pil_img)
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def get_edge_density(pil_img):
    """
    Calculates Edge Density (Canny Edge Pixels / Total Pixels).
    """
    open_cv_image = np.array(pil_img.convert('RGB'))
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    edge_pixels = np.count_nonzero(edges)
    total_pixels = gray.shape[0] * gray.shape[1]
    return edge_pixels / total_pixels


def progressive_resize(img, target_size, step=0.9):
    """
    Resizes an image in multiple steps for higher quality downscaling.
    """
    current_img = img
    target_w, target_h = target_size

    while current_img.width > target_w * 1.1 or current_img.height > target_h * 1.1:
        new_w = max(int(current_img.width * step), target_w)
        new_h = max(int(current_img.height * step), target_h)
        current_img = current_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    if current_img.size != target_size:
        current_img = current_img.resize(target_size, Image.Resampling.LANCZOS)

    return current_img


def optimize_image_size(img, step=0.98, is_prescaled=False, min_short_side=500):
    """
    Dynamically scales image down until perceptual quality peak is reached.

    Uses:
    - Adaptive relative target (1.5x own baseline sharpness)
    - Diminishing returns detection (stops if improvement < 0.5% for 8 steps)
    - Minimum size guard (never crush below min_short_side pixels)
    """
    current_img = img
    score = get_sharpness_score(current_img)

    min_absolute_target = 400.0
    relative_target = score * 1.5
    target_score = max(relative_target, min_absolute_target)

    if is_prescaled and score > min_absolute_target:
        target_score = score * 1.05

    prev_score = score
    no_improvement_count = 0
    max_no_improvement_steps = 8

    while score < target_score:
        short_side = min(current_img.width, current_img.height)
        if short_side <= min_short_side:
            break

        new_width = max(1, int(current_img.width * step))
        new_height = max(1, int(current_img.height * step))
        current_img = current_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        score = get_sharpness_score(current_img)

        improvement = score - prev_score
        if improvement < prev_score * 0.005 and score > prev_score:
            no_improvement_count += 1
            if no_improvement_count >= max_no_improvement_steps:
                break
        else:
            no_improvement_count = 0

        prev_score = score

    return current_img


def process_image(input_path, output_path, max_screen_w=1920, max_screen_h=1080, screen_threshold=2000, dpi=300):
    """
    Full pipeline: open, pre-scale if >20MP, optimize sharpness, screen-fit, save.

    Parameters:
        input_path (str): Path to the source image.
        output_path (str): Path to save the processed image.
        max_screen_w (int): Maximum output width for screen fitting.
        max_screen_h (int): Maximum output height for screen fitting.
        screen_threshold (int): If either dimension exceeds this, apply screen fitting.
        dpi (int): DPI to embed in the saved file metadata.
    """
    try:
        img_obj = None
        try:
            img_obj = Image.open(input_path)
        except Image.DecompressionBombError:
            original_limit = Image.MAX_IMAGE_PIXELS
            Image.MAX_IMAGE_PIXELS = None
            try:
                with Image.open(input_path) as big_img:
                    w, h = big_img.size
                    img_obj = progressive_resize(big_img, (w // 2, h // 2))
            finally:
                Image.MAX_IMAGE_PIXELS = original_limit

        if img_obj:
            with img_obj as img:
                total_pixels = img.width * img.height
                if total_pixels > 20_000_000:
                    scale_factor = (20_000_000 / total_pixels) ** 0.5
                    safe_scale_factor = scale_factor * 0.95
                    new_w = max(1, int(img.width * safe_scale_factor))
                    new_h = max(1, int(img.height * safe_scale_factor))
                    img = progressive_resize(img, (new_w, new_h))
                    is_prescaled = True
                else:
                    is_prescaled = False

                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

                rgb_check = img.convert('RGB')
                optimized_rgb = optimize_image_size(rgb_check, step=0.98, is_prescaled=is_prescaled)

                final_size = optimized_rgb.size
                if final_size != img.size:
                    img = progressive_resize(img, final_size)

                if img.width > screen_threshold or img.height > screen_threshold:
                    scale = min(max_screen_w / img.width, max_screen_h / img.height)
                    fit_w = max(1, int(img.width * scale))
                    fit_h = max(1, int(img.height * scale))
                    img = img.resize((fit_w, fit_h), Image.Resampling.LANCZOS)

                if output_path.lower().endswith(('.jpg', '.jpeg')):
                    final_img = img.convert('RGB')
                    final_img.save(output_path, dpi=(dpi, dpi), quality=100,
                                   subsampling=0, optimize=True, progressive=True)
                else:
                    final_img = img
                    final_img.save(output_path, dpi=(dpi, dpi))

                return final_img.size

    except Exception as e:
        raise RuntimeError(f"Failed to process {input_path}: {e}") from e


def process_batch(input_dir, output_dir, **kwargs):
    """
    Processes all images in input_dir and saves them to output_dir.
    Accepts same keyword arguments as process_image().
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_extensions)]

    results = {}
    for filename in files:
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        try:
            size = process_image(input_path, output_path, **kwargs)
            results[filename] = {'status': 'ok', 'size': size}
        except Exception as e:
            results[filename] = {'status': 'error', 'error': str(e)}

    return results
