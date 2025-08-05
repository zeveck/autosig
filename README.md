# AutoSig

Comprehensive image processing tool for batch processing images in multiple formats. Features signature application, PSD layer manipulation, aspect ratio cropping, format conversion, and multi-format export capabilities.

## Features

### Core Processing
- **Universal format support**: Process PSD, PNG, JPG, JPEG, WEBP, BMP, TIFF, TIF, and GIF files
- **Format filtering**: Choose specific input formats to process with `--input-formats` 
- **Flexible positioning**: Position signatures using pixel offsets or percentage-based positioning
- **Batch processing**: Process entire directories of images at once
- **Progress tracking**: Visual progress bar shows processing status with Ctrl+C cancellation
- **Graceful cancellation**: Press Ctrl+C to cancel processing with detailed progress report
- **Error handling**: Gracefully handles files that can't be processed
- **Animated GIF support**: Automatically extracts first frame from animated GIFs with warnings

### Advanced Features (v0.3.0+)
- **No-signature mode**: Process images without signatures for format conversion, resizing, and cropping
- **PSD layer hiding**: Hide specific layers in PSD files by name or index before processing
- **Smart aspect ratio cropping**: Apply maximum ratio constraints to prevent overly tall or wide images
- **Orientation-aware processing**: Different cropping ratios for portrait vs landscape images
- **Smart input filtering**: Automatically excludes AutoSig output files to prevent exponential file growth

