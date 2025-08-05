# Multi-Format Input Support: Design Analysis & Plan

## Current State Analysis

### Existing CLI Structure
- `--format` / `-fmt`: Controls **output** format (png, jpg, webp, tiff)
- Input discovery: Hardcoded to `*.psd` and `*.png` only
- Processing: Universal PIL pipeline works with any format

### The Naming Problem
You're absolutely right - `--format` is ambiguous! It currently means "output format" but sounds like it could control input formats too.

## Proposed CLI Design

### Option A: Rename + Add Filter (Recommended)

**Breaking Change Approach:**
```bash
# Old (current)
--format jpg              # Output format

# New (proposed)  
--output-format jpg       # Clear: output format
--input-formats jpg,png   # Clear: filter input types
```

**Backward Compatibility Approach:**
```bash
# Keep existing for compatibility
--format jpg              # Output format (deprecated but working)
--output-format jpg       # New clear name (preferred)
--input-formats jpg,png   # New: filter input types

# Alternative shorter names
-of jpg                   # Output format
-if jpg,png               # Input format filter
```

### Option B: Keep Current + Add Filter

**Conservative Approach:**
```bash
--format jpg              # Keep as-is (output format)
--input-filter jpg,png    # New: input format filter
--accept jpg,png          # Alternative name
--only jpg,png            # Alternative name
```

## Name Analysis

### Output Format Options
| Option | Pro | Con |
|--------|-----|-----|
| `--output-format` | Very clear | Longer to type |
| `--out-format` | Clear, shorter | Still long |
| `--to` | Very short | Maybe too terse |
| Keep `--format` | No breaking change | Remains ambiguous |

### Input Filter Options  
| Option | Pro | Con |
|--------|-----|-----|
| `--input-formats` | Very clear | Long |
| `--input-filter` | Clear purpose | "filter" might confuse |
| `--accept` | Intuitive | Could be confused with file patterns |
| `--only` | Short, clear | Generic word |
| `--include` | Intuitive | Long |

## Recommended Solution

**Hybrid Approach: Backward Compatible + Clear**

```bash
# Output format (both work, prefer new name)
--format jpg              # Kept for compatibility
--output-format jpg       # New preferred name
-of jpg                   # Short alias

# Input filtering (new feature)
--include jpg,png         # Include only these formats
-i jpg,png                # Short alias
```

## Implementation Details

### File Discovery Logic
```python
# Current
image_files.extend(Path(directory).glob("*.psd"))
all_png_files = list(Path(directory).glob("*.png"))

# New
ALL_SUPPORTED = ["psd", "png", "jpg", "jpeg", "webp", "bmp", "tiff", "tif", "gif"]

def get_image_files(directory, include_formats=None):
    if include_formats is None:
        include_formats = ALL_SUPPORTED
    
    # Normalize format list (handle 'jpeg' -> ['jpg', 'jpeg'])
    normalized_formats = normalize_formats(include_formats)
    
    image_files = []
    for fmt in normalized_formats:
        image_files.extend(Path(directory).glob(f"*.{fmt}"))
    
    return image_files
```

### Format Normalization
```python
def normalize_formats(formats):
    """Handle aliases: jpeg->jpg, tiff->tif, etc."""
    aliases = {
        'jpeg': ['jpg', 'jpeg'],
        'jpg': ['jpg', 'jpeg'], 
        'tiff': ['tiff', 'tif'],
        'tif': ['tiff', 'tif']
    }
    
    normalized = set()
    for fmt in formats:
        normalized.update(aliases.get(fmt.lower(), [fmt.lower()]))
    
    return list(normalized)
```

## Use Case Examples

### Basic Multi-Format Processing
```bash
# Process all supported formats (new default behavior)
python autosig.py photos/ sig.png

# Process only JPEGs
python autosig.py photos/ sig.png --include jpg

# Process JPEGs and PNGs only  
python autosig.py photos/ sig.png --include jpg,png
```

### Format Conversion Workflows
```bash
# Convert all formats to WEBP
python autosig.py mixed_photos/ --no-sig --output-format webp

# Convert only old formats (BMP, TIFF) to modern PNG
python autosig.py archive/ --no-sig --include bmp,tiff --output-format png

# Process only GIFs (extract first frame, add signature)
python autosig.py gifs/ sig.png --include gif --output-format png
```

### Professional Workflows
```bash
# Batch process only RAW-adjacent formats
python autosig.py shoot/ sig.png --include tiff --output-format jpg --quality 95

# Social media prep: only process photos (no PSDs)
python autosig.py content/ sig.png --include jpg,png,webp --crop-portrait 4:5

# Clean up mixed directory: only process specific formats
python autosig.py downloads/ --no-sig --include gif,bmp --output-format png
```

## Edge Cases & Validation

### Input Validation
```bash
# Invalid format
python autosig.py photos/ sig.png --include xyz
# Error: Unsupported format 'xyz'. Supported: psd, png, jpg, jpeg, webp, bmp, tiff, tif, gif

# No matching files
python autosig.py photos/ sig.png --include tiff  
# Warning: No TIFF files found in directory

# Contradictory filters
python autosig.py photos/ sig.png --include jpg --hide-layer "Background"
# Warning: Layer hiding only supported for PSD files, but only processing JPG files
```

### Help Text
```bash
python autosig.py --help

Input Options:
  --include FORMATS, -i FORMATS
                        Process only these formats (comma-separated)
                        Supported: psd, png, jpg, jpeg, webp, bmp, tiff, tif, gif
                        Default: all supported formats
                        
Output Options:  
  --format FORMAT, -fmt FORMAT
                        Output format (default: png) [DEPRECATED: use --output-format]
  --output-format FORMAT, -of FORMAT  
                        Output format: png, jpg, webp, tiff (default: png)
```

## Migration Strategy

### Phase 1: Add New Features (v0.3.1)
- Add `--output-format` as preferred option
- Add `--include` for input filtering  
- Keep `--format` working (backward compatible)
- Add multi-format input support
- Update documentation to prefer new names

### Phase 2: Deprecation Warnings (v0.4.0)
- Add deprecation warning for `--format`
- Update all examples to use new names

### Phase 3: Remove Old Option (v1.0.0)
- Remove `--format` entirely
- Clean up help text

## Benefits

### User Experience
- **Clear intent**: `--output-format jpg --include png` is unambiguous
- **Flexible workflows**: Process specific format subsets
- **Professional feel**: Precise control over input/output
- **Backward compatible**: Existing scripts continue working

### Technical Benefits
- **Extensible**: Easy to add new formats
- **Maintainable**: Clear separation of input/output concerns
- **Testable**: Each format combination can be tested
- **Robust**: Format validation prevents user errors

## Recommendation

**Implement Option A (Hybrid Approach):**
- Add `--output-format` / `-of` (preferred)
- Add `--include` / `-i` (input filtering)
- Keep `--format` working for backward compatibility
- Use deprecation warnings in future versions

This provides maximum clarity for new users while maintaining compatibility for existing workflows.