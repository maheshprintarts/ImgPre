# ImgPre — Perceptual Image Preprocessor

A Python package that intelligently resizes images based on **perceptual sharpness**, not fixed pixel dimensions. Includes a proportional `--scale` mode for direct control over output size.

---

## Features

- **Perceptual optimization** — Adaptive sharpness-based downscaling (Laplacian variance)
- **Proportional scaling** — `--scale 0.5` on a 6000x4000 image outputs 3000x2000
- **All formats supported** — JPG, PNG, BMP, TIFF, GIF, CMYK, Grayscale, RGBA
- **Universal RGB conversion** — Any color space normalized automatically
- **Diminishing returns detection** — Stops when quality improvement plateaus
- **20MP pre-scaling** — Handles massive files (50MP+) without memory crashes
- **Screen boundary fitting** — Auto-fits large images into configurable screen bounds
- **Single image & batch processing** — One file or an entire folder
- **Format-aware saving** — JPEG (quality=100, progressive), PNG (optimized), etc.
- **Quick test CLI** — Interactive tool to compare scales and inspect results

---

## Supported Image Types

| Format | Extensions | Notes |
|---|---|---|
| JPEG | `.jpg`, `.jpeg` | quality=100, progressive encoding |
| PNG | `.png` | Transparency flattened to white background |
| BMP | `.bmp` | Supported |
| TIFF | `.tiff` | Supported |
| CMYK | `.jpg` (Photoshop/print) | Auto-converted to RGB |
| Grayscale | `.jpg`, `.png` | Auto-converted to RGB |
| RGBA | `.png` | Transparency → white background → RGB |

---

## Installation

**From GitHub:**

```bash
pip install git+https://github.com/maheshprintarts/ImgPre.git
```

**From source (development):**

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

---

## Quick Start

```bash
# Perceptual auto-optimization (default)
imgpre input.jpg output.jpg

# Scale to 50% of original dimensions
imgpre input.jpg output.jpg --scale 0.5

# Batch process a folder
imgpre --batch -i input_folder/ -o output_folder/

# Batch with scaling
imgpre --batch -i input_folder/ -o output_folder/ --scale 0.75
```

---

## CLI Reference

### `imgpre` — Main Preprocessor

```
imgpre [input] [output] [options]
```

#### Positional Arguments

| Argument | Description |
|---|---|
| `input` | Input image file path (single image mode) |
| `output` | Output image file path (single image mode) |

#### Options

| Option | Type | Default | Description |
|---|---|---|---|
| `--scale` | float | `None` | Proportional scale factor (0.0–1.0). Bypasses perceptual optimization. |
| `--max-width` | int | `1920` | Maximum output width for screen fitting |
| `--max-height` | int | `1080` | Maximum output height for screen fitting |
| `--threshold` | int | `2000` | Screen-fit triggers when either dimension exceeds this value |
| `--dpi` | int | `300` | DPI metadata embedded in the output file |
| `--batch` | flag | — | Enable batch mode (process an entire folder) |
| `--input-dir`, `-i` | str | — | Input folder (required in batch mode) |
| `--output-dir`, `-o` | str | — | Output folder (required in batch mode) |

#### Scale Behavior

| Input Size | `--scale` | Output Size |
|---|---|---|
| 6900 x 10800 | `0.5` | 3450 x 5400 |
| 5000 x 5000 | `0.25` | 1250 x 1250 |
| 4000 x 3000 | `0.75` | 3000 x 2250 |
| 4000 x 3000 | `1.0` | 4000 x 3000 (no resize, just optimized save) |
| 4000 x 3000 | *(omitted)* | Perceptual auto — size determined by sharpness analysis |

### Examples

```bash
# Default perceptual optimization
imgpre photo.jpg optimized.jpg

# Half-size output
imgpre photo.jpg half.jpg --scale 0.5

# Quarter-size with custom DPI
imgpre photo.jpg quarter.jpg --scale 0.25 --dpi 150

# Custom screen bounds
imgpre photo.jpg fitted.jpg --max-width 2560 --max-height 1440 --threshold 3000

# Batch: scale all images to 30%
imgpre --batch -i raw_photos/ -o scaled/ --scale 0.3
```

---

## Quick Test CLI

A standalone test tool for quick experimentation and comparison.

### Usage

