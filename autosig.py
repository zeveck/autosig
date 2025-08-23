#!/usr/bin/env python3
"""
AutoSig - Automatic signature placement on image files
Processes images in multiple formats (PSD, PNG, JPG, WEBP, BMP, TIFF, GIF) and adds signatures with customizable positioning and file handling
"""

__version__ = "0.3.3"

import os
import sys
import argparse
import warnings
import threading
import time
from pathlib import Path
from PIL import Image
from psd_tools import PSDImage
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from tqdm import tqdm

# Standard imports only - using Ctrl+C for cancellation

# Suppress harmless PSD library warnings about unknown resources
warnings.filterwarnings("ignore", message="Unknown image resource.*")

# Supported input formats
ALL_SUPPORTED_FORMATS = ["psd", "png", "jpg", "jpeg", "webp", "bmp", "tiff", "tif", "gif"]

def normalize_input_formats(format_list):
    """
    Normalize format list to handle aliases (jpeg/jpg, tiff/tif)
    
    Args:
        format_list (list): List of format strings
        
    Returns:
        list: Normalized format list with aliases expanded
    """
    if not format_list:
        return ALL_SUPPORTED_FORMATS.copy()
    
    # Handle aliases
    aliases = {
        'jpeg': ['jpg', 'jpeg'],
        'jpg': ['jpg', 'jpeg'], 
        'tiff': ['tiff', 'tif'],
        'tif': ['tiff', 'tif']
    }
    
    normalized = set()
    for fmt in format_list:
        fmt_lower = fmt.lower().strip()
        if fmt_lower in ALL_SUPPORTED_FORMATS:
            if fmt_lower in aliases:
                normalized.update(aliases[fmt_lower])
            else:
                normalized.add(fmt_lower)
        else:
            raise ValueError(f"Unsupported format '{fmt}'. Supported formats: {', '.join(ALL_SUPPORTED_FORMATS)}")
    
    return list(normalized)


def hide_layers_in_psd(psd, layers_to_hide):
    """
    Hide specified layers in PSD before composite
    
    Args:
        psd: PSDImage object
        layers_to_hide: List of layer names or indices to hide
    
    Returns:
        int: Number of layers successfully hidden
    """
    if not layers_to_hide:
        return 0
    
    hidden_count = 0
    
    for layer_spec in layers_to_hide:
        if isinstance(layer_spec, str) and layer_spec.isdigit():
            # Convert string digits to int
            layer_spec = int(layer_spec)
        
        if isinstance(layer_spec, int):
            # Hide by index (0-based)
            if 0 <= layer_spec < len(psd):
                psd[layer_spec].visible = False
                hidden_count += 1
            else:
                tqdm.write(f"Warning: Layer index {layer_spec} out of range (0-{len(psd)-1})")
        else:
            # Hide by name (case-insensitive)
            found = False
            for layer in psd:
                if hasattr(layer, 'name') and layer.name and layer.name.lower() == str(layer_spec).lower():
                    layer.visible = False
                    hidden_count += 1
                    found = True
                    break
            
            if not found:
                tqdm.write(f"Warning: Layer '{layer_spec}' not found in PSD")
    
    return hidden_count


def calculate_image_difference(img1, img2):
    """
    Calculate normalized difference between two image regions
    
    Args:
        img1 (PIL.Image): First image to compare
        img2 (PIL.Image): Second image to compare
        
    Returns:
        float: Normalized difference (0-100 scale)
    """
    import numpy as np
    
    # Convert to RGB if needed (to ensure same mode)
    if img1.mode != 'RGB':
        img1 = img1.convert('RGB')
    if img2.mode != 'RGB':
        img2 = img2.convert('RGB')
    
    # Convert to numpy arrays as float to avoid uint8 overflow
    arr1 = np.array(img1, dtype=np.float32)
    arr2 = np.array(img2, dtype=np.float32)
    
    # Calculate mean squared error
    mse = np.mean((arr1 - arr2) ** 2)
    
    # Normalize to 0-100 scale
    # Max possible MSE is 255^2 = 65025 per channel
    # But mean across all pixels and channels already accounts for this
    # So max MSE is just 255^2 when comparing black vs white
    normalized = (mse / (255 * 255)) * 100
    
    return normalized


