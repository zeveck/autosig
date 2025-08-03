#!/usr/bin/env python3
"""
AutoSig - Automatic signature placement on image files
Processes PSD/PNG files in a directory and adds a signature (PSD/PNG) with customizable positioning and file handling
"""

__version__ = "0.2.0"

import os
import sys
import argparse
import warnings
from pathlib import Path
from PIL import Image
from psd_tools import PSDImage
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from tqdm import tqdm

# Suppress harmless PSD library warnings about unknown resources
warnings.filterwarnings("ignore", message="Unknown image resource.*")


def load_image_file(file_path):
    """
    Load an image file (PSD or PNG) and return as PIL Image
    
    Args:
        file_path (str): Path to image file
        
    Returns:
        PIL.Image: Loaded image in RGBA format
    """
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.psd':
        # Suppress stdout/stderr during PSD loading to hide unknown resource warnings
        with redirect_stderr(StringIO()), redirect_stdout(StringIO()):
            psd = PSDImage.open(file_path)
            return psd.composite().convert("RGBA")
    else:
        return Image.open(file_path).convert("RGBA")


def generate_output_path(input_path, suffix, output_format):
    """
    Generate output filename with suffix and format extension
    
    Args:
        input_path (Path): Original file path
        suffix (str): Suffix to add before extension
        output_format (str): Output format (png, jpg, webp, tiff)
        
    Returns:
        Path: Output path with suffix and format extension
    """
    # Map format to file extension
    format_extensions = {
        'png': '.png',
        'jpg': '.jpg',
        'jpeg': '.jpg',
        'webp': '.webp',
        'tiff': '.tiff'
    }
    
    extension = format_extensions.get(output_format.lower(), '.png')
    
    if suffix:
        return input_path.with_name(f"{input_path.stem}{suffix}{extension}")
    else:
        return input_path.with_name(f"{input_path.stem}{extension}")


def save_image_with_format(image, output_path, output_format, quality):
    """
    Save image in specified format with appropriate settings
    
    Args:
        image (PIL.Image): Image to save
        output_path (Path): Output file path
        output_format (str): Output format (png, jpg, webp, tiff)
        quality (int): Quality setting for lossy formats (1-100)
    """
    # Convert format to PIL format name
    pil_formats = {
        'png': 'PNG',
        'jpg': 'JPEG',
        'jpeg': 'JPEG', 
        'webp': 'WEBP',
        'tiff': 'TIFF'
    }
    
    pil_format = pil_formats.get(output_format.lower(), 'PNG')
    
    # Handle transparency for JPG (composite on white background)
    if output_format.lower() in ['jpg', 'jpeg']:
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            # Create white background
            background = Image.new('RGB', image.size, 'white')
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Save JPG with quality
        image.save(output_path, pil_format, quality=quality, optimize=True)
    
    elif output_format.lower() == 'webp':
        # Save WEBP with quality (supports transparency)
        image.save(output_path, pil_format, quality=quality, method=6)
    
    else:
        # Save PNG/TIFF without quality (lossless)
        image.save(output_path, pil_format)


def handle_file_conflict(output_path, force, skip_existing):
    """
    Handle file conflicts with user prompts or automatic behavior
    
    Args:
        output_path (Path): Target output file path
        force (bool): If True, always overwrite
        skip_existing (bool): If True, always skip existing files
        
    Returns:
        tuple: (should_process, global_action)
               should_process: bool indicating if file should be processed
               global_action: str for batch actions ('overwrite_all', 'skip_all', None)
    """
    if not output_path.exists():
        return True, None
    
    if force:
        return True, None
    
    if skip_existing:
        return False, None
    
    # Interactive prompt - use tqdm.write to avoid progress bar interference
    while True:
        try:
            # Clear the progress bar line and prompt cleanly
            sys.stdout.write(f"\nFile '{output_path.name}' already exists, okay to overwrite? [y]es/[n]o/overwrite [a]ll/[s]kip all: ")
            sys.stdout.flush()
            response = input().lower().strip()
            if response in ['y', 'yes']:
                return True, None
            elif response in ['n', 'no']:
                return False, None
            elif response in ['a', 'all']:
                return True, 'overwrite_all'
            elif response in ['s', 'skip', 'skip all']:
                return False, 'skip_all'
            else:
                print("Please enter: y (yes), n (no), a (overwrite all), or s (skip all)")
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled by user")
            return False, 'skip_all'