### User Experience Features (v0.3.2+)
- **Ctrl+C cancellation**: Press Ctrl+C during processing to gracefully cancel with progress report
- **Immediate cancellation**: Standard KeyboardInterrupt handling for reliable cancellation
- **Comprehensive reporting**: Shows processed files, remaining files, and skipped files on cancellation
- **Clean error handling**: Proper cleanup without terminal corruption

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python autosig.py [directory] [signature_file]
```

**Example:**
```bash
python autosig.py psds sigs\justsig.png
```

### Positioning Options

#### Pixel Offset (Default: 20px)
Position the signature with a specific pixel distance from the right and bottom edges:

```bash
python autosig.py psds sigs\justsig.png --pixels 50
python autosig.py psds sigs\justsig.png -p 30
```

#### Percentage Offset
Position the signature as a percentage of the image dimensions from the right and bottom edges:

```bash
python autosig.py psds sigs\justsig.png --percent 5
python autosig.py psds sigs\justsig.png -pc 3
```

*Note: Percentage values are limited to 0-50% to ensure signatures remain visible.*

## Command Line Arguments

| Argument | Short | Type | Default | Description |
|----------|-------|------|---------|-------------|
| `directory` | - | string | - | Directory containing PSD/PNG files to process |
| `signature` | - | string | - | Path to signature file (PSD or PNG) - optional with `--no-sig` |
| `--pixels` | `-p` | integer | 20 | Pixel offset from right and bottom edges |
| `--percent` | `-pc` | float | - | Percentage offset from edges (overrides --pixels) |
| `--max-dimension` | `-md` | integer | - | Maximum size for larger dimension (maintains aspect ratio) |
| `--suffix` | `-s` | string | `_with_sig` | Suffix to add to output filenames |
| `--output-format` | `-of` | string | `png` | Output format: png, jpg, webp, tiff |
| `--input-formats` | `-if` | string | `all` | Input formats to process (comma-separated): psd,png,jpg,jpeg,webp,bmp,tiff,tif,gif |
| `--quality` | `-q` | integer | 85 | Quality for lossy formats (1-100) |
| `--force` | `-f` | flag | - | Overwrite existing files without prompting |
| `--skip-existing` | `-se` | flag | - | Skip existing files without prompting |
| `--exclude-suffix` | `-ex` | string | - | Additional suffix patterns to exclude from input (repeatable) |
| `--no-sig` | - | flag | - | Process images without signature (format conversion, resizing, cropping) |
| `--hide-layer` | - | string | - | Hide PSD layer by name or index (repeatable) |
| `--crop-portrait` | - | string | - | Maximum aspect ratio for portrait/square images (e.g., '4:5') |
| `--crop-landscape` | - | string | - | Maximum aspect ratio for landscape images (e.g., '16:9') |

## Examples

### Process with default 20px offset
```bash
python autosig.py photos signature.png
```

### Use custom pixel offset
```bash
python autosig.py images logo.psd --pixels 40
```

### Use percentage positioning
```bash
python autosig.py ./photos watermark.png --percent 8
```

### Process current directory
```bash
python autosig.py . signature.png -p 25
```

### Resize images to max dimension
```bash
python autosig.py photos signature.png --max-dimension 2000
```

### Combine resizing with custom positioning
```bash
python autosig.py images logo.png -md 1920 --percent 3
```

### Custom output filename suffix
```bash
python autosig.py photos signature.png --suffix "_signed"
```

### Force overwrite existing files
```bash
python autosig.py images logo.png --force
```

### Skip existing files without prompting
```bash
python autosig.py photos sig.png --skip-existing
```

### Remove suffix (original name + extension)
```bash
python autosig.py images sig.png --suffix ""
```

### Output as JPG with default quality
```bash
python autosig.py photos sig.png --output-format jpg
```

### High quality JPG output
```bash
python autosig.py images sig.png --output-format jpg --quality 95
```

### WEBP format for web use
```bash
python autosig.py photos sig.png --output-format webp --quality 80
```

### Exclude custom patterns from input
```bash
python autosig.py images sig.png --exclude-suffix "_draft" --exclude-suffix "_backup"
```

## Advanced Features Examples

### No-Signature Mode (v0.3.0+)

#### Convert formats without signature
```bash
python autosig.py psds/ --no-sig --output-format jpg --quality 90
```

#### Resize and convert PSD to PNG
```bash
python autosig.py psds/ --no-sig --max-dimension 2000 --suffix "_converted"
```

### PSD Layer Hiding (v0.3.0+)

#### Hide layers by name
```bash
python autosig.py psds/ sig.png --hide-layer "Signature" --hide-layer "Watermark"
```

#### Hide layers by index (0-based)
```bash
python autosig.py psds/ --no-sig --hide-layer 0 --hide-layer 3
```

#### Mix layer names and indices
```bash
python autosig.py psds/ sig.png --hide-layer "Draft Layer" --hide-layer 5
```

### Smart Aspect Ratio Cropping (v0.3.0+)

#### Apply different max ratios for portrait vs landscape
```bash
python autosig.py photos/ sig.png --crop-portrait 4:5 --crop-landscape 16:9
```

#### Crop only portrait images to square
```bash
python autosig.py images/ sig.png --crop-portrait 1:1
```

#### Social media batch processing with constraints
```bash
python autosig.py photos/ sig.png --crop-portrait 4:5 --crop-landscape 16:9 --max-dimension 1080 --output-format jpg --suffix "_insta"
```

### Multi-Format Input Support (v0.3.1+)

#### Process only specific formats
```bash
# Process only JPEG files
python autosig.py photos/ sig.png --input-formats jpg

# Process multiple specific formats
python autosig.py mixed_media/ sig.png --input-formats jpg,png,webp
```

#### Format conversion workflows
```bash
# Convert old formats to modern PNG
python autosig.py archive/ --no-sig --input-formats bmp,tiff --output-format png

# Batch convert GIFs to static images
python autosig.py gifs/ --no-sig --input-formats gif --output-format png --suffix "_static"
```

#### Mixed format processing
```bash
# Process all supported formats with different output
python autosig.py media/ sig.png --output-format webp --quality 85

# Format-specific processing (all formats automatically detected)
python autosig.py content/ sig.png --hide-layer "Watermark" --output-format jpg
```

### Complex Workflows (v0.3.0+)

#### Complete image processing pipeline
```bash
python autosig.py psds/ sig.png \
    --hide-layer "Draft" --hide-layer "Notes" \
    --crop-portrait 4:5 --crop-landscape 16:9 \
    --max-dimension 2000 \
    --format jpg --quality 90
```

#### Pure image processing without signature
```bash
python autosig.py psds/ --no-sig \
    --hide-layer "Watermark" \
    --crop-landscape 16:9 \
    --format webp --quality 85
