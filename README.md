# ImgPre — Perceptual Image Preprocessor

A Python package that intelligently resizes images based on **perceptual sharpness**, not fixed pixel dimensions. It ensures every image reaches its optimal visual quality before saving.

## Features

- **Adaptive sharpness target** — each image targets 1.5× its own baseline sharpness
- **Diminishing returns detection** — stops scaling when quality improvements plateau
- **Minimum size guard** — never crushes images below 500px
- **20MP pre-scaling** — handles massive images without memory crashes
- **Screen boundary fitting** — optional max output dimensions (default: 1920×1080)
- **Batch processing** — process entire folders in one call

## Installation

```bash
pip install ImgPre
```

Or install from source:

```bash
git clone https://github.com/maheshprintarts/ImgPre.git
cd ImgPre
pip install -e .
```

## Usage

### As a Python module

```python
from ImgPre import process_image, process_batch

# Process a single image
process_image('photo.jpg', 'output.jpg')

# Batch process a folder
results = process_batch('input_images/', 'processed_images/')
for filename, result in results.items():
    print(f"{filename}: {result['status']} -> {result.get('size')}")
```

### Advanced options

```python
process_image(
    'photo.jpg',
    'output.jpg',
    max_screen_w=1920,    # Max output width
    max_screen_h=1080,    # Max output height
    screen_threshold=2000, # Apply screen fitting only if > this px
    dpi=300               # DPI metadata to embed
)
```

### Command Line

```bash
imgpre --input input_images/ --output processed_images/
```

## License

MIT