def likely_has_signature(corner_region):
    """
    Check if corner region likely contains a signature
    
    Args:
        corner_region (PIL.Image): Corner region to analyze
        
    Returns:
        bool: True if likely contains signature content
    """
    import numpy as np
    
    # Convert to grayscale for analysis
    gray = corner_region.convert('L')
    pixels = np.array(gray)
    
    # Check for high contrast areas (signatures usually have text/graphics)
    std_dev = np.std(pixels)
    
    # If standard deviation > threshold, likely has content
    # Lower threshold to 10 to catch low-contrast signatures
    # Most signatures will have at least this much variation
    return std_dev > 10


def detect_and_hide_signature_layers(psd, check_region_size=None):
    """
    Automatically detect and hide layers containing signatures
    
    Args:
        psd (PSDImage): PSD file object
        check_region_size (tuple): Deprecated - kept for compatibility
        
    Returns:
        tuple: (signature_layers_hidden, originally_hidden, signature_detected_but_not_hideable)
    """
    import numpy as np
    from contextlib import redirect_stderr, redirect_stdout
    from io import StringIO
    from tqdm import tqdm
    
    # Silence PSD warnings during composite operations
    with redirect_stderr(StringIO()), redirect_stdout(StringIO()):
        # Get reference image with all currently visible layers
        reference = psd.composite(force=True)
    
    width, height = reference.size
    image_area = width * height
    
    # Track layer states
    originally_hidden = []
    signature_layers = []
    
    # Record originally hidden layers
    for i, layer in enumerate(psd):
        if not layer.is_visible():
            originally_hidden.append(i)
    
    # Test each visible layer - looking for small layers anywhere in the image
    for i, layer in enumerate(psd):
        if i in originally_hidden:
            continue  # Skip already hidden layers
        
        # Check layer bounds to see if it's likely a signature
        is_signature_sized = False
        
        if hasattr(layer, 'bbox') and layer.bbox:
            x1, y1, x2, y2 = layer.bbox
            layer_width = x2 - x1
            layer_height = y2 - y1
            layer_area = layer_width * layer_height
            
            # Calculate layer size as percentage of image
            layer_size_percent = (layer_area / image_area) * 100
            
            # Signatures are typically small (< 15% of image area)
            # We're being a bit more generous than before (was 10%)
            is_signature_sized = layer_size_percent < 15
            
            # Skip very large layers early (optimization)
            if layer_size_percent > 50:
                continue  # Definitely not a signature
        
        # Temporarily hide this layer
        layer.visible = False
        
        try:
            with redirect_stderr(StringIO()), redirect_stdout(StringIO()):
                test_image = psd.composite(force=True)
            
            # Calculate difference in the region where the layer exists
            # This gives us better sensitivity for small layers
            if hasattr(layer, 'bbox') and layer.bbox:
                x1, y1, x2, y2 = layer.bbox
                # Crop to layer bounds for comparison
                ref_crop = reference.crop((x1, y1, x2, y2))
                test_crop = test_image.crop((x1, y1, x2, y2))
                diff = calculate_image_difference(ref_crop, test_crop)
            else:
                # No bbox, check entire image
                diff = calculate_image_difference(reference, test_image)
            
            # Decision logic:
            # - Small layers (< 15% of image) with ANY detectable change (>0.01%) are likely signatures
            # - Medium layers (15-50% of image) need moderate change (5-25%) to be considered
            # - Large layers (> 50%) are never considered signatures
            
            if is_signature_sized and diff > 0.01:
                signature_layers.append(i)
                # Keep it hidden
            elif not is_signature_sized and layer_size_percent < 50 and 5.0 < diff < 25.0:
                # Medium-sized layer with moderate change might be signature
                signature_layers.append(i)
                # Keep it hidden
            else:
                # Restore the layer - either no significant change or too large a change
                layer.visible = True
                
        except Exception:
            # If something goes wrong, restore the layer
            layer.visible = True
    
    # Since we're no longer checking a specific region, we can't detect
    # "signature present but not hideable" - we just report what we found
    signature_not_hideable = False
    
    return signature_layers, originally_hidden, signature_not_hideable


