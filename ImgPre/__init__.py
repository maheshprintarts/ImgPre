"""
ImgPre — Perceptual Image Preprocessor
=======================================
A Python package for intelligently resizing images based on perceptual sharpness
rather than fixed pixel dimensions.

Usage:
    from ImgPre import process_image, process_batch

    # Process a single image
    process_image('input.jpg', 'output.jpg')

    # Process a folder of images
    process_batch('input_images/', 'processed_images/')
"""

from .processor import (
    process_image,
    process_batch,
    optimize_image_size,
    progressive_resize,
    get_sharpness_score,
    get_edge_density,
    to_rgb,
)

__version__ = "1.0.0"
__author__ = "maheshprintarts"
__all__ = [
    "process_image",
    "process_batch",
    "optimize_image_size",
    "progressive_resize",
    "get_sharpness_score",
    "get_edge_density",
    "to_rgb",
]
