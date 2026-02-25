"""
Command-line interface for ImgPre.

Default usage (single image):
    imgpre input.jpg output.jpg

Batch usage:
    imgpre --batch --input input_folder/ --output output_folder/
"""
import argparse
import os
from . import process_image, process_batch


def main():
    parser = argparse.ArgumentParser(
        prog="imgpre",
        description="ImgPre — Perceptual Image Preprocessor"
    )

    # --- Default: single image mode ---
    parser.add_argument("input", nargs="?", help="Input image file (single image mode)")
    parser.add_argument("output", nargs="?", help="Output image file (single image mode)")

    # --- Optional: batch mode ---
    parser.add_argument("--batch", action="store_true", help="Enable batch mode (process a folder)")
    parser.add_argument("--input-dir", "-i", help="Input folder (batch mode)")
    parser.add_argument("--output-dir", "-o", help="Output folder (batch mode)")

    # --- Shared options ---
    parser.add_argument("--max-width", type=int, default=1920, help="Max output width (default: 1920)")
    parser.add_argument("--max-height", type=int, default=1080, help="Max output height (default: 1080)")
    parser.add_argument("--threshold", type=int, default=2000, help="Screen-fit threshold in px (default: 2000)")
    parser.add_argument("--dpi", type=int, default=300, help="Output DPI (default: 300)")

    args = parser.parse_args()

    kwargs = dict(
        max_screen_w=args.max_width,
        max_screen_h=args.max_height,
        screen_threshold=args.threshold,
        dpi=args.dpi,
    )

    # --- Batch mode ---
    if args.batch:
        if not args.input_dir or not args.output_dir:
            parser.error("--batch requires --input-dir and --output-dir")
        if not os.path.exists(args.input_dir):
            print(f"Error: Input folder '{args.input_dir}' does not exist.")
            return
        print(f"ImgPre [Batch] — '{args.input_dir}' -> '{args.output_dir}'")
        results = process_batch(args.input_dir, args.output_dir, **kwargs)
        ok = sum(1 for r in results.values() if r['status'] == 'ok')
        err = sum(1 for r in results.values() if r['status'] == 'error')
        print(f"\nDone! {ok} processed, {err} errors.")
        for filename, result in results.items():
            if result['status'] == 'error':
                print(f"  ERROR: {filename} — {result['error']}")
        return

    # --- Default: single image mode ---
    if not args.input or not args.output:
        parser.print_help()
        print("\nExample: imgpre photo.jpg output.jpg")
        return

    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' does not exist.")
        return

    print(f"ImgPre — Processing '{args.input}' -> '{args.output}'")
    try:
        size = process_image(args.input, args.output, **kwargs)
        print(f"Done! Saved: {args.output} ({size[0]}x{size[1]} @ {args.dpi} DPI)")
    except RuntimeError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