def load_image_file(file_path, layers_to_hide=None, auto_hide_signature=False):
    """
    Load an image file in any supported format and return as PIL Image
    
    Args:
        file_path (str): Path to image file (PSD, PNG, JPG, WEBP, BMP, TIFF, GIF)
        layers_to_hide (list): List of layer names or indices to hide (PSD only)
        auto_hide_signature (bool): Automatically detect and hide signature layers (PSD only)
        
    Returns:
        PIL.Image: Loaded image in RGBA format
        
    Note:
        - PSD files support layer hiding before composite
        - Animated GIFs automatically use first frame with warning
        - All formats normalized to RGBA for consistent processing
    """
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.psd':
        # Suppress stdout/stderr during PSD loading to hide unknown resource warnings
        with redirect_stderr(StringIO()), redirect_stdout(StringIO()):
            psd = PSDImage.open(file_path)
            
            # Hide specified layers before compositing
            if layers_to_hide:
                hidden_count = hide_layers_in_psd(psd, layers_to_hide)
                if hidden_count > 0:
                    tqdm.write(f"Hidden {hidden_count} layer(s) in {Path(file_path).name}")
            
            # Auto-detect and hide signature layers if requested
            if auto_hide_signature:
                sig_layers, orig_hidden, not_hideable = detect_and_hide_signature_layers(psd)
                
                # Warn if signature detected but couldn't be hidden
                if not_hideable:
                    tqdm.write(f"Warning: Possible signature detected in {Path(file_path).name} but no hideable layer found")
            
            return psd.composite(force=True).convert("RGBA")
    else:
        # Non-PSD files don't have layers, ignore layer hiding
        if layers_to_hide:
            tqdm.write(f"Warning: Layer hiding only supported for PSD files, ignored for {Path(file_path).name}")
        
        img = Image.open(file_path)
        
        # Check for animated GIF and warn user
        if file_ext == '.gif':
            is_animated = getattr(img, "is_animated", False)
            frame_count = getattr(img, "n_frames", 1)
            if is_animated and frame_count > 1:
                tqdm.write(f"Warning: Animated GIF detected ({frame_count} frames), using first frame only: {Path(file_path).name}")
        
        return img.convert("RGBA")


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


def detect_orientation(width, height):
    """
    Classify image orientation
    
    Args:
        width (int): Image width
        height (int): Image height
        
    Returns:
        str: "landscape", "portrait", or "square"
    """
    ratio = width / height
    if ratio > 1.2:
        return "landscape"
    elif ratio < 0.8:
        return "portrait"
    else:
        return "square"


def parse_aspect_ratio(ratio_str):
    """
    Parse aspect ratio string like "4:5" or "16:9"
    
    Args:
        ratio_str (str): Ratio in format "width:height" or decimal number
        
    Returns:
        float: Aspect ratio as width/height
    """
    if ":" in ratio_str:
        try:
            w, h = map(float, ratio_str.split(":"))
            if h == 0:
                raise ValueError("Height cannot be zero")
            return w / h
        except ValueError:
            raise ValueError(f"Invalid aspect ratio format: {ratio_str}")
    else:
        try:
            return float(ratio_str)
        except ValueError:
            raise ValueError(f"Invalid aspect ratio format: {ratio_str}")