def is_likely_autosig_output(file_path, current_suffix, exclude_patterns=None):
    """
    Check if a file is likely an AutoSig output file based on suffix patterns
    
    Args:
        file_path (Path): File path to check
        current_suffix (str): Current suffix being used in this run
        exclude_patterns (list): Additional patterns to exclude
        
    Returns:
        bool: True if file appears to be AutoSig output
    """
    filename = file_path.stem  # filename without extension
    
    # Common AutoSig suffixes to exclude
    common_suffixes = [
        "_with_sig", "_signed", "_watermarked", "_autosig", "_sig", "_signature",
        "_test", "_test2", "_final", "_processed", "_stamped"
    ]
    
    # Add current suffix if not empty
    if current_suffix:
        common_suffixes.append(current_suffix)
    
    # Add any custom exclude patterns
    if exclude_patterns:
        common_suffixes.extend(exclude_patterns)
    
    # Check if filename ends with any of the known suffixes
    for suffix in common_suffixes:
        if filename.endswith(suffix):
            return True
    
    return False


def resize_image_if_needed(image, max_dimension):
    """
    Resize image if its larger dimension exceeds max_dimension, maintaining aspect ratio
    
    Args:
        image (PIL.Image): Source image to potentially resize
        max_dimension (int): Maximum size for the larger dimension (None to skip resizing)
        
    Returns:
        PIL.Image: Resized image or original if no resizing needed
    """
    if max_dimension is None:
        return image
    
    width, height = image.size
    larger_dimension = max(width, height)
    
    if larger_dimension <= max_dimension:
        return image
    
    # Calculate new dimensions maintaining aspect ratio
    if width > height:
        new_width = max_dimension
        new_height = int((height * max_dimension) / width)
    else:
        new_height = max_dimension
        new_width = int((width * max_dimension) / height)
    
    return image.resize((new_width, new_height), Image.LANCZOS)


def process_image_files(directory, signature_path, offset_pixels=20, offset_percent=None, max_dimension=None, suffix="_with_sig", force=False, skip_existing=False, output_format="png", quality=85, exclude_patterns=None):
    """
    Process all PSD/PNG files in the specified directory and add signature
    
    Args:
        directory (str): Path to directory containing image files
        signature_path (str): Path to signature file (PSD or PNG)
        offset_pixels (int): Pixel offset from right and bottom edges (default: 20)
        offset_percent (float): Percentage offset from right and bottom edges (overrides pixels if provided)
        max_dimension (int): Maximum size for larger dimension, maintains aspect ratio (None to skip resizing)
        suffix (str): Suffix to add to output filenames (default: "_with_sig")
        force (bool): If True, overwrite existing files without prompting
        skip_existing (bool): If True, skip existing files without prompting
        output_format (str): Output format - png, jpg, webp, tiff (default: "png")
        quality (int): Quality for lossy formats 1-100 (default: 85)
        exclude_patterns (list): Additional suffix patterns to exclude from input scanning
    """
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist")
        return
    
    if not os.path.exists(signature_path):
        print(f"Error: Signature file '{signature_path}' does not exist")
        return
    
    # Load signature image
    try:
        signature = load_image_file(signature_path)
        sig_ext = Path(signature_path).suffix.lower()
        print(f"Loaded {sig_ext.upper()} signature: {signature.size[0]}x{signature.size[1]} pixels")
    except Exception as e:
        print(f"Error loading signature file: {e}")
        return
    
    # Find all image files in directory (PSD and PNG)
    image_files = []
    image_files.extend(Path(directory).glob("*.psd"))
    
    # Filter PNG files to exclude likely AutoSig outputs
    all_png_files = list(Path(directory).glob("*.png"))
    filtered_png_files = [
        f for f in all_png_files 
        if not is_likely_autosig_output(f, suffix, exclude_patterns)
    ]
    image_files.extend(filtered_png_files)
    
    # Report any excluded files for transparency
    excluded_count = len(all_png_files) - len(filtered_png_files)
    if excluded_count > 0:
        print(f"Excluded {excluded_count} PNG files that appear to be AutoSig outputs")
    
    if not image_files:
        print(f"No PSD or PNG files found in '{directory}'")
        return
    
    print(f"Found {len(image_files)} image files to process")
    
    # Track processing results
    processed_count = 0
    skipped_files = []
    global_action = None
    
    for image_file in tqdm(image_files, desc="Processing images", unit="file"):
        try:
            # Load image file
            source_image = load_image_file(image_file)
            
            # Calculate signature position based on offset type
            if offset_percent is not None:
                # Use percentage offset
                offset_x = int(source_image.width * (offset_percent / 100))
                offset_y = int(source_image.height * (offset_percent / 100))
            else:
                # Use pixel offset
                offset_x = offset_pixels
                offset_y = offset_pixels
            
            sig_x = source_image.width - signature.width - offset_x
            sig_y = source_image.height - signature.height - offset_y
            
            # Ensure signature fits within image bounds
            if sig_x < 0 or sig_y < 0:
                tqdm.write(f"Warning: Signature too large for {image_file.name}, skipping")
                continue
            
            # Create a copy of the original image for compositing
            result_image = source_image.copy()
            
            # Paste signature onto image with alpha blending
            result_image.paste(signature, (sig_x, sig_y), signature)
            
            # Resize the final composite image if needed
            result_image = resize_image_if_needed(result_image, max_dimension)
            
            # Generate output path with suffix and format
            output_path = generate_output_path(image_file, suffix, output_format)
            
            # Handle file conflicts
            if global_action == 'overwrite_all':
                should_process = True
            elif global_action == 'skip_all':
                should_process = False
            else:
                should_process, new_global_action = handle_file_conflict(output_path, force, skip_existing)
                if new_global_action:
                    global_action = new_global_action
            
            if should_process:
                # Save in specified format
                save_image_with_format(result_image, output_path, output_format, quality)
                processed_count += 1
            else:
                skipped_files.append(output_path.name)
                continue
            
        except Exception as e:
            tqdm.write(f"Error processing {image_file.name}: {e}")
            continue
    
    # Print summary
    print(f"\nProcessing complete!")
    print(f"Processed: {processed_count} files")
    if skipped_files:
        print(f"Skipped: {len(skipped_files)} files due to conflicts")
        if len(skipped_files) <= 10:
            for filename in skipped_files:
                print(f"  - {filename}")
        else:
            for filename in skipped_files[:10]:
                print(f"  - {filename}")
            print(f"  ... and {len(skipped_files) - 10} more")


