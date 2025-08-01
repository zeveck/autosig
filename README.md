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

## File Support

### Input Files
- **PSD files**: Adobe Photoshop documents
- **PNG files**: Portable Network Graphics

### Signature Files
- **PSD files**: Adobe Photoshop documents
- **PNG files**: Portable Network Graphics

### Output
All processed files are exported as **PNG** format with the same base filename as the original.

## How It Works

1. **Scans** the specified directory for PSD and PNG files
2. **Loads** the signature file (supports transparency)
3. **Processes** each image file:
   - Loads and converts to RGBA format
   - Calculates signature position based on offset settings
   - Composites signature onto image with alpha blending
   - Saves result as PNG file
4. **Shows progress** with a visual progress bar

## Error Handling

- Files that can't be processed are skipped with error messages
- Signatures too large for the target image are skipped with warnings
- Invalid percentage values (outside 0-50%) are rejected
- Missing directories or signature files are reported

## Requirements

- Python 3.6+
- Pillow (PIL) >= 9.0.0
- psd-tools >= 1.9.0
- tqdm >= 4.64.0

## License

This project is provided as-is for educational and personal use.