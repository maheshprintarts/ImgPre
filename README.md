# ImgPre — Perceptual Image Preprocessor

A Python package that intelligently resizes images based on **perceptual sharpness**, not fixed pixel dimensions. Every image is scaled down to find its optimal visual quality before saving.

## Features

- ✅ **All image formats supported** — JPG, PNG, BMP, TIFF, GIF, CMYK, Grayscale, RGBA
- ✅ **Universal RGB conversion** — Any color space (CMYK, Grayscale, RGBA, Palette) is normalized to RGB automatically
- ✅ **Adaptive sharpness target** — Each image targets 1.5× its own baseline sharpness (not a fixed number)
- ✅ **Diminishing returns detection** — Stops scaling when quality improvements plateau (< 0.5% for 8 steps)
- ✅ **Minimum size guard** — Never crushes images below 500px on the shorter side
- ✅ **20MP pre-scaling** — Handles massive files (50MP+) without memory crashes
- ✅ **Screen boundary fitting** — Auto-fits images >2000px into 1920×1080
- ✅ **Single image & batch processing** — Process one file or an entire folder
- ✅ **Format-aware saving** — JPEG (quality=100, progressive), PNG (optimize), others saved cleanly

## Supported Image Types

| Format | Extension | Notes |
|---|---|---|
| JPEG | `.jpg`, `.jpeg` | quality=100, progressive encoding |
| PNG | `.png` | Transparency flattened to white background |
| BMP | `.bmp` | Supported |
| TIFF | `.tiff` | Supported |
| CMYK | `.jpg` (Photoshop/print) | Auto-converted to RGB |
| Grayscale | `.jpg`, `.png` | Auto-converted to RGB |
| RGBA transparent | `.png` | Transparency → white background → RGB |

## Installation

```bash
pip install git+https://github.com/maheshprintarts/ImgPre.git
```

Or install from source:

```bash
git clone https://github.com/maheshprintarts/ImgPre.git
cd ImgPre
pip install -e .
```

### Dependencies

```
Pillow>=9.0.0
opencv-python>=4.5.0
numpy>=1.21.0
```

## Usage

### Python API — Single Image

```python
from ImgPre import process_image

# Basic usage
process_image("photo.jpg", "output.jpg")

# With custom options
process_image(
    "photo.jpg",
    "output.jpg",
    max_screen_w=1920,     # Max output width (default: 1920)
    max_screen_h=1080,     # Max output height (default: 1080)
    screen_threshold=2000, # Apply screen fitting if image > this px (default: 2000)
    dpi=300                # DPI metadata to embed (default: 300)
)
```

### Python API — Batch Processing

```python
from ImgPre import process_batch

results = process_batch("input_images/", "processed_images/")

for filename, result in results.items():
    if result["status"] == "ok":
        print(f"{filename}: {result['size']}")
    else:
        print(f"{filename}: ERROR — {result['error']}")
```

### Command Line — Single Image (Default)

```bash
imgpre photo.jpg output.jpg
```

### Command Line — Batch Mode

```bash
imgpre --batch --input-dir input_images/ --output-dir processed_images/
```

### Command Line — All Options

```bash
imgpre photo.jpg output.jpg \
  --max-width 1920 \
  --max-height 1080 \
  --threshold 2000 \
  --dpi 300
```

## How It Works

The pipeline runs these steps for every image:

```
1. Open Image (any format)
       ↓
2. Convert to RGB (CMYK, RGBA, Grayscale, etc. all normalized)
       ↓
3. Pre-Scale if >20MP (prevents memory crashes)
       ↓
4. Perceptual Optimization (downscale 2% per step until sharpness target is met)
       - Adaptive target: image's own sharpness × 1.5
       - Stops early if diminishing returns detected (8 flat steps)
       - Never shrinks below 500px on shorter side
       ↓
5. Screen Fit (if >2000px, proportionally fit within 1920×1080)
       ↓
6. Save (format-aware, 300 DPI)
```

## Advanced Usage

```python
from ImgPre import to_rgb, get_sharpness_score, optimize_image_size
from PIL import Image

# Convert any image to RGB
img = Image.open("cmyk_file.jpg")
rgb_img = to_rgb(img)

# Get sharpness score
score = get_sharpness_score(rgb_img)
print(f"Sharpness: {score:.2f}")

# Run optimization only
optimized = optimize_image_size(rgb_img, step=0.98, min_short_side=500)
```

## License

MIT
