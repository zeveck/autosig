#!/usr/bin/env python3
"""
AutoSig - Automatic signature placement on image files
Processes PSD/PNG files in a directory and adds a signature (PSD/PNG) with 20px margin from right and bottom edges
"""

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


def process_image_files(directory, signature_path, offset_pixels=20, offset_percent=None):
    """
    Process all PSD/PNG files in the specified directory and add signature
    
    Args:
        directory (str): Path to directory containing image files
        signature_path (str): Path to signature file (PSD or PNG)
        offset_pixels (int): Pixel offset from right and bottom edges (default: 20)
        offset_percent (float): Percentage offset from right and bottom edges (overrides pixels if provided)
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
    image_files.extend(Path(directory).glob("*.png"))
    
    if not image_files:
        print(f"No PSD or PNG files found in '{directory}'")
        return
    
    print(f"Found {len(image_files)} image files to process")
    
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
            
            # Save as PNG
            output_path = image_file.with_suffix('.png')
            result_image.save(output_path, "PNG")
            
        except Exception as e:
            tqdm.write(f"Error processing {image_file.name}: {e}")
            continue
    
    print("Processing complete!")


def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Add signature to PSD/PNG files and export as PNG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python autosig.py /path/to/images signature.png
  python autosig.py . my_signature.psd --pixels 50
  python autosig.py /photos signature.png --percent 5
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
    
    args = parser.parse_args()
    
    # Validate percentage range
    if args.percent is not None and (args.percent < 0 or args.percent > 50):
        print("Error: Percentage must be between 0 and 50")
        sys.exit(1)
    
    # Process the files
    process_image_files(args.directory, args.signature, args.pixels, args.percent)


if __name__ == "__main__":
    main()