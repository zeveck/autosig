# AutoSig

Automatic signature placement tool for batch processing PSD and PNG files. Adds a signature image with customizable positioning and exports the results as PNG files.

## Features

- **Multi-format support**: Process PSD and PNG source files with PSD or PNG signature files
- **Flexible positioning**: Position signatures using pixel offsets or percentage-based positioning
- **Batch processing**: Process entire directories of images at once
- **Progress tracking**: Visual progress bar shows processing status
- **Error handling**: Gracefully handles files that can't be processed

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
| `signature` | - | string | - | Path to signature file (PSD or PNG) |
| `--pixels` | `-p` | integer | 20 | Pixel offset from right and bottom edges |
| `--percent` | `-pc` | float | - | Percentage offset from edges (overrides --pixels) |
| `--max-dimension` | `-md` | integer | - | Maximum size for larger dimension (maintains aspect ratio) |
| `--suffix` | `-s` | string | `_with_sig` | Suffix to add to output filenames |
| `--format` | `-fmt` | string | `png` | Output format: png, jpg, webp, tiff |
| `--quality` | `-q` | integer | 85 | Quality for lossy formats (1-100) |
| `--force` | `-f` | flag | - | Overwrite existing files without prompting |
| `--skip-existing` | `-se` | flag | - | Skip existing files without prompting |
| `--exclude-suffix` | `-ex` | string | - | Additional suffix patterns to exclude from input (repeatable) |

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
python autosig.py photos sig.png --format jpg
```

### High quality JPG output
```bash
python autosig.py images sig.png --format jpg --quality 95
```

### WEBP format for web use
```bash
python autosig.py photos sig.png --format webp --quality 80
```

### Exclude custom patterns from input
```bash
python autosig.py images sig.png --exclude-suffix "_draft" --exclude-suffix "_backup"
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

1. **Scans** the specified directory for PSD and PNG files
2. **Filters** input files to exclude previous AutoSig outputs
3. **Loads** the signature file (supports transparency)
4. **Processes** each image file:
   - Loads and converts to RGBA format
   - Resizes image if max-dimension is specified (maintains aspect ratio)
   - Calculates signature position based on offset settings
   - Composites signature onto image with alpha blending
   - Generates output filename with suffix
   - Handles file conflicts based on user settings
   - Saves result in specified format (PNG/JPG/WEBP/TIFF)
5. **Shows progress** with a visual progress bar
6. **Reports summary** with processed/skipped file counts

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

The test suite covers:
- **Unit tests**: Core functions (positioning, resizing, file handling)
- **Format tests**: PNG/JPG/WEBP/TIFF output validation
- **Integration tests**: End-to-end processing with real image files
- **Error handling**: Invalid inputs and edge cases

## Credits

Created by Rich Conlan  
Coded by Claude Code

## License

This project is provided as-is for educational and personal use.