def center_crop_to_max_ratio(image, max_ratio, orientation):
    """
    Center crop image only if it exceeds the maximum aspect ratio for its orientation
    
    Args:
        image (PIL.Image): PIL Image object
        max_ratio (float): Maximum allowed aspect ratio (width/height)
        orientation (str): "portrait", "landscape", or "square"
    
    Returns:
        PIL.Image: Cropped image (only if needed) or original
    """
    current_ratio = image.width / image.height
    
    # Only crop if image exceeds the maximum ratio for its orientation
    if orientation in ["portrait", "square"] and current_ratio < max_ratio:
        # Portrait/square image too tall (ratio too small) - crop height
        new_height = int(image.width / max_ratio)
        if new_height < image.height:  # Only crop if needed
            top = (image.height - new_height) // 2
            return image.crop((0, top, image.width, top + new_height))
    elif orientation == "landscape" and current_ratio > max_ratio:
        # Landscape image too wide (ratio too large) - crop width
        new_width = int(image.height * max_ratio)
        if new_width < image.width:  # Only crop if needed
            left = (image.width - new_width) // 2
            return image.crop((left, 0, left + new_width, image.height))
    
    # Image is within acceptable ratio limits, no cropping needed
    return image


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


def process_image_files(directory, signature_path=None, offset_pixels=70, offset_percent=None, max_dimension=None, suffix="_with_sig", force=False, skip_existing=False, output_format="png", quality=85, exclude_patterns=None, apply_signature=True, layers_to_hide=None, crop_portrait_ratio=None, crop_landscape_ratio=None, input_formats=None, sample_size=None, auto_hide_signature=False):
    """
    Process image files in the specified directory with optional signature application
    
    Args:
        directory (str): Path to directory containing image files
        signature_path (str): Path to signature file (PSD or PNG) - None if apply_signature=False
        offset_pixels (int): Pixel offset from right and bottom edges (default: 70)
        offset_percent (float): Percentage offset from right and bottom edges (overrides pixels if provided)
        max_dimension (int): Maximum size for larger dimension, maintains aspect ratio (None to skip resizing)
        suffix (str): Suffix to add to output filenames (default: "_with_sig")
        force (bool): If True, overwrite existing files without prompting
        skip_existing (bool): If True, skip existing files without prompting
        output_format (str): Output format - png, jpg, webp, tiff (default: "png")
        quality (int): Quality for lossy formats 1-100 (default: 85)
        exclude_patterns (list): Additional suffix patterns to exclude from input scanning
        apply_signature (bool): If True, apply signature to images (default: True)
        layers_to_hide (list): List of layer names or indices to hide in PSD files
        crop_portrait_ratio (str): Maximum aspect ratio for portrait/square images (e.g., "4:5")
        crop_landscape_ratio (str): Maximum aspect ratio for landscape images (e.g., "16:9")
        input_formats (list): List of input formats to process (default: all supported formats)
        sample_size (int): Process only the first N files (None to process all)
        auto_hide_signature (bool): Automatically detect and hide signature layers in PSD files
    """
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist")
        return
    
    # Load signature image only if applying signature
    signature = None
    if apply_signature:
        if not signature_path or not os.path.exists(signature_path):
            print(f"Error: Signature file '{signature_path}' does not exist")
            return
        
        try:
            signature = load_image_file(signature_path)
            sig_ext = Path(signature_path).suffix.lower()
            print(f"Loaded {sig_ext.upper()} signature: {signature.size[0]}x{signature.size[1]} pixels")
        except Exception as e:
            print(f"Error loading signature file: {e}")
            return
    
    # Normalize and validate input formats
    try:
        if input_formats:
            # Parse comma-separated format list
            format_list = [fmt.strip() for fmt in input_formats.split(',')]
            normalized_formats = normalize_input_formats(format_list)
        else:
            normalized_formats = normalize_input_formats(None)  # All formats
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Find all image files in directory for specified formats
    image_files = []
    all_files_by_format = {}
    
    for fmt in normalized_formats:
        pattern = f"*.{fmt}"
        found_files = list(Path(directory).glob(pattern))
        all_files_by_format[fmt] = found_files
        
        # Apply AutoSig output filtering to all formats (not just PNG)
        filtered_files = [
            f for f in found_files 
            if not is_likely_autosig_output(f, suffix, exclude_patterns)
        ]
        image_files.extend(filtered_files)
        
        # Report excluded files for transparency
        excluded_count = len(found_files) - len(filtered_files)
        if excluded_count > 0:
            print(f"Excluded {excluded_count} {fmt.upper()} files that appear to be AutoSig outputs")
    
    if not image_files:
        format_names = ', '.join(normalized_formats).upper()
        print(f"No {format_names} files found in '{directory}'")
        return
    
    # Apply sample size limit if specified
    total_files = len(image_files)
    if sample_size and sample_size > 0:
        image_files = image_files[:sample_size]
        print(f"Found {total_files} image files, processing first {len(image_files)} as sample")
    else:
        print(f"Found {len(image_files)} image files to process")
    
    print("Press Ctrl+C to cancel processing at any time")
    
    # Track processing results
    processed_count = 0
    skipped_files = []
    global_action = None
    cancelled = False
    
    try:
        for image_file in tqdm(image_files, desc="Processing images (Ctrl+C to cancel)", unit="file"):
            
            try:
                # Load image file with layer hiding if specified
                source_image = load_image_file(image_file, layers_to_hide, auto_hide_signature)
                
                # Create a copy of the original image for processing
                result_image = source_image.copy()
                
                # Apply aspect ratio cropping if specified
                if crop_portrait_ratio or crop_landscape_ratio:
                    orientation = detect_orientation(result_image.width, result_image.height)
                    
                    if orientation in ["portrait", "square"] and crop_portrait_ratio:
                        try:
                            max_ratio = parse_aspect_ratio(crop_portrait_ratio)
                            result_image = center_crop_to_max_ratio(result_image, max_ratio, orientation)
                        except ValueError as e:
                            tqdm.write(f"Warning: Invalid portrait ratio '{crop_portrait_ratio}': {e}")
                    
                    elif orientation == "landscape" and crop_landscape_ratio:
                        try:
                            max_ratio = parse_aspect_ratio(crop_landscape_ratio)
                            result_image = center_crop_to_max_ratio(result_image, max_ratio, orientation)
                        except ValueError as e:
                            tqdm.write(f"Warning: Invalid landscape ratio '{crop_landscape_ratio}': {e}")
                
                # Apply signature if requested
                if apply_signature and signature:
                    # Calculate signature position based on offset type
                    if offset_percent is not None:
                        # Use percentage offset (based on cropped dimensions)
                        offset_x = int(result_image.width * (offset_percent / 100))
                        offset_y = int(result_image.height * (offset_percent / 100))
                    else:
                        # Use pixel offset
                        offset_x = offset_pixels
                        offset_y = offset_pixels
                    
                    sig_x = result_image.width - signature.width - offset_x
                    sig_y = result_image.height - signature.height - offset_y
                    
                    # Ensure signature fits within image bounds
                    if sig_x < 0 or sig_y < 0:
                        tqdm.write(f"Warning: Signature too large for {image_file.name}, skipping")
                        continue
                    
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
    
    except KeyboardInterrupt:
        # Handle Ctrl+C cancellation
        print(f"\n\nProcessing cancelled by user (Ctrl+C)")
        print(f"Successfully processed: {processed_count} files")
        print(f"Remaining files: {len(image_files) - processed_count - len(skipped_files)}")
        if skipped_files:
            print(f"Previously skipped: {len(skipped_files)} files")
        return
    
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
        description="Add signature to images in multiple formats and export with advanced processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python autosig.py /path/to/images signature.png
  python autosig.py . my_signature.psd --pixels 50
  python autosig.py /photos signature.png --percent 5
  python autosig.py images sig.png --max-dimension 2000
  python autosig.py photos sig.png --suffix \"_signed\" --force
  python autosig.py images sig.png --output-format jpg --quality 90
  python autosig.py photos sig.png --exclude-suffix "_draft"
  python autosig.py images/ --no-sig --output-format jpg --max-dimension 2000
  python autosig.py psds/ --no-sig --output-format png --suffix "_converted"
  python autosig.py psds/ sig.png --hide-layer "Signature" --hide-layer "Watermark"
  python autosig.py images/ --no-sig --hide-layer 0 --hide-layer 3
  python autosig.py photos/ sig.png --crop-portrait 4:5 --crop-landscape 16:9
  python autosig.py images/ --no-sig --crop-portrait 1:1 --output-format jpg
  python autosig.py photos/ sig.png --input-formats jpg,png --output-format webp
  python autosig.py archive/ --no-sig --input-formats bmp,tiff --output-format png
  python autosig.py images/ sig.png --sample 10  # Test on first 10 files
  python autosig.py photos/ sig.png --sample 5 --force  # Process first 5 without prompts
        """
    )
    
    parser.add_argument(
        "directory",
        help="Directory containing image files to process (PSD, PNG, JPG, WEBP, BMP, TIFF, GIF)"
    )
    
    parser.add_argument(
        "signature",
        nargs="?",
        help="Path to signature file (PSD or PNG) - optional if --no-sig specified"
    )
    
    parser.add_argument(
        "--pixels", "-p",
        type=int,
        default=70,
        help="Pixel offset from right and bottom edges (default: 70)"
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
        nargs='?',
        const="",
        help="Suffix to add to output filenames (default: '_with_sig'). Use --suffix without value for no suffix."
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
        "--output-format", "-of",
        type=str,
        choices=["png", "jpg", "webp", "tiff"],
        default="png",
        help="Output format (default: png)"
    )
    
    parser.add_argument(
        "--input-formats", "-if",
        type=str,
        help="Process only these input formats (comma-separated). Default: all supported formats (psd,png,jpg,jpeg,webp,bmp,tiff,tif,gif)"
    )
    
    parser.add_argument(
        "--quality", "-q",
        type=int,
        default=85,
        help="Quality for lossy formats 1-100 (default: 85)"
    )
    
    parser.add_argument(
        "--no-sig",
        action="store_true",
        help="Process images without applying signature (useful for format conversion, resizing, etc.)"
    )
    
    parser.add_argument(
        "--hide-layer",
        type=str,
        action="append",
        help="Hide PSD layer by name or index before processing (can be used multiple times)"
    )
    
    parser.add_argument(
        "--hide-signature-layer",
        action="store_true",
        help="Automatically detect and hide existing signature layers in PSD files"
    )
    
    parser.add_argument(
        "--crop-portrait",
        type=str,
        help="Maximum aspect ratio for portrait/square images (e.g., '4:5')"
    )
    
    parser.add_argument(
        "--crop-landscape", 
        type=str,
        help="Maximum aspect ratio for landscape images (e.g., '16:9')"
    )
    
    parser.add_argument(
        "--sample",
        type=int,
        metavar="N",
        help="Process only the first N files (useful for testing settings)"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"AutoSig {__version__}"
    )
    
    args = parser.parse_args()
    
    # Validate --no-sig and signature requirements
    if args.no_sig and args.signature:
        print("Error: Cannot specify both --no-sig and signature file")
        sys.exit(1)
    
    if not args.no_sig and not args.signature:
        print("Error: Signature file required unless --no-sig specified")
        sys.exit(1)
    
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
    
    # Validate sample size
    if args.sample is not None and args.sample <= 0:
        print("Error: Sample size must be a positive integer")
        sys.exit(1)
    
    # Adjust suffix for no-signature mode
    suffix = args.suffix
    if args.no_sig and suffix == "_with_sig":
        suffix = "_processed"
    
    # Process the files
    process_image_files(
        args.directory, 
        args.signature, 
        args.pixels, 
        args.percent, 
        args.max_dimension, 
        suffix, 
        args.force, 
        args.skip_existing, 
        args.output_format, 
        args.quality, 
        args.exclude_suffix,
        apply_signature=not args.no_sig,
        layers_to_hide=args.hide_layer,
        crop_portrait_ratio=args.crop_portrait,
        crop_landscape_ratio=args.crop_landscape,
        input_formats=args.input_formats,
        sample_size=args.sample,
        auto_hide_signature=args.hide_signature_layer
    )


if __name__ == "__main__":
    main()