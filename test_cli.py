#!/usr/bin/env python3
"""
Quick Test CLI for ImgPre
=========================
Interactive tool for testing ImgPre preprocessing with different settings.

Usage:
    python test_cli.py                          # Interactive mode
    python test_cli.py image.jpg                # Quick test with defaults
    python test_cli.py image.jpg --scale 0.5    # Test with specific scale
    python test_cli.py image.jpg --all-scales   # Test multiple scales at once
"""
import argparse
import os
import sys
import time
from PIL import Image

from ImgPre import process_image, get_sharpness_score, to_rgb


def get_image_info(path):
    """Return a dict with image metadata."""
    img = Image.open(path)
    rgb = to_rgb(img)
    sharpness = get_sharpness_score(rgb)
    file_size = os.path.getsize(path)
    return {
        "path": path,
        "width": img.width,
        "height": img.height,
        "mode": img.mode,
        "format": img.format,
        "megapixels": round(img.width * img.height / 1_000_000, 2),
        "file_size_mb": round(file_size / (1024 * 1024), 2),
        "sharpness": round(sharpness, 2),
    }


def print_info(info, label="Image"):
    """Pretty-print image info."""
    print(f"\n  {label}:")
    print(f"    Path       : {info['path']}")
    print(f"    Dimensions : {info['width']} x {info['height']} px")
    print(f"    Megapixels : {info['megapixels']} MP")
    print(f"    Mode       : {info['mode']} | Format: {info['format'] or 'N/A'}")
    print(f"    File Size  : {info['file_size_mb']} MB")
    print(f"    Sharpness  : {info['sharpness']}")


def print_comparison(input_info, output_info, elapsed):
    """Print before/after comparison table."""
    print(f"\n  {'':=<60}")
    print(f"  {'Metric':<20} {'Input':>15} {'Output':>15} {'Change':>10}")
    print(f"  {'':-<60}")
    print(f"  {'Dimensions':<20} {input_info['width']}x{input_info['height']:>10} {output_info['width']}x{output_info['height']:>10}")
    print(f"  {'Megapixels':<20} {input_info['megapixels']:>15} {output_info['megapixels']:>15}")
    print(f"  {'File Size (MB)':<20} {input_info['file_size_mb']:>15} {output_info['file_size_mb']:>15}")
    print(f"  {'Sharpness':<20} {input_info['sharpness']:>15} {output_info['sharpness']:>15}")

    ratio = (output_info['width'] * output_info['height']) / (input_info['width'] * input_info['height'])
    print(f"  {'Pixel Ratio':<20} {'':>15} {ratio:>14.1%}")
    print(f"  {'Processing Time':<20} {'':>15} {elapsed:>13.2f}s")
    print(f"  {'':=<60}")


def run_test(input_path, output_path, scale=None, max_width=1920, max_height=1080,
             threshold=2000, dpi=300, label=None):
    """Run a single preprocessing test and print results."""
    tag = label or (f"scale={scale}" if scale else "perceptual-auto")
    print(f"\n{'#' * 64}")
    print(f"  TEST: {tag}")
    print(f"{'#' * 64}")

    input_info = get_image_info(input_path)
    print_info(input_info, "Input")

    print(f"\n  Processing...")
    start = time.time()
    result_size = process_image(
        input_path, output_path,
        max_screen_w=max_width,
        max_screen_h=max_height,
        screen_threshold=threshold,
        dpi=dpi,
        scale=scale,
    )
    elapsed = time.time() - start

    output_info = get_image_info(output_path)
    print_info(output_info, "Output")
    print_comparison(input_info, output_info, elapsed)
    print(f"\n  Saved to: {output_path}")
    return output_info


def run_all_scales(input_path, output_dir, scales=None, **kwargs):
    """Test multiple scale values and compare results."""
    if scales is None:
        scales = [0.25, 0.5, 0.75, 1.0]

    os.makedirs(output_dir, exist_ok=True)

    base = os.path.splitext(os.path.basename(input_path))[0]
    ext = os.path.splitext(input_path)[1]

    results = []

    # Also run perceptual-auto mode
    auto_output = os.path.join(output_dir, f"{base}_auto{ext}")
    print("\n" + "=" * 64)
    print("  MULTI-SCALE COMPARISON TEST")
    print("=" * 64)

    info = run_test(input_path, auto_output, scale=None, label="Perceptual Auto", **kwargs)
    results.append(("auto", info))

    for s in scales:
        output_path = os.path.join(output_dir, f"{base}_scale{s}{ext}")
        info = run_test(input_path, output_path, scale=s, label=f"Scale {s}", **kwargs)
        results.append((str(s), info))

    # Summary table
    print(f"\n\n{'=' * 72}")
    print(f"  SUMMARY: {input_path}")
    print(f"{'=' * 72}")
    print(f"  {'Scale':<10} {'Dimensions':>15} {'MP':>8} {'Size(MB)':>10} {'Sharpness':>12}")
    print(f"  {'-' * 55}")
    for label, info in results:
        dims = f"{info['width']}x{info['height']}"
        print(f"  {label:<10} {dims:>15} {info['megapixels']:>8} {info['file_size_mb']:>10} {info['sharpness']:>12}")
    print(f"{'=' * 72}\n")


