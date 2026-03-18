from PIL import Image
import os
import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)


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


def optimize_image_size(img, step=0.98, is_prescaled=False, min_short_side=500,
                        target_multiplier=1.5, max_no_improvement_steps=8):
    """
    Dynamically scales image down until perceptual quality peak is reached.

    Uses:
    - Adaptive relative target (target_multiplier × own baseline sharpness)
    - Diminishing returns detection (stops if improvement < 0.5% for N steps)
    - Minimum size guard (never crush below min_short_side pixels)
    """
    current_img = img
    score = get_sharpness_score(current_img)

    min_absolute_target = 400.0
    relative_target = score * target_multiplier
    target_score = max(relative_target, min_absolute_target)

    if is_prescaled and score > min_absolute_target:
        target_score = score * 1.05

    prev_score = score
    no_improvement_count = 0

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


# Modes that need special handling when converting to RGB
_MODES_NEEDING_ALPHA_FLATTEN = ('RGBA', 'LA', 'PA')


def to_rgb(img):
    """
    Converts any PIL image to RGB color space.
    Handles: CMYK, Grayscale (L), Palette (P), RGBA (flattened on white),
             YCbCr, LAB, HSV, float (F), integer (I), and others.
    """
    mode = img.mode

    if mode == 'RGB':
        return img

    # Modes with alpha: flatten onto a white background before converting
    if mode in _MODES_NEEDING_ALPHA_FLATTEN:
        bg = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'PA':
            img = img.convert('RGBA')
        # Paste using alpha channel as mask
        alpha = img.split()[-1]
        bg.paste(img.convert('RGB'), mask=alpha)
        return bg

    # All other modes: Pillow handles most directly
    return img.convert('RGB')


def find_effective_resolution(img, threshold=0.998, analysis_max=2000):
    """
    Detects the image's true information content using downscale-upscale roundtrip.

    Principle: downscale to X%, upscale back, compare with original.
    If quality stays above threshold, those pixels were interpolated/redundant.
    Binary search finds the smallest X where real information is preserved.

    Works on a ~2000px analysis copy for speed (< 0.5s on any image).

    Returns:
        float: Effective resolution ratio (0.0-1.0) relative to input dimensions.
               e.g. 0.85 means image only has real information at 85% of its pixel size.
    """
    aw, ah = img.size

    # Downscale to analysis size for fast computation
    if max(aw, ah) > analysis_max:
        ratio = analysis_max / max(aw, ah)
        aw_a, ah_a = max(1, int(aw * ratio)), max(1, int(ah * ratio))
        analysis_img = img.resize((aw_a, ah_a), Image.Resampling.LANCZOS)
    else:
        aw_a, ah_a = aw, ah
        analysis_img = img

    original_arr = np.array(analysis_img, dtype=np.float32)

    low, high = 0.1, 1.0
    for _ in range(10):  # 10 iterations of binary search -> ~0.1% precision
        mid = (low + high) / 2.0
        test_w = max(1, int(aw_a * mid))
        test_h = max(1, int(ah_a * mid))

        # Roundtrip: downscale then upscale back
        small = analysis_img.resize((test_w, test_h), Image.Resampling.LANCZOS)
        restored = small.resize((aw_a, ah_a), Image.Resampling.LANCZOS)

        # MSE-based quality metric (1.0 = identical)
        restored_arr = np.array(restored, dtype=np.float32)
        mse = np.mean((original_arr - restored_arr) ** 2)
        quality = 1.0 - mse / 65025.0  # 65025 = 255^2

        if quality >= threshold:
            high = mid  # can go smaller, still retaining quality
        else:
            low = mid   # lost too much, need more pixels

    return high


def scale_to_params(scale):
    """
    Maps scale factor (0.1–1.0) to perceptual optimization parameters.

    scale=1.0 → most aggressive optimization (sharpest output)
    scale=0.1 → least optimization (preserves original characteristics)

    Returns dict with: step, target_multiplier, patience, min_short_side
    """
    t = max(0.0, min(1.0, (scale - 0.1) / 0.9))  # normalize to [0, 1]

    return {
        'step': 0.997 - t * 0.017,               # 0.997 (gentle) → 0.98 (aggressive)
        'target_multiplier': 1.05 + t * 0.45,     # 1.05× → 1.5× sharpness target
        'patience': int(2 + t * 6),                # 2 → 8 diminishing-returns steps
        'min_short_side': int(50 + t * 450),       # 50px → 500px floor
    }