```bash
# Interactive mode (prompts for everything)
python test_cli.py

# Quick test with perceptual auto
python test_cli.py photo.jpg

# Test specific scale
python test_cli.py photo.jpg --scale 0.5

# Custom output path
python test_cli.py photo.jpg --scale 0.5 -o my_output.jpg

# Multi-scale comparison (auto + 0.25, 0.5, 0.75, 1.0)
python test_cli.py photo.jpg --all-scales

# Custom scale values for comparison
python test_cli.py photo.jpg --all-scales --scales 0.1 0.3 0.5 0.8
```

### Interactive Mode

Run without arguments to enter interactive mode:

```
$ python test_cli.py

  ImgPre — Quick Test CLI (Interactive)

  Input image path: photo.jpg

  Input Image:
    Path       : photo.jpg
    Dimensions : 6900 x 10800 px
    Megapixels : 74.52 MP
    Mode       : RGB | Format: JPEG
    File Size  : 12.34 MB
    Sharpness  : 45.67

  Test modes:
    1) Perceptual auto (default pipeline)
    2) Scale factor (0.0 - 1.0)
    3) Multi-scale comparison (auto + 0.25, 0.5, 0.75, 1.0)
    4) Custom parameters

  Choose mode [1-4]:
```

### Multi-Scale Comparison Output

The `--all-scales` flag generates a comparison table:

```
  SUMMARY: photo.jpg
  ========================================================================
  Scale      Dimensions          MP    Size(MB)    Sharpness
  ---------------------------------------------------------------
  auto         1920x1080       2.07        0.85        312.45
  0.25         1725x2700       4.66        1.92        189.34
  0.5          3450x5400      18.63        7.21         78.56
  0.75         5175x8100      41.92       15.84         52.31
  1.0          6900x10800     74.52       28.47         45.67
  ========================================================================
```

---

## Python API

### Single Image

```python
from ImgPre import process_image

# Perceptual auto-optimization
process_image("photo.jpg", "output.jpg")

# Proportional scaling
process_image("photo.jpg", "output.jpg", scale=0.5)

# Full options
process_image(
    "photo.jpg",
    "output.jpg",
    max_screen_w=1920,
    max_screen_h=1080,
    screen_threshold=2000,
    dpi=300,
    scale=0.5,
)
```

### Batch Processing

```python
from ImgPre import process_batch

results = process_batch("input_images/", "processed_images/", scale=0.5)

for filename, result in results.items():
    if result["status"] == "ok":
        print(f"{filename}: {result['size']}")
    else:
        print(f"{filename}: ERROR — {result['error']}")
```

### Utility Functions

```python
from ImgPre import to_rgb, get_sharpness_score, get_edge_density, optimize_image_size
from PIL import Image

img = Image.open("photo.jpg")

# Convert any color space to RGB
rgb = to_rgb(img)

# Measure sharpness (Laplacian variance)
score = get_sharpness_score(rgb)
print(f"Sharpness: {score:.2f}")

# Measure edge density (Canny edge ratio)
density = get_edge_density(rgb)
print(f"Edge density: {density:.4f}")

# Run perceptual optimization only
optimized = optimize_image_size(rgb, step=0.98, min_short_side=500)
print(f"Optimized size: {optimized.size}")
```

---

## How It Works

```
Input Image (any format/color space)
       |
       v
  [1] Convert to RGB
       |  CMYK, Grayscale, RGBA, Palette → RGB
       |  Alpha channels flattened onto white background
       v
  [2] Pre-scale if > 20MP
       |  Reduces memory footprint before processing
       v
  [3] Choose path:
       |
       |-- --scale provided?
       |      YES → Proportional resize (progressive multi-step LANCZOS)
       |      NO  → Perceptual optimization:
       |              - Measure baseline sharpness (Laplacian variance)
       |              - Set target = baseline × 1.5
       |              - Downscale 2% per step until target met
       |              - Stop early if < 0.5% improvement for 8 steps
       |              - Never shrink below 500px on shorter side
       v
  [4] Screen boundary fitting (if no --scale)
       |  If either dimension > threshold (default 2000px),
       |  fit proportionally within max_width × max_height
       v
  [5] Save with format-aware settings
       |  JPEG: quality=100, progressive, optimized
       |  PNG:  optimized compression
       |  DPI metadata embedded (default 300)
       v
Output Image (RGB)
```

---

## License

MIT