def interactive_mode():
    """Run in interactive prompt mode."""
    print("\n" + "=" * 50)
    print("  ImgPre — Quick Test CLI (Interactive)")
    print("=" * 50)

    input_path = input("\n  Input image path: ").strip().strip('"').strip("'")
    if not os.path.exists(input_path):
        print(f"  Error: '{input_path}' not found.")
        return

    info = get_image_info(input_path)
    print_info(info, "Input Image")

    print("\n  Test modes:")
    print("    1) Perceptual auto (default pipeline)")
    print("    2) Scale factor (0.0 - 1.0)")
    print("    3) Multi-scale comparison (auto + 0.25, 0.5, 0.75, 1.0)")
    print("    4) Custom parameters")

    choice = input("\n  Choose mode [1-4] (default: 1): ").strip() or "1"

    base = os.path.splitext(os.path.basename(input_path))[0]
    ext = os.path.splitext(input_path)[1] or ".jpg"

    if choice == "1":
        output_path = f"{base}_test_auto{ext}"
        run_test(input_path, output_path)

    elif choice == "2":
        scale = float(input("  Scale factor (0.0-1.0): ").strip())
        if not 0.0 < scale <= 1.0:
            print("  Error: Scale must be between 0.0 (exclusive) and 1.0 (inclusive)")
            return
        output_path = f"{base}_test_s{scale}{ext}"
        run_test(input_path, output_path, scale=scale)

    elif choice == "3":
        output_dir = f"{base}_test_results"
        run_all_scales(input_path, output_dir)

    elif choice == "4":
        scale_str = input("  Scale (leave empty for auto): ").strip()
        scale = float(scale_str) if scale_str else None
        max_w = int(input("  Max width [1920]: ").strip() or "1920")
        max_h = int(input("  Max height [1080]: ").strip() or "1080")
        threshold = int(input("  Screen threshold [2000]: ").strip() or "2000")
        dpi = int(input("  DPI [300]: ").strip() or "300")

        tag = f"s{scale}" if scale else "auto"
        output_path = f"{base}_test_{tag}{ext}"
        run_test(input_path, output_path, scale=scale,
                 max_width=max_w, max_height=max_h, threshold=threshold, dpi=dpi)
    else:
        print("  Invalid choice.")


def main():
    parser = argparse.ArgumentParser(
        prog="test_cli",
        description="ImgPre Quick Test CLI — test preprocessing with different settings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_cli.py                                 # Interactive mode
  python test_cli.py photo.jpg                       # Perceptual auto test
  python test_cli.py photo.jpg --scale 0.5           # Scale to 50%%
  python test_cli.py photo.jpg --scale 0.3 -o out.jpg
  python test_cli.py photo.jpg --all-scales          # Compare all scales
  python test_cli.py photo.jpg --all-scales --scales 0.1 0.25 0.5 0.75
        """,
    )
    parser.add_argument("input", nargs="?", help="Input image path")
    parser.add_argument("-o", "--output", help="Output image path (auto-generated if omitted)")
    parser.add_argument("--scale", type=float, help="Scale factor 0.0-1.0")
    parser.add_argument("--all-scales", action="store_true",
                        help="Run multi-scale comparison (auto + multiple scales)")
    parser.add_argument("--scales", type=float, nargs="+", default=[0.25, 0.5, 0.75, 1.0],
                        help="Scale values for --all-scales (default: 0.25 0.5 0.75 1.0)")
    parser.add_argument("--max-width", type=int, default=1920, help="Max output width (default: 1920)")
    parser.add_argument("--max-height", type=int, default=1080, help="Max output height (default: 1080)")
    parser.add_argument("--threshold", type=int, default=2000, help="Screen-fit threshold (default: 2000)")
    parser.add_argument("--dpi", type=int, default=300, help="Output DPI (default: 300)")

    args = parser.parse_args()

    if args.scale is not None and not (0.0 < args.scale <= 1.0):
        parser.error("--scale must be between 0.0 (exclusive) and 1.0 (inclusive)")

    # No input → interactive mode
    if not args.input:
        interactive_mode()
        return

    if not os.path.exists(args.input):
        print(f"Error: '{args.input}' not found.")
        sys.exit(1)

    common_kwargs = dict(
        max_width=args.max_width,
        max_height=args.max_height,
        threshold=args.threshold,
        dpi=args.dpi,
    )

    # Multi-scale comparison
    if args.all_scales:
        base = os.path.splitext(os.path.basename(args.input))[0]
        output_dir = args.output or f"{base}_test_results"
        run_all_scales(args.input, output_dir, scales=args.scales, **common_kwargs)
        return

    # Single test
    if args.output:
        output_path = args.output
    else:
        base = os.path.splitext(os.path.basename(args.input))[0]
        ext = os.path.splitext(args.input)[1] or ".jpg"
        tag = f"s{args.scale}" if args.scale else "auto"
        output_path = f"{base}_test_{tag}{ext}"

    run_test(args.input, output_path, scale=args.scale, **common_kwargs)


if __name__ == "__main__":
    main()