```

## File Support

### Input Files
- **PSD files**: Adobe Photoshop documents
- **PNG files**: Portable Network Graphics

### Signature Files
- **PSD files**: Adobe Photoshop documents
- **PNG files**: Portable Network Graphics

### Output Formats
- **PNG**: Lossless with transparency support (default)
- **JPG**: Smaller files, composited on white background (no transparency)
- **WEBP**: Modern format with transparency and compression
- **TIFF**: Professional/print quality with transparency

## File Handling

### Output Files
- **Default naming**: `original_name_with_sig.png`
- **Custom suffix**: Use `--suffix` to customize (e.g., `_watermarked`, `_signed`)
- **No suffix**: Use `--suffix ""` for just the original name with format extension
- **Output formats**: PNG (default), JPG, WEBP, TIFF
- **Quality control**: Use `--quality` for JPG/WEBP compression (1-100, default 85)

### Overwrite Behavior
- **Default**: Prompts for each existing file with options:
  - `y` - overwrite this file
  - `n` - skip this file
  - `a` - overwrite all remaining files  
  - `s` - skip all remaining files
- **Force mode**: `--force` overwrites all without prompting
- **Skip mode**: `--skip-existing` skips all existing files silently

### Smart Input Filtering
AutoSig automatically prevents processing its own output files:
- **Auto-detection**: Recognizes common AutoSig suffixes (`_with_sig`, `_signed`, `_test`, etc.)
- **No file doubling**: Running multiple times on same directory won't create exponential files
- **Custom exclusions**: Use `--exclude-suffix` to exclude additional patterns
- **Transparent reporting**: Shows count of excluded files during processing

## How It Works

1. **Scans** the specified directory for supported image files
2. **Filters** input files to exclude previous AutoSig outputs  
3. **Starts** ESC key monitoring for graceful cancellation
4. **Loads** the signature file if signature mode is enabled (supports transparency)
5. **Processes** each image file (with cancellation checks):
   - Loads image and converts to RGBA format
   - **Hides PSD layers** if `--hide-layer` specified (PSD files only)
   - **Applies aspect ratio cropping** if `--crop-portrait` or `--crop-landscape` specified
     - Detects image orientation (portrait/landscape/square)
     - Only crops images that exceed the maximum ratio constraints
     - Uses center-aligned cropping to preserve important content
   - **Applies signature** if not in `--no-sig` mode
     - Calculates signature position based on offset settings  
     - Composites signature onto image with alpha blending
   - **Resizes image** if `--max-dimension` specified (maintains aspect ratio)
   - Generates output filename with suffix (auto-adjusts to `_processed` for `--no-sig`)
   - Handles file conflicts based on user settings
   - Saves result in specified format (PNG/JPG/WEBP/TIFF)
6. **Shows progress** with a visual progress bar (Ctrl+C to cancel)
7. **Handles cancellation** if Ctrl+C is pressed with detailed report
8. **Reports summary** with processed/skipped file counts

## Error Handling

- Files that can't be processed are skipped with error messages
- Signatures too large for the target image are skipped with warnings
- Invalid percentage values (outside 0-50%) are rejected
- Missing directories or signature files are reported
- File conflicts are handled according to user preferences
- Processing summary shows counts and lists skipped files

## Requirements

- Python 3.6+
- Pillow (PIL) >= 9.0.0
- psd-tools >= 1.9.0
- tqdm >= 4.64.0

## Development

### Running Tests

AutoSig includes a comprehensive test suite to ensure reliability:

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=autosig

# Run specific test categories
pytest -k "unit"          # Unit tests only
pytest -k "integration"   # Integration tests only
```

### Test Coverage

The comprehensive test suite includes **95 tests** with **75% code coverage**:
- **Unit tests**: Core functions (positioning, resizing, file handling, aspect ratio cropping)
- **Format tests**: PNG/JPG/WEBP/TIFF output validation with transparency handling
- **PSD tests**: Real PSD file processing with multi-layer scenarios and layer hiding
- **Integration tests**: End-to-end processing workflows with complex feature combinations
- **CLI tests**: Complete command-line validation using subprocess testing
- **Cancellation tests**: Ctrl+C handling and graceful exit scenarios
- **Error handling**: Invalid inputs, edge cases, and graceful failure scenarios

## Credits

Created by Rich Conlan  
Coded by Claude Code

## License

This project is provided as-is for educational and personal use.