def process_image(input_path, output_path, max_screen_w=1920, max_screen_h=1080, screen_threshold=2000, dpi=300, scale=None):
    """
    Full pipeline for a SINGLE image:
    1. Open image (any format/color space)
    2. Convert to RGB color space
    3. Pre-scale if >20MP
    4. Perceptual sharpness optimization (intensity modulated by scale)
    5. Proportional resize to target (if scale provided) OR screen fitting
    6. Save at specified DPI

    When scale is provided (0.1–1.0):
        - scale=1.0: full optimization, output = original dimensions
        - scale=0.5: moderate optimization, output = 50% of original
        - scale=0.1: minimal optimization, output = 10% of original
        - Screen fitting is bypassed (user controls size via scale)

    When scale is None:
        - Full perceptual optimization + screen boundary fitting (original behavior)

    Parameters:
        input_path (str): Path to the source image.
        output_path (str): Path to save the processed image.
        max_screen_w (int): Maximum output width for screen fitting (default: 1920).
        max_screen_h (int): Maximum output height for screen fitting (default: 1080).
        screen_threshold (int): Apply screen fitting if either dim > this (default: 2000).
        dpi (int): DPI metadata to embed in the saved file (default: 300).
        scale (float): Preprocessing scale 0.1–1.0. Controls both optimization
                       intensity and proportional output size.

    Returns:
        tuple: Final (width, height) of the saved image.
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
            with img_obj as raw:
                # Step 1: Normalize ALL image types to RGB
                img = to_rgb(raw)
                original_w, original_h = img.width, img.height

                total_pixels = img.width * img.height

                if scale is not None:
                    # Step 2a: Detect effective resolution (real information ceiling)
                    # Uses fast roundtrip analysis on ~2000px working copy
                    eff_ratio = find_effective_resolution(img)
                    eff_w = max(1, int(original_w * eff_ratio))
                    eff_h = max(1, int(original_h * eff_ratio))
                    logger.info(
                        "Effective resolution: %.1f%% -> %dx%d (of %dx%d original)",
                        eff_ratio * 100, eff_w, eff_h, original_w, original_h,
                    )

                    # Target = effective_resolution * scale (never exceeds real info)
                    # scale=1.0 -> full effective size (all real pixels, zero fake)
                    # scale=0.5 -> half of effective (always downscaling)
                    target_w = max(1, int(eff_w * scale))
                    target_h = max(1, int(eff_h * scale))

                    # Step 2b: Adaptive pre-scale for memory — 2x headroom above
                    # target for optimizer, capped at 50MP
                    target_pixels = target_w * target_h
                    headroom_pixels = min(int(target_pixels * 2), 50_000_000)
                    working_limit = max(headroom_pixels, 20_000_000)

                    if total_pixels > working_limit:
                        sf = (working_limit / total_pixels) ** 0.5
                        new_w = max(target_w, int(img.width * sf))
                        new_h = max(target_h, int(img.height * sf))
                        img = progressive_resize(img, (new_w, new_h))
                        is_prescaled = True
                    else:
                        is_prescaled = False

                    # Step 3a: Perceptual optimization with scale-modulated intensity
                    params = scale_to_params(scale)
                    logger.info(
                        "Scale %.2f -> step=%.4f, target_mult=%.2f, patience=%d, min_short=%d",
                        scale, params['step'], params['target_multiplier'],
                        params['patience'], params['min_short_side'],
                    )

                    optimized = optimize_image_size(
                        img,
                        step=params['step'],
                        is_prescaled=is_prescaled,
                        min_short_side=params['min_short_side'],
                        target_multiplier=params['target_multiplier'],
                        max_no_improvement_steps=params['patience'],
                    )

                    if optimized.size != img.size:
                        img = progressive_resize(img, optimized.size)
                    else:
                        img = optimized

                    # Step 3b: Resize to target (always downscaling — zero fake pixels)
                    if img.size != (target_w, target_h):
                        img = progressive_resize(img, (target_w, target_h))

                    logger.info(
                        "Output: %dx%d (%.1f%% of effective %dx%d, %.1f%% of original %dx%d)",
                        img.width, img.height,
                        100.0 * scale, eff_w, eff_h,
                        100.0 * img.width * img.height / (original_w * original_h),
                        original_w, original_h,
                    )
                else:
                    # Step 2: Pre-scale if >20MP to avoid memory issues
                    if total_pixels > 20_000_000:
                        scale_factor = (20_000_000 / total_pixels) ** 0.5
                        safe_scale_factor = scale_factor * 0.95
                        new_w = max(1, int(img.width * safe_scale_factor))
                        new_h = max(1, int(img.height * safe_scale_factor))
                        img = progressive_resize(img, (new_w, new_h))
                        is_prescaled = True
                    else:
                        is_prescaled = False

                    # Step 3: Perceptual sharpness optimization (works on RGB)
                    optimized = optimize_image_size(img, step=0.98, is_prescaled=is_prescaled)

                    if optimized.size != img.size:
                        img = progressive_resize(img, optimized.size)
                    else:
                        img = optimized

                    # Step 4: Screen boundary fitting
                    if img.width > screen_threshold or img.height > screen_threshold:
                        scale_fit = min(max_screen_w / img.width, max_screen_h / img.height)
                        fit_w = max(1, int(img.width * scale_fit))
                        fit_h = max(1, int(img.height * scale_fit))
                        img = img.resize((fit_w, fit_h), Image.Resampling.LANCZOS)

                # Step 5: Save — format-aware, always RGB
                ext = os.path.splitext(output_path)[1].lower()
                if ext in ('.jpg', '.jpeg'):
                    img.save(output_path, dpi=(dpi, dpi), quality=100,
                             subsampling=0, optimize=True, progressive=True)
                elif ext == '.png':
                    img.save(output_path, dpi=(dpi, dpi), optimize=True)
                else:
                    img.save(output_path, dpi=(dpi, dpi))

                logger.info("Saved: %s (%dx%d @ %d DPI)", output_path, img.width, img.height, dpi)
                return img.size

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
    files = sorted(f for f in os.listdir(input_dir) if f.lower().endswith(valid_extensions))

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