def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Add signature to PSD/PNG files and export in multiple formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python autosig.py /path/to/images signature.png
  python autosig.py . my_signature.psd --pixels 50
  python autosig.py /photos signature.png --percent 5
  python autosig.py images sig.png --max-dimension 2000
  python autosig.py photos sig.png --suffix \"_signed\" --force
  python autosig.py images sig.png --format jpg --quality 90
  python autosig.py photos sig.png --exclude-suffix "_draft"
        """
    )
    
    parser.add_argument(
        "directory",
        help="Directory containing PSD/PNG files to process"
    )
    
    parser.add_argument(
        "signature",
        help="Path to signature file (PSD or PNG)"
    )
    
    parser.add_argument(
        "--pixels", "-p",
        type=int,
        default=20,
        help="Pixel offset from right and bottom edges (default: 20)"
    )
    
    parser.add_argument(
        "--percent", "-pc",
        type=float,
        help="Percentage offset from right and bottom edges (overrides --pixels)"
    )
    
    parser.add_argument(
        "--max-dimension", "-md",
        type=int,
        help="Maximum size for the larger dimension (maintains aspect ratio)"
    )
    
    parser.add_argument(
        "--suffix", "-s",
        type=str,
        default="_with_sig",
        help="Suffix to add to output filenames (default: '_with_sig')"
    )
    
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing files without prompting"
    )
    
    parser.add_argument(
        "--skip-existing", "-se",
        action="store_true",
        help="Skip existing files without prompting"
    )
    
    parser.add_argument(
        "--exclude-suffix", "-ex",
        type=str,
        action="append",
        help="Additional suffix patterns to exclude from input (can be used multiple times)"
    )
    
    parser.add_argument(
        "--format", "-fmt",
        type=str,
        choices=["png", "jpg", "webp", "tiff"],
        default="png",
        help="Output format (default: png)"
    )
    
    parser.add_argument(
        "--quality", "-q",
        type=int,
        default=85,
        help="Quality for lossy formats 1-100 (default: 85)"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"AutoSig {__version__}"
    )
    
    args = parser.parse_args()
    
    # Validate percentage range
    if args.percent is not None and (args.percent < 0 or args.percent > 50):
        print("Error: Percentage must be between 0 and 50")
        sys.exit(1)
    
    # Validate max dimension
    if args.max_dimension is not None and args.max_dimension <= 0:
        print("Error: Max dimension must be a positive integer")
        sys.exit(1)
    
    # Validate quality
    if args.quality < 1 or args.quality > 100:
        print("Error: Quality must be between 1 and 100")
        sys.exit(1)
    
    # Process the files
    process_image_files(args.directory, args.signature, args.pixels, args.percent, args.max_dimension, args.suffix, args.force, args.skip_existing, args.format, args.quality, args.exclude_suffix)


if __name__ == "__main__":
    main()