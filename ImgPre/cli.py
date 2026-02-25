"""
Command-line interface for ImgPre.
Usage: imgpre --input <dir> --output <dir>
"""
import argparse
import os
from . import process_batch


def main():
    parser = argparse.ArgumentParser(
        prog="imgpre",
        description="ImgPre — Perceptual Image Preprocessor"
    )
    parser.add_argument("--input", "-i", required=True, help="Input folder of images")
    parser.add_argument("--output", "-o", required=True, help="Output folder for processed images")
    parser.add_argument("--max-width", type=int, default=1920, help="Max output width (default: 1920)")
    parser.add_argument("--max-height", type=int, default=1080, help="Max output height (default: 1080)")
    parser.add_argument("--threshold", type=int, default=2000, help="Screen-fit threshold in px (default: 2000)")
    parser.add_argument("--dpi", type=int, default=300, help="Output DPI (default: 300)")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input folder '{args.input}' does not exist.")
        return

    print(f"ImgPre — Processing images in '{args.input}' -> '{args.output}'")
    results = process_batch(
        args.input,
        args.output,
        max_screen_w=args.max_width,
        max_screen_h=args.max_height,
        screen_threshold=args.threshold,
        dpi=args.dpi,
    )

    ok = sum(1 for r in results.values() if r['status'] == 'ok')
    err = sum(1 for r in results.values() if r['status'] == 'error')
    print(f"\nDone! {ok} processed, {err} errors.")

    for filename, result in results.items():
        if result['status'] == 'error':
            print(f"  ERROR: {filename} — {result['error']}")


if __name__ == "__main__":
    main()
